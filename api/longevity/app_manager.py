import logging
import os
import time
import uuid
from collections import defaultdict
from pathlib import Path
from typing import Any

from sqlalchemy import func, select
from starlette.datastructures import UploadFile

from core.exceptions import NotFoundException
from core.queues.message_queue import MessageQueue
from core.requester import Requester
from core.store.database import Database
from core.util import date_util
from core.util import file_util
from longevity import model
from longevity.api import v1_resources as resources
from longevity.constants import EXAMPLE_ANALYSIS_ID
from longevity.genome_analyzer import GenomeAnalyzer
from longevity.messages import AnalyzeGenomeMessageContent
from longevity.store import schema
from longevity.store.entity_repository import StringFieldFilter


class AppManager:
    def __init__(self, database: Database, requester: Requester, workQueue: MessageQueue[Any]) -> None:
        self.database = database
        self.requester = requester
        self.workQueue = workQueue
        dataDir = Path(os.environ.get('DATA_DIR', str(Path(__file__).parent.parent)))
        self.uploadsDir = dataDir / 'uploads'
        self.outputsDir = dataDir / 'outputs'
        self.uploadsDir.mkdir(parents=True, exist_ok=True)
        self.outputsDir.mkdir(parents=True, exist_ok=True)
        self.genomeAnalyzer = GenomeAnalyzer(database=self.database)

    async def create_genome_analysis(self, fileName: str, fileType: str, genomeAnalysisId: str | None = None, userId: str = 'anonymous') -> resources.GenomeAnalysis:
        """Create a genome analysis record.

        Args:
            fileName: Name of the genome file
            fileType: Type of the file (e.g., 'text/plain')
            genomeAnalysisId: Optional specific ID (for example analysis). If None, generates UUID.
            userId: User ID (default: 'anonymous')
        """
        if genomeAnalysisId is None:
            genomeAnalysisId = str(uuid.uuid4())
        dbGenomeAnalysis = await schema.GenomeAnalysesRepository.create(
            database=self.database,
            genomeAnalysisId=genomeAnalysisId,
            userId=userId,
            fileName=fileName,
            status='waiting_for_upload',
            totalSnps=None,
            matchedSnps=None,
            totalAssociations=None,
            clinvarCount=None,
        )
        genomeAnalysis = resources.GenomeAnalysis(
            genomeAnalysisId=dbGenomeAnalysis.genomeAnalysisId,
            fileName=dbGenomeAnalysis.fileName,
            fileType=fileType,
            detectedFormat=None,
            status=dbGenomeAnalysis.status,
            createdDate=date_util.datetime_to_string(dbGenomeAnalysis.createdDate),
            summary=None,
        )
        return genomeAnalysis

    async def get_example_analysis_id(self) -> str:
        return EXAMPLE_ANALYSIS_ID

    async def upload_and_analyze_genome_file(self, genomeAnalysisId: str, file: UploadFile) -> resources.GenomeAnalysis:
        dbGenomeAnalysis = await schema.GenomeAnalysesRepository.get(
            database=self.database,
            idValue=genomeAnalysisId,
        )
        if not dbGenomeAnalysis:
            raise NotFoundException(message=f'GenomeAnalysis with id {genomeAnalysisId} not found')
        uploadDirectory = Path('./uploads')
        await file_util.create_directory(str(uploadDirectory))
        uploadPath = uploadDirectory / f'{genomeAnalysisId}_{file.filename}'
        content = await file.read()
        contentStr = content.decode('utf-8')
        await file_util.write_file(str(uploadPath), contentStr)
        await schema.GenomeAnalysesRepository.update(
            database=self.database,
            genomeAnalysisId=genomeAnalysisId,
            status='queued',
        )
        await self.workQueue.send_message(
            message=AnalyzeGenomeMessageContent(
                genomeAnalysisId=genomeAnalysisId,
                filePath=str(uploadPath),
            ).to_message(),
        )
        dbGenomeAnalysis = await schema.GenomeAnalysesRepository.get(
            database=self.database,
            idValue=genomeAnalysisId,
        )
        return resources.GenomeAnalysis(
            genomeAnalysisId=dbGenomeAnalysis.genomeAnalysisId,
            fileName=dbGenomeAnalysis.fileName,
            fileType=file.content_type or 'text/plain',
            detectedFormat=None,
            status=dbGenomeAnalysis.status,
            createdDate=date_util.datetime_to_string(dbGenomeAnalysis.createdDate),
            summary=resources.GenomeAnalysisSummary(
                totalSnps=dbGenomeAnalysis.totalSnps,
                matchedSnps=dbGenomeAnalysis.matchedSnps,
                totalAssociations=dbGenomeAnalysis.totalAssociations,
                clinvarCount=dbGenomeAnalysis.clinvarCount,
            )
            if dbGenomeAnalysis.totalSnps is not None
            else None,
        )

    async def run_genome_analysis(self, genomeAnalysisId: str, inputFilePath: str) -> None:
        """Run the genome analysis - each status update is committed immediately for UI visibility."""
        try:
            # Update status to parsing in database (commit immediately)
            async with self.database.create_transaction() as connection:
                await schema.GenomeAnalysesRepository.update(
                    database=self.database,
                    connection=connection,
                    genomeAnalysisId=genomeAnalysisId,
                    status='parsing',
                )

            genomeContent = await file_util.read_file(inputFilePath)

            analysisResult = await self.genomeAnalyzer.analyze_genome(genomeContent=genomeContent)

            # Update status to building_baseline in database (commit immediately)
            async with self.database.create_transaction() as connection:
                await schema.GenomeAnalysesRepository.update(
                    database=self.database,
                    connection=connection,
                    genomeAnalysisId=genomeAnalysisId,
                    status='building_baseline',
                )

            outputPath = self.outputsDir / f'{genomeAnalysisId}.json'
            resultContent = analysisResult.model_dump_json(indent=2)
            await file_util.write_file(str(outputPath), resultContent)

            await self._create_real_results(genomeAnalysisId, analysisResult)

            # Update status to completed with summary in database (commit immediately)
            async with self.database.create_transaction() as connection:
                await schema.GenomeAnalysesRepository.update(
                    database=self.database,
                    connection=connection,
                    genomeAnalysisId=genomeAnalysisId,
                    status='completed',
                    totalSnps=analysisResult.summary.totalSnps,
                    matchedSnps=analysisResult.summary.matchedSnps,
                    totalAssociations=analysisResult.summary.totalAssociations,
                    clinvarCount=analysisResult.summary.clinvarCount,
                )
        except Exception:
            # Update status to failed on error (commit immediately)
            async with self.database.create_transaction() as connection:
                await schema.GenomeAnalysesRepository.update(
                    database=self.database,
                    connection=connection,
                    genomeAnalysisId=genomeAnalysisId,
                    status='failed',
                )
            raise

    async def _create_real_results(self, genomeAnalysisId: str, analysisData: model.GenomeAnalysisResult) -> None:
        """Create genome analysis results from real analysis output."""
        # Group associations by trait category
        categoryGroups: dict[str, list[Any]] = defaultdict(list)
        for assoc in analysisData.associations:
            categoryGroups[assoc.traitCategory].append(assoc)

        # Create results for each category
        for category, associations in categoryGroups.items():
            # Deduplicate by rsid - keep highest scoring association per SNP
            seenRsids = {}
            for assoc in associations:
                if assoc.rsid not in seenRsids or assoc.importanceScore > seenRsids[assoc.rsid].importanceScore:
                    seenRsids[assoc.rsid] = assoc

            # Sort by importance score (show all unique SNPs, no limit)
            uniqueAssociations = sorted(seenRsids.values(), key=lambda x: x.importanceScore, reverse=True)

            # Convert to SNP resources
            snps = []
            for assoc in uniqueAssociations:
                snp = resources.SNP(
                    rsid=assoc.rsid,
                    genotype=assoc.genotype,
                    chromosome=assoc.chromosome,
                    position=int(assoc.position) if assoc.position.isdigit() else 0,
                    annotation=f'{assoc.trait} - {assoc.effectStrength or "Unknown"} effect. ' + (f'ClinVar: {assoc.clinvarCondition}' if assoc.clinvarCondition else ''),
                    confidence='Unknown',  # Not provided by analyzer
                    sources=['GWAS Catalog', 'ClinVar'] if assoc.clinvarCondition else ['GWAS Catalog'],
                    # Additional fields
                    trait=assoc.trait,
                    importanceScore=assoc.importanceScore,
                    pValue=str(assoc.pvalue) if assoc.pvalue else None,
                    effectStrength=assoc.effectStrength,
                    riskAllele=assoc.riskAllele,
                    clinvarCondition=assoc.clinvarCondition,
                    clinvarSignificance=assoc.clinvarSignificance,
                    oddsRatio=assoc.oddsRatio,
                    riskAlleleFrequency=assoc.riskAlleleFrequency,
                    studyDescription=assoc.studyDescription,
                    userHasRiskAllele=assoc.userHasRiskAllele,
                    riskLevel=None,  # Will be set below
                )
                # Calculate and set risk level
                snp.riskLevel = self._get_risk_level(snp)
                snps.append(snp)

            if snps:
                resultId = str(uuid.uuid4())

                # Save to database
                await schema.GenomeAnalysisResultsRepository.create(
                    database=self.database,
                    resultId=resultId,
                    genomeAnalysisId=genomeAnalysisId,
                    phenotypeGroup=category,
                    phenotypeDescription=f'Genetic variants associated with {category.lower()}',
                    snps=[snp.model_dump() for snp in snps],  # Convert to dict for JSON storage
                )

    async def get_genome_analysis(self, genomeAnalysisId: str) -> resources.GenomeAnalysis:
        startTime = time.time()
        logging.info(f'[PERF] get_genome_analysis started for {genomeAnalysisId}')

        # Get from database
        dbGenomeAnalysis = await schema.GenomeAnalysesRepository.get(
            database=self.database,
            idValue=genomeAnalysisId,
        )

        logging.info(f'[PERF] get_genome_analysis completed in {time.time() - startTime:.2f}s')

        # Convert to resource
        return resources.GenomeAnalysis(
            genomeAnalysisId=dbGenomeAnalysis.genomeAnalysisId,
            fileName=dbGenomeAnalysis.fileName,
            fileType='text/plain',  # Default, could be stored in DB later
            detectedFormat='23andme',  # Default for now
            status=dbGenomeAnalysis.status,
            createdDate=date_util.datetime_to_string(dbGenomeAnalysis.createdDate),
            summary=resources.GenomeAnalysisSummary(
                totalSnps=dbGenomeAnalysis.totalSnps or 0,
                matchedSnps=dbGenomeAnalysis.matchedSnps or 0,
                totalAssociations=dbGenomeAnalysis.totalAssociations or 0,
                clinvarCount=dbGenomeAnalysis.clinvarCount or 0,
            )
            if dbGenomeAnalysis.totalSnps is not None
            else None,
        )

    async def get_genome_analysis_overview(self, genomeAnalysisId: str) -> resources.GenomeAnalysisOverview:
        """Get overview of genome analysis with all categories (no SNPs - loaded on demand)."""
        startTime = time.time()
        logging.info(f'[PERF] get_genome_analysis_overview started for {genomeAnalysisId}')

        # Get genome analysis from database
        stepStart = time.time()
        genomeAnalysis = await self.get_genome_analysis(genomeAnalysisId)
        logging.info(f'[PERF] get_genome_analysis took {time.time() - stepStart:.2f}s')

        # Fetch only metadata for all categories (no SNPs for fast loading)
        stepStart = time.time()

        # Query to get just the category metadata
        query = select(
            schema.GenomeAnalysisResultsTable.c.resultId,
            schema.GenomeAnalysisResultsTable.c.phenotypeGroup,
            schema.GenomeAnalysisResultsTable.c.phenotypeDescription,
            func.jsonb_array_length(schema.GenomeAnalysisResultsTable.c.snps).label('totalCount'),
        ).where(
            schema.GenomeAnalysisResultsTable.c.genomeAnalysisId == genomeAnalysisId
        )

        result = await self.database.execute(query=query)
        rows = result.mappings().all()
        logging.info(f'[PERF] Fetched {len(rows)} categories with metadata in {time.time() - stepStart:.2f}s')

        # Build category groups (no SNPs - frontend will load them on demand)
        stepStart = time.time()
        categoryGroups = []
        for row in rows:
            categoryGroup = resources.GenomeAnalysisCategoryGroup(
                genomeAnalysisResultId=row['resultId'],
                phenotypeGroup=row['phenotypeGroup'],
                phenotypeDescription=row['phenotypeDescription'],
                totalCount=row['totalCount'],
                topSnps=[],  # Empty - frontend loads SNPs when category is opened
            )
            categoryGroups.append(categoryGroup)

        # Sort category groups by total count (descending)
        categoryGroups = sorted(categoryGroups, key=lambda x: x.totalCount, reverse=True)
        logging.info(f'[PERF] Built and sorted {len(categoryGroups)} category groups in {time.time() - stepStart:.2f}s')

        totalTime = time.time() - startTime
        logging.info(f'[PERF] get_genome_analysis_overview completed in {totalTime:.2f}s')

        return resources.GenomeAnalysisOverview(
            genomeAnalysisId=genomeAnalysisId,
            summary=genomeAnalysis.summary or resources.GenomeAnalysisSummary(),
            categoryGroups=categoryGroups,
        )

    async def list_category_snps(self, genomeAnalysisId: str, genomeAnalysisResultId: str, offset: int = 0, limit: int = 20, minImportanceScore: float | None = None) -> resources.CategorySnpsPage:  # noqa: ARG002
        """Get paginated SNPs for a specific category."""
        # Get result from database
        dbResult = await schema.GenomeAnalysisResultsRepository.get(
            database=self.database,
            idValue=genomeAnalysisResultId,
        )

        # Convert JSON SNPs back to SNP resources
        snps = [resources.SNP.model_validate(snpDict) for snpDict in dbResult.snps]

        # Filter by minimum importance score if specified
        if minImportanceScore is not None:
            snps = [snp for snp in snps if snp.importanceScore and snp.importanceScore >= minImportanceScore]

        # Sort by risk priority, then importance score (highest first)
        snps = sorted(snps, key=lambda x: (self._get_risk_priority(x), x.importanceScore or 0), reverse=True)

        totalCount = len(snps)

        # Apply pagination
        paginatedSnps = snps[offset : offset + limit]

        return resources.CategorySnpsPage(
            genomeAnalysisResultId=dbResult.resultId,
            phenotypeGroup=dbResult.phenotypeGroup,
            phenotypeDescription=dbResult.phenotypeDescription,
            totalCount=totalCount,
            offset=offset,
            limit=limit,
            snps=paginatedSnps,
        )

    async def get_genome_analysis_result(self, genomeAnalysisId: str, genomeAnalysisResultId: str) -> resources.GenomeAnalysisResult:  # noqa: ARG002
        # Get result from database
        dbResult = await schema.GenomeAnalysisResultsRepository.get(
            database=self.database,
            idValue=genomeAnalysisResultId,
        )

        # Convert JSON SNPs back to SNP resources
        snps = [resources.SNP.model_validate(snpDict) for snpDict in dbResult.snps]

        return resources.GenomeAnalysisResult(
            genomeAnalysisResultId=dbResult.resultId,
            genomeAnalysisId=dbResult.genomeAnalysisId,
            phenotypeGroup=dbResult.phenotypeGroup,
            phenotypeDescription=dbResult.phenotypeDescription,
            snps=snps,
        )

    async def delete_genome_analysis(self, genomeAnalysisId: str) -> None:
        """Delete a genome analysis and all its results.

        Args:
            genomeAnalysisId: ID of the genome analysis to delete
        """
        # Delete all results first
        await schema.GenomeAnalysisResultsRepository.delete(
            database=self.database,
            fieldFilters=[StringFieldFilter(fieldName='genomeAnalysisId', eq=genomeAnalysisId)],
        )
        # Delete the genome analysis
        await schema.GenomeAnalysesRepository.delete(
            database=self.database,
            fieldFilters=[StringFieldFilter(fieldName='genomeAnalysisId', eq=genomeAnalysisId)],
        )

    def _get_risk_level(self, snp: resources.SNP) -> str:
        """Calculate risk level for a SNP (very_high, high, moderate, slight, lower, unknown)."""
        importanceScore = snp.importanceScore or 0
        userHasRiskAllele = snp.userHasRiskAllele or False
        oddsRatio = snp.oddsRatio or 1.0
        riskAlleleFrequency = snp.riskAlleleFrequency or 0

        # If risk allele is very common (>80% of population), it's basically baseline/normal
        # Downgrade the risk level since it's "priced in" to the population baseline
        isCommonVariant = riskAlleleFrequency > 0.8

        # Very high risk: strong research + user has risk allele + high odds ratio + not too common
        if importanceScore >= 30 and userHasRiskAllele and oddsRatio >= 2.0 and not isCommonVariant:
            return 'very_high'

        # High risk: strong research + user has risk allele + moderate odds ratio + not too common
        if importanceScore >= 30 and userHasRiskAllele and oddsRatio >= 1.5 and not isCommonVariant:
            return 'high'

        # Moderately higher risk: moderate research + user has risk allele + high odds ratio + not too common
        if importanceScore >= 15 and userHasRiskAllele and oddsRatio >= 2.0 and not isCommonVariant:
            return 'moderate'

        # Moderately higher risk: strong research + user has risk allele (even if common, but lower priority)
        if importanceScore >= 30 and userHasRiskAllele:
            return 'moderate' if not isCommonVariant else 'slight'

        # Slightly higher risk: moderate research + user has risk allele + moderate odds ratio
        if importanceScore >= 15 and userHasRiskAllele and oddsRatio >= 1.5:
            return 'slight'

        # Slightly higher risk: moderate research + user has risk allele
        if importanceScore >= 15 and userHasRiskAllele:
            return 'slight'

        # Lower risk: user does NOT have risk allele
        if not userHasRiskAllele:
            return 'lower'

        # Unknown risk: missing data
        return 'unknown'

    def _get_risk_priority(self, snp: resources.SNP) -> int:
        """Calculate risk priority for sorting SNPs (0-100, higher = more important)."""
        riskLevel = self._get_risk_level(snp)

        riskPriorities = {
            'very_high': 100,
            'high': 90,
            'moderate': 75,  # Average of 80 and 70
            'slight': 55,  # Average of 60 and 50
            'lower': 1,
            'unknown': 0,
        }

        return riskPriorities.get(riskLevel, 0)
