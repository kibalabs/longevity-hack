import math
import time
from typing import Tuple

import sqlalchemy
from core import logging
from core.store.database import Database
from core.store.retriever import StringFieldFilter
from core.util import list_util

from longevity import model
from longevity.manual_categories import get_manual_category
from longevity.store import schema
from longevity.manual_categories import MANUAL_CATEGORIES

# ClinVar significance scoring (higher = more clinically important)
CLINVAR_SIGNIFICANCE_SCORES = {
    'Pathogenic': 10,
    'Likely pathogenic': 8,
    'Pathogenic/Likely pathogenic': 9,
    'Pathogenic/Established risk allele': 10,
    'risk factor': 7,
    'Uncertain significance': 3,
    'Conflicting interpretations of pathogenicity': 4,
    'Likely benign': 1,
    'Benign': 0,
    'drug response': 6,
    'association': 5,
    'other': 2,
    'not provided': 2,
}

# Review status scoring (higher = more reliable)
REVIEW_STATUS_SCORES = {
    'practice guideline': 4,
    'reviewed by expert panel': 4,
    'criteria provided, multiple submitters, no conflicts': 3,
    'criteria provided, conflicting interpretations': 2,
    'criteria provided, single submitter': 2,
    'no assertion criteria provided': 1,
    'no assertion provided': 1,
}


class GenomeAnalyzer:
    """Handles genome analysis logic."""

    def __init__(self, database: Database, batch_size: int = 10000):
        self.database = database
        self.batch_size = batch_size

    @staticmethod
    def parse_genotype(genotype: str) -> Tuple[str, str]:
        """Parse genotype into two alleles."""
        if not genotype or len(genotype) != 2:
            return ('', '')
        return (genotype[0], genotype[1])

    @staticmethod
    def parse_clinvar_significance(sig_string: str) -> Tuple[str, int]:
        """Parse clinical significance string and return normalized form with score."""
        sig_lower = sig_string.lower()
        for key, score in CLINVAR_SIGNIFICANCE_SCORES.items():
            if key.lower() in sig_lower:
                return (key, score)
        return (sig_string, 0)

    @staticmethod
    def get_review_status_score(review_status: str) -> int:
        """Get numerical score for review status."""
        review_lower = review_status.lower()
        for key, score in REVIEW_STATUS_SCORES.items():
            if key.lower() in review_lower:
                return score
        return 0

    async def read_gwas_from_database_batch(self, snps: list[model.UserSnp]) -> dict[str, list[model.GwasAssociation]]:
        """Read GWAS associations from database for multiple SNPs, filtering by rsid AND user's alleles."""
        start_time = time.time()
        if not snps:
            return {}

        # Build list of (rsid, effect_allele) tuples for VALUES clause
        # This allows PostgreSQL to use the composite index efficiently
        rsid_allele_pairs = set()  # Use set to automatically deduplicate
        for snp in snps:
            rsid = snp.rsid
            genotype = snp.genotype
            if genotype in ['--', '']:
                continue
            alleles = list(set(genotype))  # Get unique alleles from genotype

            # Add a pair for each unique allele in the user's genotype
            for allele in alleles:
                rsid_allele_pairs.add((rsid, allele))

        if not rsid_allele_pairs:
            return {}

        # Convert to list for the query
        rsid_allele_pairs = list(rsid_allele_pairs)

        # Use a temporary table approach for better performance with large datasets
        query_start = time.time()
        logging.info(f'      → Query will search for {len(rsid_allele_pairs)} (rsid, allele) pairs...')

        # Create temporary table with user's SNP pairs
        await self.database.execute(
            sqlalchemy.text("""
            CREATE TEMP TABLE IF NOT EXISTS temp_user_snps (
                rsid TEXT NOT NULL,
                effect_allele TEXT NOT NULL
            ) ON COMMIT DROP
        """)
        )

        # Insert user's SNP pairs into temp table
        if rsid_allele_pairs:
            values = ','.join([f"('{rsid}', '{allele}')" for rsid, allele in rsid_allele_pairs])
            await self.database.execute(
                sqlalchemy.text(f"""
                INSERT INTO temp_user_snps (rsid, effect_allele)
                VALUES {values}
            """)
            )

        # Join temp table with GWAS table using the composite index
        query = sqlalchemy.text("""
            SELECT g.*
            FROM tbl_snps_gwas g
            INNER JOIN temp_user_snps u
                ON g.rsid = u.rsid AND g.effect_allele = u.effect_allele
        """)
        result = await self.database.execute(query)
        records = result.fetchall()

        # Clean up temp table
        await self.database.execute(sqlalchemy.text('DROP TABLE IF EXISTS temp_user_snps'))

        query_time = time.time() - query_start

        logging.info(f'GWAS query executed: {len(rsid_allele_pairs)} (rsid, allele) pairs, {len(records)} records returned in {query_time:.2f}s')

        # Group records by rsid
        rsid_map: dict[str, list[model.GwasAssociation]] = {}
        for record in records:
            rsid = record.rsid if hasattr(record, 'rsid') else record[0]
            if rsid not in rsid_map:
                rsid_map[rsid] = []
            # Handle both SQLAlchemy Row objects and raw database rows
            rsid_map[rsid].append(
                model.GwasAssociation(
                    trait=record.trait if hasattr(record, 'trait') else record[1],
                    traitCategory=record.trait_category if hasattr(record, 'trait_category') else record[2],
                    pvalue=record.pvalue if hasattr(record, 'pvalue') else record[3],
                    pvalueMlog=record.pvalue_mlog if hasattr(record, 'pvalue_mlog') else record[4],
                    effectAllele=record.effect_allele if hasattr(record, 'effect_allele') else record[5],
                    effectType=record.effect_type if hasattr(record, 'effect_type') else record[6],
                    orOrBeta=record.or_or_beta if hasattr(record, 'or_or_beta') else record[7],
                    riskAlleleFrequency=record.risk_allele_frequency if hasattr(record, 'risk_allele_frequency') else record[8],
                    studyDescription=record.study_description if hasattr(record, 'study_description') else record[9],
                    pubmedId=record.pubmed_id if hasattr(record, 'pubmed_id') else record[10],
                    chromosome=record.chromosome if hasattr(record, 'chromosome') else record[11],
                    position=record.position if hasattr(record, 'position') else record[12],
                    mappedGene=record.mapped_gene if hasattr(record, 'mapped_gene') else record[13],
                )
            )

        total_time = time.time() - start_time
        logging.info(f'GWAS batch completed: {len(rsid_map)} unique SNPs with associations in {total_time:.2f}s')
        return rsid_map

    async def read_clinvar_from_database_batch(self, rsids: list[str]) -> dict[str, model.ClinvarInfo]:
        """Read ClinVar data from database for multiple RSIDs and extract scored info."""
        start_time = time.time()
        if not rsids:
            return {}

        records = await schema.SnpsClinvarRepository.list_many(database=self.database, fieldFilters=[StringFieldFilter(fieldName='rsid', containedIn=rsids)])

        logging.info(f'ClinVar query executed: {len(rsids)} RSIDs requested, {len(records)} records returned')

        # Group records by rsid
        rsid_map: dict[str, dict] = {}
        for record in records:
            if record.rsid not in rsid_map:
                rsid_map[record.rsid] = {'gene': record.gene or 'Unknown', 'submissions': []}

            # Parse and score this submission
            sig_normalized, sig_score = self.parse_clinvar_significance(record.clinicalSignificance or 'Unknown')
            review_score = self.get_review_status_score(record.reviewStatus or 'Unknown')

            rsid_map[record.rsid]['submissions'].append(
                model.ClinvarSubmission(
                    accession=record.accession or 'Unknown',
                    clinicalSignificance=sig_normalized,
                    significanceScore=sig_score,
                    condition=record.condition or 'Unknown',
                    reviewStatus=record.reviewStatus or 'Unknown',
                    reviewScore=review_score,
                    lastEvaluated=record.lastEvaluated or 'Unknown',
                    numberSubmitters=record.numberSubmitters or 0,
                )
            )

        # Build ClinvarInfo objects with scoring
        result = {}
        for rsid, data in rsid_map.items():
            submissions = data['submissions']

            # Calculate max scores
            max_sig_score = max((s.significanceScore for s in submissions), default=0)
            max_review_score = max((s.reviewScore for s in submissions), default=0)

            # Sort submissions by significance score, then review score
            submissions.sort(key=lambda x: (x.significanceScore, x.reviewScore), reverse=True)

            result[rsid] = model.ClinvarInfo(
                hasClinvar=True,
                gene=data['gene'],
                maxSignificanceScore=max_sig_score,
                maxReviewScore=max_review_score,
                submissionCount=len(submissions),
                submissions=submissions,
            )

        total_time = time.time() - start_time
        logging.info(f'ClinVar batch completed: {len(result)} SNPs with ClinVar data in {total_time:.2f}s')
        return result

    @staticmethod
    def detect_23andme_format(content: str) -> bool:
        """Detect if content is in 23andMe format."""
        lines = content.split('\n')

        has_header_comment = False
        has_data_line = False

        for i, line in enumerate(lines[:100]):  # Check first 100 lines
            # Check for 23andMe-style comment header
            if line.startswith('#'):
                if 'rsid' in line.lower() and 'chromosome' in line.lower():
                    has_header_comment = True
                continue

            # Check for data line format
            parts = line.strip().split('\t')
            if len(parts) >= 4:
                rsid, chrom, pos, genotype = parts[:4]
                # 23andMe format: rsid starts with 'rs' or 'i', chromosome is number/X/Y/MT
                if (rsid.startswith('rs') or rsid.startswith('i')) and len(genotype) <= 2:
                    has_data_line = True
                    break

        return has_header_comment or has_data_line

    async def analyze_snps_batch(self, snps: list[model.UserSnp]) -> list[model.SnpAnalysisResult]:
        """Analyze multiple SNPs in batch."""
        batch_start = time.time()
        if not snps:
            return []

        rsids = [snp.rsid for snp in snps]

        # Fetch all GWAS and ClinVar data in batches
        logging.info(f'      → Querying GWAS database for {len(snps)} SNPs...')
        gwas_start = time.time()
        gwas_data_map = await self.read_gwas_from_database_batch(snps)
        gwas_time = time.time() - gwas_start
        logging.info(f'      ✓ GWAS query completed in {gwas_time:.2f}s - {sum(len(v) for v in gwas_data_map.values())} associations found')

        logging.info(f'      → Querying ClinVar database for {len(rsids)} RSIDs...')
        clinvar_start = time.time()
        clinvar_info_map = await self.read_clinvar_from_database_batch(rsids)
        clinvar_time = time.time() - clinvar_start
        logging.info(f'      ✓ ClinVar query completed in {clinvar_time:.2f}s - {len(clinvar_info_map)} entries found')

        # Process each SNP
        logging.info(f'      → Processing and scoring {len(snps)} SNPs...')
        processing_start = time.time()
        results = []
        for snp in snps:
            rsid = snp.rsid
            chromosome = snp.chromosome
            position = snp.position
            genotype = snp.genotype

            associations = gwas_data_map.get(rsid, [])
            if not associations:
                results.append(model.SnpAnalysisResult(associations=[], hasClinvar=False))
                continue

            clinvar_info = clinvar_info_map.get(rsid)
            has_clinvar = clinvar_info is not None

            scored_associations = []
            # Score each association
            for assoc in associations:
                # Calculate importance score
                importance_score = 0

                # P-value contribution
                pvalue = assoc.pvalue
                if pvalue:
                    try:
                        pval_float = float(pvalue)
                        if pval_float > 0:
                            pvalue_score = min(-math.log10(pval_float), 50)
                            importance_score += pvalue_score
                    except (ValueError, TypeError):
                        pass

                if has_clinvar and clinvar_info:
                    importance_score += clinvar_info.maxSignificanceScore * 2

                # Extract odds ratio
                odds_ratio = None
                if assoc.orOrBeta and assoc.effectType == 'OR':
                    try:
                        odds_ratio = float(assoc.orOrBeta)
                    except (ValueError, TypeError):
                        pass

                # Extract risk allele frequency
                risk_allele_freq = None
                if assoc.riskAlleleFrequency:
                    try:
                        risk_allele_freq = float(assoc.riskAlleleFrequency)
                    except (ValueError, TypeError):
                        pass

                # Determine if user has risk allele
                # Since we filter at DB level, we know user has this allele
                risk_allele = assoc.effectAllele or ''
                user_has_risk_allele = True if (risk_allele and genotype not in ['--', '']) else None

                # Get manual category if available (trait-specific to handle pleiotropic SNPs)
                manual_category = get_manual_category(rsid=rsid, trait=assoc.trait)

                scored_associations.append(
                    model.GenomeAssociation(
                        rsid=rsid,
                        genotype=genotype,
                        chromosome=chromosome,
                        position=position,
                        trait=assoc.trait,
                        pvalue=pvalue,
                        importanceScore=importance_score,
                        effectStrength='',
                        riskAllele=risk_allele,
                        clinvarCondition=clinvar_info.submissions[0].condition if clinvar_info and clinvar_info.submissions else None,
                        clinvarSignificance=clinvar_info.maxSignificanceScore if clinvar_info else None,
                        traitCategory=assoc.traitCategory or 'Other',
                        manualCategory=manual_category,
                        oddsRatio=odds_ratio,
                        riskAlleleFrequency=risk_allele_freq,
                        studyDescription=assoc.studyDescription,
                        pubmedId=assoc.pubmedId,
                        userHasRiskAllele=user_has_risk_allele,
                    )
                )

            results.append(
                model.SnpAnalysisResult(
                    associations=scored_associations,
                    hasClinvar=has_clinvar,
                )
            )

        processing_time = time.time() - processing_start
        logging.info(f'      ✓ Processing completed in {processing_time:.2f}s')

        total_batch_time = time.time() - batch_start

        total_associations = sum(len(r.associations) for r in results)
        logging.info(f'Batch analysis completed: {len(snps)} SNPs processed, {total_associations} associations found. Times - GWAS: {gwas_time:.2f}s, ClinVar: {clinvar_time:.2f}s, Processing: {processing_time:.2f}s, Total: {total_batch_time:.2f}s')

        return results

    async def analyze_genome(self, genomeContent: str) -> model.GenomeAnalysisResult:
        analysis_start = time.time()
        manual_rsids = set(rsid for rsid, _ in MANUAL_CATEGORIES.keys())
        logging.info(f'Manual categories contain {len(manual_rsids)} unique RSIDs to match')
        logging.info('=' * 80)
        logging.info('STARTING GENOME ANALYSIS')
        logging.info('=' * 80)
        logging.info('Starting genome analysis')

        # Detect file format
        if not self.detect_23andme_format(genomeContent):
            raise ValueError(
                'Unrecognized file format. This analyzer only supports 23andMe format.\n'
                'Expected format:\n'
                '  - Comment lines starting with #\n'
                '  - Header line with: # rsid chromosome position genotype\n'
                '  - Tab-separated data lines with rsid, chromosome, position, genotype'
            )

        # Parse genome file content
        parse_start = time.time()
        userSnps: dict[str, model.UserSnp] = {}
        firstLine = True

        for line in genomeContent.split('\n'):
            # Skip comment lines
            if line.startswith('#'):
                continue
            # Skip header line (first non-comment line if it contains 'rsid')
            if firstLine:
                firstLine = False
                if 'rsid' in line.lower() and 'chromosome' in line.lower():
                    continue
            parts = line.strip().split('\t')
            if len(parts) < 4:
                continue
            rsid, chromosome, position, genotype = parts[:4]
            if genotype == '--':
                continue
            userSnps[rsid] = model.UserSnp(
                rsid=rsid,
                chromosome=chromosome,
                position=position,
                genotype=genotype,
            )

        parse_time = time.time() - parse_start
        logging.info(f'✓ Genome parsing completed: {len(userSnps)} SNPs parsed in {parse_time:.2f}s')

        # Filter to only SNPs we care about (those in manual categories)
        filtered_snps = {rsid: snp for rsid, snp in userSnps.items() if rsid in manual_rsids}
        logging.info(f'✓ Filtered to {len(filtered_snps)} SNPs that match manual categories (from {len(userSnps)} total)')

        # Process SNPs in batches
        batch_processing_start = time.time()
        matchedSnpsCount = 0
        clinvarCount = 0
        scoredAssociations = []

        chunks = list(list_util.generate_chunks(list(filtered_snps.values()), chunkSize=self.batch_size))
        total_batches = len(chunks)
        logging.info(f'Processing {len(filtered_snps)} filtered SNPs in {total_batches} batches of {self.batch_size}')

        for batch_num, snp_data_chunk in enumerate(chunks, 1):
            batch_start = time.time()
            logging.info(f'  → Batch {batch_num}/{total_batches}: Processing {len(snp_data_chunk)} SNPs...')
            logging.info(f'Processing batch {batch_num}/{total_batches} ({len(snp_data_chunk)} SNPs)')

            results = await self.analyze_snps_batch(snp_data_chunk)
            for result in results:
                scoredAssociations.extend(result.associations)
                matchedSnpsCount += 1 if len(result.associations) > 0 else 0
                clinvarCount += 1 if result.hasClinvar else 0

            batch_time = time.time() - batch_start
            logging.info(f'  ✓ Batch {batch_num}/{total_batches} completed in {batch_time:.2f}s - {matchedSnpsCount} matched, {len(scoredAssociations)} associations')
            logging.info(f'Batch {batch_num}/{total_batches} completed in {batch_time:.2f}s. Progress: {matchedSnpsCount} matched SNPs, {len(scoredAssociations)} total associations')

        batch_processing_time = time.time() - batch_processing_start
        logging.info(f'All batches completed in {batch_processing_time:.2f}s')

        # Sort associations
        logging.info('Sorting associations by importance score...')
        sort_start = time.time()
        scoredAssociations.sort(key=lambda x: x.importanceScore, reverse=True)
        sort_time = time.time() - sort_start
        logging.info(f'✓ Sorting completed in {sort_time:.2f}s')
        logging.info(f'Association sorting completed in {sort_time:.2f}s')

        result = model.GenomeAnalysisResult(
            summary=model.GenomeAnalysisSummary(
                totalSnps=len(userSnps),  # Keep original total
                matchedSnps=matchedSnpsCount,
                totalAssociations=len(scoredAssociations),
                clinvarCount=clinvarCount,
            ),
            associations=scoredAssociations,
        )

        total_time = time.time() - analysis_start
        logging.info('=' * 80)
        logging.info(f'ANALYSIS COMPLETE in {total_time:.2f}s')
        logging.info(f'  Total SNPs: {len(userSnps)}')
        logging.info(f'  Matched SNPs: {matchedSnpsCount}')
        logging.info(f'  Total Associations: {len(scoredAssociations)}')
        logging.info(f'  ClinVar entries: {clinvarCount}')
        logging.info('=' * 80)
        logging.info(f'Genome analysis completed in {total_time:.2f}s. Summary: {len(userSnps)} total SNPs, {matchedSnpsCount} matched, {len(scoredAssociations)} associations, {clinvarCount} with ClinVar data')

        return result
