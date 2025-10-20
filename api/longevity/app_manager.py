import uuid
from collections import defaultdict
from pathlib import Path

from core.exceptions import NotFoundException
from core.queues.message_queue import MessageQueue
from core.requester import Requester
from core.store.database import Database
from core.util import date_util
from core.util import file_util
from starlette.datastructures import UploadFile

from longevity import model
from longevity.api import v1_resources as resources
from longevity.genome_analyzer import GenomeAnalyzer
from longevity.messages import AnalyzeGenomeMessageContent
from longevity.store import schema
from longevity.store.entity_repository import StringFieldFilter

EXAMPLE_ANALYSIS_ID = 'example-analysis-123'


class AppManager:
    def __init__(self, database: Database, requester: Requester, workQueue: MessageQueue[Any]) -> None:
        self.database = database
        self.requester = requester
        self.workQueue = workQueue
        self.uploadsDir = Path(__file__).parent.parent / 'uploads'
        self.outputsDir = Path(__file__).parent.parent / 'outputs'
        self.uploadsDir.mkdir(parents=True, exist_ok=True)
        self.outputsDir.mkdir(parents=True, exist_ok=True)
        self.genomeAnalyzer = GenomeAnalyzer(database=self.database)
        self._create_example_analysis()

    async def create_genome_analysis(self, fileName: str, fileType: str) -> resources.GenomeAnalysis:
        genomeAnalysisId = str(uuid.uuid4())
        dbGenomeAnalysis = await schema.GenomeAnalysesRepository.create(
            database=self.database,
            genomeAnalysisId=genomeAnalysisId,
            userId='anonymous',
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
        # Get from database
        dbGenomeAnalysis = await schema.GenomeAnalysesRepository.get(
            database=self.database,
            idValue=genomeAnalysisId,
        )
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
        """Get overview of genome analysis with all categories and top 5 SNPs per category."""
        # Get genome analysis from database
        genomeAnalysis = await self.get_genome_analysis(genomeAnalysisId)

        # Get results from database
        dbResults = await schema.GenomeAnalysisResultsRepository.list_many(
            database=self.database,
            fieldFilters=[StringFieldFilter(fieldName='genomeAnalysisId', eq=genomeAnalysisId)],
        )

        # Convert database results to resources
        categoryGroups = []
        for dbResult in dbResults:
            # Convert JSON SNPs back to SNP resources
            snps = [resources.SNP.model_validate(snpDict) for snpDict in dbResult.snps]

            # Sort SNPs by risk priority, then importance score
            sortedSnps = sorted(snps, key=lambda x: (self._get_risk_priority(x), x.importanceScore or 0), reverse=True)

            categoryGroup = resources.GenomeAnalysisCategoryGroup(
                genomeAnalysisResultId=dbResult.resultId,
                phenotypeGroup=dbResult.phenotypeGroup,
                phenotypeDescription=dbResult.phenotypeDescription,
                totalCount=len(snps),
                topSnps=sortedSnps[:5],  # Top 5 SNPs
            )
            categoryGroups.append(categoryGroup)

        # Sort category groups by total count (descending)
        categoryGroups = sorted(categoryGroups, key=lambda x: x.totalCount, reverse=True)

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

    def _create_mock_results(self, genomeAnalysisId: str, fileName: str, fileType: str) -> None:  # noqa: ARG002
        # Mock SNP data for different phenotype groups
        drugResponseSnps = [
            resources.SNP(
                rsid='rs1801133',
                genotype='CT',
                chromosome='1',
                position=11856378,
                annotation='MTHFR gene - associated with folate metabolism and methotrexate response',
                confidence='High (replicated in multiple studies)',
                sources=['dbSNP', 'ClinVar', 'GWAS Catalog'],
            ),
            resources.SNP(
                rsid='rs4680',
                genotype='AG',
                chromosome='22',
                position=19963748,
                annotation='COMT gene - affects dopamine breakdown, linked to stress response and pain medication efficacy',
                confidence='High (well-established)',
                sources=['dbSNP', 'PharmGKB', 'GWAS Catalog'],
            ),
            resources.SNP(
                rsid='rs1051740',
                genotype='TT',
                chromosome='11',
                position=67584651,
                annotation='CYP2A6 gene - nicotine metabolism and smoking cessation drug response',
                confidence='High (validated in clinical trials)',
                sources=['dbSNP', 'PharmGKB'],
            ),
            resources.SNP(
                rsid='rs1799853',
                genotype='GG',
                chromosome='10',
                position=96702047,
                annotation='CYP2C9 gene - warfarin metabolism and dosing requirements',
                confidence='Very High (FDA recognized)',
                sources=['dbSNP', 'PharmGKB', 'ClinVar'],
            ),
            resources.SNP(
                rsid='rs4149056',
                genotype='TT',
                chromosome='12',
                position=21331549,
                annotation='SLCO1B1 gene - statin-induced myopathy risk',
                confidence='High (clinical guideline available)',
                sources=['dbSNP', 'PharmGKB', 'CPIC'],
            ),
        ]

        sleepSnps = [
            resources.SNP(
                rsid='rs73598374',
                genotype='AA',
                chromosome='2',
                position=48950954,
                annotation='ABCG2 gene - slow caffeine metabolizer, associated with caffeine sensitivity',
                confidence='Moderate (multiple small studies)',
                sources=['dbSNP', 'ClinVar'],
            ),
            resources.SNP(
                rsid='rs2472297',
                genotype='TT',
                chromosome='15',
                position=74758169,
                annotation='CYP1A2 gene - caffeine metabolism rate',
                confidence='High (replicated studies)',
                sources=['dbSNP', 'GWAS Catalog'],
            ),
            resources.SNP(
                rsid='rs1801260',
                genotype='CT',
                chromosome='4',
                position=56305131,
                annotation='CLOCK gene - circadian rhythm regulation, morning vs evening preference',
                confidence='Moderate (emerging research)',
                sources=['dbSNP', 'GWAS Catalog'],
            ),
            resources.SNP(
                rsid='rs228697',
                genotype='CC',
                chromosome='6',
                position=32006008,
                annotation='ADORA2A gene - adenosine receptor affecting sleep quality and caffeine response',
                confidence='Moderate (multiple studies)',
                sources=['dbSNP', 'PubMed'],
            ),
        ]

        longevitySnps = [
            resources.SNP(
                rsid='rs7412',
                genotype='CC',
                chromosome='19',
                position=44908684,
                annotation="APOE ε2/ε3/ε4 variants - associated with Alzheimer's risk and longevity. CC genotype indicates ε3/ε3 (most common, neutral risk)",
                confidence='Very High (extensively studied)',
                sources=['dbSNP', 'ClinVar', 'OMIM', 'AlzGene'],
            ),
            resources.SNP(
                rsid='rs429358',
                genotype='TT',
                chromosome='19',
                position=44908822,
                annotation="APOE ε4 variant - combined with rs7412, determines APOE genotype. TT indicates no ε4 alleles (lower Alzheimer's risk)",
                confidence='Very High (extensively studied)',
                sources=['dbSNP', 'ClinVar', 'OMIM'],
            ),
            resources.SNP(
                rsid='rs1042522',
                genotype='GC',
                chromosome='17',
                position=7676154,
                annotation='TP53 gene - tumor suppressor, associated with cancer risk and cellular aging',
                confidence='High (well-established)',
                sources=['dbSNP', 'ClinVar', 'COSMIC'],
            ),
            resources.SNP(
                rsid='rs2802292',
                genotype='GT',
                chromosome='6',
                position=31356116,
                annotation='FOXO3 gene - associated with exceptional longevity across multiple populations',
                confidence='High (replicated in centenarian studies)',
                sources=['dbSNP', 'GWAS Catalog', 'PubMed'],
            ),
            resources.SNP(
                rsid='rs1333049',
                genotype='CC',
                chromosome='9',
                position=22125504,
                annotation='CDKN2A/B locus - associated with cardiovascular disease and biological aging',
                confidence='Very High (large-scale GWAS)',
                sources=['dbSNP', 'GWAS Catalog', 'CARDIoGRAMplusC4D'],
            ),
        ]

        cardiovascularSnps = [
            resources.SNP(
                rsid='rs1801252',
                genotype='GG',
                chromosome='5',
                position=148826877,
                annotation='ADRB1 gene - beta-blocker response in heart disease treatment',
                confidence='High (pharmacogenomic studies)',
                sources=['dbSNP', 'PharmGKB'],
            ),
            resources.SNP(
                rsid='rs1799983',
                genotype='GT',
                chromosome='7',
                position=150696111,
                annotation='NOS3 gene - nitric oxide production, blood pressure regulation',
                confidence='Moderate (association studies)',
                sources=['dbSNP', 'GWAS Catalog'],
            ),
            resources.SNP(
                rsid='rs662799',
                genotype='AG',
                chromosome='11',
                position=116778201,
                annotation='APOA5 gene - triglyceride levels and cardiovascular disease risk',
                confidence='High (replicated studies)',
                sources=['dbSNP', 'GWAS Catalog'],
            ),
        ]

        metabolicSnps = [
            resources.SNP(
                rsid='rs9939609',
                genotype='AT',
                chromosome='16',
                position=53820527,
                annotation='FTO gene - obesity risk and metabolic rate, associated with BMI variation',
                confidence='Very High (genome-wide significant)',
                sources=['dbSNP', 'GWAS Catalog', 'GIANT Consortium'],
            ),
            resources.SNP(
                rsid='rs7903146',
                genotype='CT',
                chromosome='10',
                position=112998590,
                annotation='TCF7L2 gene - type 2 diabetes risk, strongest common genetic risk factor',
                confidence='Very High (extensively replicated)',
                sources=['dbSNP', 'GWAS Catalog', 'DIAGRAM'],
            ),
            resources.SNP(
                rsid='rs1801282',
                genotype='CG',
                chromosome='3',
                position=12351626,
                annotation='PPARG gene - insulin sensitivity and type 2 diabetes risk',
                confidence='High (meta-analysis confirmed)',
                sources=['dbSNP', 'ClinVar', 'GWAS Catalog'],
            ),
            resources.SNP(
                rsid='rs780094',
                genotype='CT',
                chromosome='2',
                position=27508073,
                annotation='GCKR gene - affects glucose and lipid metabolism, fasting glucose levels',
                confidence='High (large cohort studies)',
                sources=['dbSNP', 'GWAS Catalog'],
            ),
        ]

        immuneSnps = [
            resources.SNP(
                rsid='rs1800629',
                genotype='GG',
                chromosome='6',
                position=31543031,
                annotation='TNF gene - tumor necrosis factor production, inflammatory response',
                confidence='Moderate (multiple associations)',
                sources=['dbSNP', 'ClinVar'],
            ),
            resources.SNP(
                rsid='rs2476601',
                genotype='AA',
                chromosome='1',
                position=113834946,
                annotation='PTPN22 gene - autoimmune disease risk (rheumatoid arthritis, type 1 diabetes)',
                confidence='High (multiple autoimmune conditions)',
                sources=['dbSNP', 'ClinVar', 'ImmunoBase'],
            ),
            resources.SNP(
                rsid='rs3135388',
                genotype='AA',
                chromosome='6',
                position=32665748,
                annotation='HLA-DRB1 region - immune system recognition, autoimmune disease susceptibility',
                confidence='Moderate (HLA complex)',
                sources=['dbSNP', 'ImmunoBase'],
            ),
        ]
        # Mock results are not persisted - this function is for demonstration purposes only

    def _create_example_analysis(self) -> None:
        """Create a pre-existing completed example analysis."""
        # Note: Example analysis is created in-memory only for demo purposes
        # In production, this should create actual database records

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
