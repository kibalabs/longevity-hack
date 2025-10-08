import random
import uuid

from core.exceptions import NotFoundException
from core.store.database import Database
from core.util import date_util

from longevity.api import v1_resources as resources

COMPLETION_PROBABILITY = 0.25  # 25% chance to advance to next phase on each poll
EXAMPLE_ANALYSIS_ID = 'example-analysis-123'

# Status progression phases
STATUS_PHASES = ['uploading', 'validating', 'parsing', 'building_baseline', 'completed']


class AppManager:
    def __init__(self, database: Database) -> None:
        self.database = database
        # In-memory mock storage for the hackathon
        self.genomeAnalysisStore: dict[str, resources.GenomeAnalysis] = {}
        self.genomeAnalysisResultsStore: dict[str, list[resources.GenomeAnalysisResult]] = {}
        self._create_example_analysis()

    async def create_genome_analysis(self, fileName: str, fileType: str) -> resources.GenomeAnalysis:
        genomeAnalysisId = str(uuid.uuid4())
        genomeAnalysis = resources.GenomeAnalysis(
            genomeAnalysisId=genomeAnalysisId,
            fileName=fileName,
            fileType=fileType,
            status='uploading',
            createdDate=date_util.datetime_to_string(date_util.datetime_from_now()),
        )
        self.genomeAnalysisStore[genomeAnalysisId] = genomeAnalysis
        return genomeAnalysis

    async def get_example_analysis_id(self) -> str:
        return EXAMPLE_ANALYSIS_ID

    async def get_genome_analysis(self, genomeAnalysisId: str) -> resources.GenomeAnalysis:
        genomeAnalysis = self.genomeAnalysisStore.get(genomeAnalysisId)
        if not genomeAnalysis:
            raise NotFoundException

        # If already completed, return it
        if genomeAnalysis.status == 'completed':
            return genomeAnalysis

        # If in a processing phase, advance to next phase with probability
        currentStatus = genomeAnalysis.status
        if currentStatus in STATUS_PHASES[:-1] and random.random() < COMPLETION_PROBABILITY:  # noqa: S311
            currentIndex = STATUS_PHASES.index(currentStatus)
            nextStatus = STATUS_PHASES[currentIndex + 1]
            genomeAnalysis.status = nextStatus

            # If we just completed, create the mock results
            if nextStatus == 'completed':
                self._create_mock_results(genomeAnalysisId, genomeAnalysis.fileName, genomeAnalysis.fileType)

            self.genomeAnalysisStore[genomeAnalysisId] = genomeAnalysis

        return genomeAnalysis

    async def list_genome_analysis_results(self, genomeAnalysisId: str, phenotypeGroup: str | None = None) -> list[resources.GenomeAnalysisResult]:
        results = self.genomeAnalysisResultsStore.get(genomeAnalysisId, [])
        if phenotypeGroup:
            results = [result for result in results if result.phenotypeGroup == phenotypeGroup]
        return results

    async def get_genome_analysis_result(self, genomeAnalysisId: str, genomeAnalysisResultId: str) -> resources.GenomeAnalysisResult:
        results = self.genomeAnalysisResultsStore.get(genomeAnalysisId, [])
        for result in results:
            if result.genomeAnalysisResultId == genomeAnalysisResultId:
                return result
        raise NotFoundException

    def _create_mock_results(self, genomeAnalysisId: str, fileName: str, fileType: str) -> None:  # noqa: ARG002
        # Mock SNP data for different phenotype groups
        drugResponseSnps = [
            resources.SNP(
                rsid='rs1801133',
                genotype='CT',
                chromosome='1',
                position=11856378,
                annotation='MTHFR gene - associated with folate metabolism',
                confidence='High (replicated in multiple studies)',
                sources=['dbSNP', 'ClinVar', 'GWAS Catalog'],
            ),
            resources.SNP(
                rsid='rs4680',
                genotype='AG',
                chromosome='22',
                position=19963748,
                annotation='COMT gene - affects dopamine breakdown, linked to stress response',
                confidence='High (well-established)',
                sources=['dbSNP', 'PharmGKB', 'GWAS Catalog'],
            ),
        ]
        sleepSnps = [
            resources.SNP(
                rsid='rs73598374',
                genotype='AA',
                chromosome='2',
                position=48950954,
                annotation='ABCG2 gene - associated with caffeine metabolism',
                confidence='Moderate (multiple small studies)',
                sources=['dbSNP', 'ClinVar'],
            ),
        ]
        longevitySnps = [
            resources.SNP(
                rsid='rs7412',
                genotype='CC',
                chromosome='19',
                position=44908684,
                annotation="APOE ε2/ε3/ε4 variants - associated with Alzheimer's risk and longevity",
                confidence='Very High (extensively studied)',
                sources=['dbSNP', 'ClinVar', 'OMIM', 'AlzGene'],
            ),
        ]
        results = [
            resources.GenomeAnalysisResult(
                genomeAnalysisResultId=str(uuid.uuid4()),
                genomeAnalysisId=genomeAnalysisId,
                phenotypeGroup='Drug Response',
                phenotypeDescription='How your genes may affect medication metabolism and efficacy',
                snps=drugResponseSnps,
            ),
            resources.GenomeAnalysisResult(
                genomeAnalysisResultId=str(uuid.uuid4()), genomeAnalysisId=genomeAnalysisId, phenotypeGroup='Sleep & Stimulants', phenotypeDescription='Genetic factors influencing sleep patterns and caffeine sensitivity', snps=sleepSnps
            ),
            resources.GenomeAnalysisResult(
                genomeAnalysisResultId=str(uuid.uuid4()),
                genomeAnalysisId=genomeAnalysisId,
                phenotypeGroup='Longevity & Aging',
                phenotypeDescription='Variants associated with lifespan and age-related conditions',
                snps=longevitySnps,
            ),
        ]
        self.genomeAnalysisResultsStore[genomeAnalysisId] = results

    def _create_example_analysis(self) -> None:
        """Create a pre-existing completed example analysis."""
        exampleAnalysis = resources.GenomeAnalysis(
            genomeAnalysisId=EXAMPLE_ANALYSIS_ID,
            fileName='example_genome_23andme.txt',
            fileType='text/plain',
            status='completed',
            createdDate=date_util.datetime_to_string(date_util.datetime_from_now()),
        )
        self.genomeAnalysisStore[EXAMPLE_ANALYSIS_ID] = exampleAnalysis
        self._create_mock_results(EXAMPLE_ANALYSIS_ID, exampleAnalysis.fileName, exampleAnalysis.fileType)
