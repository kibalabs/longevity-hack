"""Genome analysis - core analysis logic."""

import json
from pathlib import Path
from typing import Dict, List, Tuple

from longevity import model


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
    """Handles genome analysis logic (no file I/O)."""

    def __init__(self, gwasDir: Path = None, annotationsDir: Path = None):
        self.gwasDir = gwasDir or Path('./.data/snps-gwas')
        self.annotationsDir = annotationsDir or Path('./.data/snps')

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

    def extract_clinvar_info(self, snp_annotation: dict) -> Dict:
        """Extract and score ClinVar information from SNP annotation."""
        clinvar = snp_annotation.get('clinvar', {})

        if not clinvar or 'rcv' not in clinvar:
            return {
                'has_clinvar': False,
                'max_significance_score': 0,
                'submissions': [],
            }

        gene = clinvar.get('gene', {})
        gene_symbol = gene.get('symbol', 'Unknown') if isinstance(gene, dict) else 'Unknown'
        rcv_entries = clinvar.get('rcv', [])

        # Handle case where rcv is a single dict instead of list
        if isinstance(rcv_entries, dict):
            rcv_entries = [rcv_entries]

        submissions = []
        max_sig_score = 0
        max_review_score = 0

        for rcv in rcv_entries:
            sig_raw = rcv.get('clinical_significance', 'Unknown')
            sig_normalized, sig_score = self.parse_clinvar_significance(sig_raw)
            review_status = rcv.get('review_status', 'Unknown')
            review_score = self.get_review_status_score(review_status)

            condition_info = rcv.get('conditions', {})
            # Handle both dict and list formats for conditions
            if isinstance(condition_info, list):
                condition_name = condition_info[0].get('name', 'Unknown') if condition_info else 'Unknown'
            elif isinstance(condition_info, dict):
                condition_name = condition_info.get('name', 'Unknown')
            else:
                condition_name = 'Unknown'

            submissions.append({
                'accession': rcv.get('accession', 'Unknown'),
                'clinical_significance': sig_normalized,
                'significance_score': sig_score,
                'condition': condition_name,
                'review_status': review_status,
                'review_score': review_score,
                'last_evaluated': rcv.get('last_evaluated', 'Unknown'),
                'number_submitters': rcv.get('number_submitters', 0),
            })

            max_sig_score = max(max_sig_score, sig_score)
            max_review_score = max(max_review_score, review_score)

        # Sort submissions by significance score, then review score
        submissions.sort(key=lambda x: (x['significance_score'], x['review_score']), reverse=True)

        return {
            'has_clinvar': True,
            'gene': gene_symbol,
            'max_significance_score': max_sig_score,
            'max_review_score': max_review_score,
            'submission_count': len(submissions),
            'submissions': submissions,
        }

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

    async def analyze_genome(
        self,
        genomeContent: str,
        read_gwas_file: callable,
        read_annotation_file: callable
    ) -> model.GenomeAnalysisResult:
        """
        Run genome analysis on genome file content.

        Args:
            genomeContent: The raw content of the genome file
            read_gwas_file: Async function(rsid: str) -> dict | None - reads GWAS data for an rsid
            read_annotation_file: Async function(rsid: str) -> dict | None - reads annotation data for an rsid

        Returns:
            Analysis results as a proper model.
        """
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
        userSnps = {}
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
            userSnps[rsid] = {
                'rsid': rsid,
                'chromosome': chromosome,
                'position': position,
                'genotype': genotype,
            }        # Find matches with GWAS data and ClinVar
        matched_snps = 0
        total_associations = 0
        scored_associations = []
        clinvar_variants = []
        snps_with_clinvar = 0

        for rsid, snp_data in userSnps.items():
            # Try to load GWAS data for this SNP
            gwas_data = await read_gwas_file(rsid)
            if not gwas_data:
                continue

            matched_snps += 1

            # Try to load annotation data (for ClinVar, gnomAD, etc.)
            annotation = await read_annotation_file(rsid)
            clinvar_info = None
            if annotation:
                clinvar_info = self.extract_clinvar_info(annotation)

                if clinvar_info['has_clinvar']:
                    snps_with_clinvar += 1

                    # Store clinically significant variants separately
                    if clinvar_info['max_significance_score'] >= 6:  # Pathogenic or risk factor
                        clinvar_variants.append({
                            'rsid': rsid,
                            'genotype': snp_data['genotype'],
                            'chromosome': snp_data['chromosome'],
                            'position': snp_data['position'],
                            'clinvar': clinvar_info,
                            'annotation': annotation,
                        })

            associations = gwas_data.get('associations', [])
            total_associations += len(associations)

            # Score each association
            for assoc in associations:
                # Calculate importance score (simplified version)
                importance_score = 0

                # P-value contribution - GWAS Catalog uses 'P-VALUE' field
                # P-values are typically in scientific notation (e.g., 5E-8)
                # Use -log10(p-value) for scoring, capped at 50
                pvalue = assoc.get('P-VALUE') or assoc.get('pvalue')
                if pvalue:
                    try:
                        pval_float = float(pvalue)
                        if pval_float > 0:
                            import math
                            # -log10(p-value): larger values = more significant
                            # e.g., p=1E-20 gives score of 20, p=5E-8 gives ~7.3
                            pvalue_score = min(-math.log10(pval_float), 50)
                            importance_score += pvalue_score
                    except (ValueError, TypeError):
                        pass

                # Add ClinVar score if available
                if clinvar_info and clinvar_info['has_clinvar']:
                    importance_score += clinvar_info['max_significance_score'] * 2

                scored_associations.append({
                    'rsid': rsid,
                    'genotype': snp_data['genotype'],
                    'chromosome': snp_data['chromosome'],
                    'position': snp_data['position'],
                    'trait': assoc.get('DISEASE/TRAIT') or assoc.get('trait', ''),
                    'pvalue': pvalue,
                    'importanceScore': importance_score,
                    'effectStrength': assoc.get('effect_strength', ''),
                    'riskAllele': assoc.get('effect_allele') or assoc.get('risk_allele', ''),
                    'clinvarCondition': clinvar_info['submissions'][0]['condition'] if clinvar_info and clinvar_info['has_clinvar'] else None,
                    'clinvarSignificance': clinvar_info['max_significance_score'] if clinvar_info and clinvar_info['has_clinvar'] else None,
                })

        # Sort by importance score
        scored_associations.sort(key=lambda x: x['importanceScore'], reverse=True)

        # Group by phenotype (all associations, not just top 50)
        phenotype_groups = {}
        for assoc in scored_associations:
            trait = assoc['trait']
            # Simple categorization based on keywords
            category = GenomeAnalyzer._categorize_trait(trait)

            if category not in phenotype_groups:
                phenotype_groups[category] = []
            phenotype_groups[category].append(assoc)

        # Build proper model
        associations_models = [model.GenomeAssociation(**assoc) for assoc in scored_associations]
        phenotype_groups_models = {
            category: [model.GenomeAssociation(**assoc) for assoc in assocs]
            for category, assocs in phenotype_groups.items()
        }

        result = model.GenomeAnalysisResult(
            summary=model.GenomeAnalysisSummary(
                totalSnps=len(userSnps),
                matchedSnps=matched_snps,
                totalAssociations=total_associations,
                topCategories=list(phenotype_groups.keys())[:8],
                clinvarCount=snps_with_clinvar,
            ),
            phenotypeGroups=phenotype_groups_models,
            top50Associations=associations_models[:50],
            clinvarVariants=clinvar_variants[:20],
        )

        return result

    @staticmethod
    def _categorize_trait(trait: str) -> str:
        """Categorize trait into phenotype group."""
        trait_lower = trait.lower()

        if any(word in trait_lower for word in ['cancer', 'tumor', 'carcinoma', 'melanoma', 'leukemia', 'lymphoma']):
            return 'Cancer'
        elif any(word in trait_lower for word in ['heart', 'cardiac', 'cardiovascular', 'coronary', 'blood pressure', 'hypertension']):
            return 'Cardiovascular disease'
        elif any(word in trait_lower for word in ['cholesterol', 'ldl', 'hdl', 'triglyceride', 'lipid']):
            return 'Lipid or lipoprotein measurement'
        elif any(word in trait_lower for word in ['diabetes', 'glucose', 'insulin', 'metabolic']):
            return 'Metabolic disorder'
        elif any(word in trait_lower for word in ['alzheimer', 'parkinson', 'neurological', 'brain', 'cognitive', 'dementia']):
            return 'Neurological disorder'
        elif any(word in trait_lower for word in ['height', 'weight', 'bmi', 'body mass']):
            return 'Body measurement'
        elif 'measurement' in trait_lower:
            return 'Other measurement'
        elif 'disease' in trait_lower or 'disorder' in trait_lower:
            return 'Other disease'
        else:
            return 'Other trait'
