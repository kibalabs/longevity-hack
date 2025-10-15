import asyncio
import json
import uuid
from pathlib import Path

from core.exceptions import NotFoundException
from core.requester import Requester
from core.store.database import Database
from core.util import date_util, file_util

from longevity import model
from longevity.api import v1_resources as resources
from longevity.genome_analyzer import GenomeAnalyzer

EXAMPLE_ANALYSIS_ID = 'example-analysis-123'


class AppManager:
    def __init__(self, database: Database, requester: Requester) -> None:
        self.database = database
        self.requester = requester
        # In-memory mock storage for the hackathon
        self.genomeAnalysisStore: dict[str, resources.GenomeAnalysis] = {}
        self.genomeAnalysisResultsStore: dict[str, list[resources.GenomeAnalysisResult]] = {}
        # Real genome analyzer
        uploadsDir = Path(__file__).parent.parent / "uploads"
        outputsDir = Path(__file__).parent.parent / "outputs"
        gwasDir = Path(__file__).parent.parent / ".data" / "snps-gwas"
        annotationsDir = Path(__file__).parent.parent / ".data" / "snps"

        uploadsDir.mkdir(parents=True, exist_ok=True)
        outputsDir.mkdir(parents=True, exist_ok=True)

        self.uploadsDir = uploadsDir
        self.outputsDir = outputsDir
        self.gwasDir = gwasDir
        self.annotationsDir = annotationsDir
        self.genomeAnalyzer = GenomeAnalyzer(gwasDir=gwasDir, annotationsDir=annotationsDir)
        self._create_example_analysis()

    async def create_genome_analysis(self, fileName: str, fileType: str) -> resources.GenomeAnalysis:
        genomeAnalysisId = str(uuid.uuid4())
        genomeAnalysis = resources.GenomeAnalysis(
            genomeAnalysisId=genomeAnalysisId,
            fileName=fileName,
            fileType=fileType,
            detectedFormat=None,  # Will be detected during analysis
            status='waiting_for_upload',  # Changed from 'uploading'
            createdDate=date_util.datetime_to_string(date_util.datetime_from_now()),
        )
        self.genomeAnalysisStore[genomeAnalysisId] = genomeAnalysis
        return genomeAnalysis

    async def get_example_analysis_id(self) -> str:
        return EXAMPLE_ANALYSIS_ID

    async def upload_and_analyze_genome_file(self, genomeAnalysisId: str, file) -> resources.GenomeAnalysis:
        """Upload genome file and start analysis asynchronously."""
        genomeAnalysis = self.genomeAnalysisStore.get(genomeAnalysisId)
        if not genomeAnalysis:
            raise NotFoundException

        # Update status to uploading
        genomeAnalysis.status = 'uploading'
        self.genomeAnalysisStore[genomeAnalysisId] = genomeAnalysis

        # Save the uploaded file (async)
        safeName = Path(genomeAnalysis.fileName).name
        uploadPath = self.uploadsDir / f"{genomeAnalysisId}_{safeName}"
        content = await file.read()

        # Write file asynchronously to avoid blocking
        await file_util.write_file_bytes(str(uploadPath), content)

        # Update status to validating
        genomeAnalysis.status = 'validating'
        self.genomeAnalysisStore[genomeAnalysisId] = genomeAnalysis

        # Start analysis in background
        asyncio.create_task(self._run_genome_analysis(genomeAnalysisId, uploadPath))

        return genomeAnalysis

    async def _run_genome_analysis(self, genomeAnalysisId: str, inputFilePath: Path) -> None:
        """Run the genome analysis in the background."""
        genomeAnalysis = self.genomeAnalysisStore[genomeAnalysisId]
        genomeAnalysis.status = 'parsing'
        self.genomeAnalysisStore[genomeAnalysisId] = genomeAnalysis
        genomeContent = await file_util.read_file(str(inputFilePath))
        async def read_gwas_file(rsid: str) -> dict | None:
            gwasFile = self.gwasDir / f'{rsid}.json'
            if not gwasFile.exists():
                return None
            content = await file_util.read_file(str(gwasFile))
            return json.loads(content)

        async def read_annotation_file(rsid: str) -> dict | None:
            annotationFile = self.annotationsDir / f'{rsid}.json'
            if not annotationFile.exists():
                return None
            content = await file_util.read_file(str(annotationFile))
            return json.loads(content)
        analysisResult = await self.genomeAnalyzer.analyze_genome(
            genomeContent=genomeContent,
            read_gwas_file=read_gwas_file,
            read_annotation_file=read_annotation_file
        )
        genomeAnalysis.status = 'building_baseline'
        self.genomeAnalysisStore[genomeAnalysisId] = genomeAnalysis
        outputPath = self.outputsDir / f"{genomeAnalysisId}.json"
        resultContent = analysisResult.model_dump_json(indent=2)
        await file_util.write_file(str(outputPath), resultContent)
        self._create_real_results(genomeAnalysisId, analysisResult)
        genomeAnalysis.status = 'completed'
        genomeAnalysis.detectedFormat = '23andme'
        self.genomeAnalysisStore[genomeAnalysisId] = genomeAnalysis

    def _create_real_results(self, genomeAnalysisId: str, analysisData: model.GenomeAnalysisResult) -> None:
        """Create genome analysis results from real analysis output."""
        # Update analysis with summary
        genomeAnalysis = self.genomeAnalysisStore[genomeAnalysisId]
        genomeAnalysis.summary = resources.GenomeAnalysisSummary(
            totalSnps=analysisData.summary.totalSnps,
            matchedSnps=analysisData.summary.matchedSnps,
            totalAssociations=analysisData.summary.totalAssociations,
            topCategories=analysisData.summary.topCategories,
            clinvarCount=analysisData.summary.clinvarCount,
        )
        self.genomeAnalysisStore[genomeAnalysisId] = genomeAnalysis

        # Use phenotype_groups from the analyzer
        results = []
        for category, associations in analysisData.phenotypeGroups.items():
            # Deduplicate by rsid - keep highest scoring association per SNP
            seenRsids = {}
            for assoc in associations:
                if assoc.rsid not in seenRsids:
                    seenRsids[assoc.rsid] = assoc
                elif assoc.importanceScore > seenRsids[assoc.rsid].importanceScore:
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
                    annotation=f"{assoc.trait} - {assoc.effectStrength or 'Unknown'} effect. " +
                              (f"ClinVar: {assoc.clinvarCondition}" if assoc.clinvarCondition else ""),
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
                )
                snps.append(snp)

            if snps:
                result = resources.GenomeAnalysisResult(
                    genomeAnalysisResultId=str(uuid.uuid4()),
                    genomeAnalysisId=genomeAnalysisId,
                    phenotypeGroup=category,
                    phenotypeDescription=f"Genetic variants associated with {category.lower()}",
                    snps=snps,
                )
                results.append(result)

        self.genomeAnalysisResultsStore[genomeAnalysisId] = results

    async def get_genome_analysis(self, genomeAnalysisId: str) -> resources.GenomeAnalysis:
        genomeAnalysis = self.genomeAnalysisStore.get(genomeAnalysisId)
        if not genomeAnalysis:
            raise NotFoundException

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

        results = [
            resources.GenomeAnalysisResult(
                genomeAnalysisResultId=str(uuid.uuid4()),
                genomeAnalysisId=genomeAnalysisId,
                phenotypeGroup='Drug Response',
                phenotypeDescription='How your genes may affect medication metabolism and efficacy',
                snps=drugResponseSnps,
            ),
            resources.GenomeAnalysisResult(
                genomeAnalysisResultId=str(uuid.uuid4()),
                genomeAnalysisId=genomeAnalysisId,
                phenotypeGroup='Sleep & Stimulants',
                phenotypeDescription='Genetic factors influencing sleep patterns and caffeine sensitivity',
                snps=sleepSnps,
            ),
            resources.GenomeAnalysisResult(
                genomeAnalysisResultId=str(uuid.uuid4()),
                genomeAnalysisId=genomeAnalysisId,
                phenotypeGroup='Longevity & Aging',
                phenotypeDescription='Variants associated with lifespan and age-related conditions',
                snps=longevitySnps,
            ),
            resources.GenomeAnalysisResult(
                genomeAnalysisResultId=str(uuid.uuid4()),
                genomeAnalysisId=genomeAnalysisId,
                phenotypeGroup='Cardiovascular Health',
                phenotypeDescription='Genetic variants affecting heart health and blood pressure',
                snps=cardiovascularSnps,
            ),
            resources.GenomeAnalysisResult(
                genomeAnalysisResultId=str(uuid.uuid4()),
                genomeAnalysisId=genomeAnalysisId,
                phenotypeGroup='Metabolic Traits',
                phenotypeDescription='Genes influencing weight, blood sugar, and metabolic function',
                snps=metabolicSnps,
            ),
            resources.GenomeAnalysisResult(
                genomeAnalysisResultId=str(uuid.uuid4()),
                genomeAnalysisId=genomeAnalysisId,
                phenotypeGroup='Immune System',
                phenotypeDescription='Genetic factors affecting immune response and autoimmune risk',
                snps=immuneSnps,
            ),
        ]
        self.genomeAnalysisResultsStore[genomeAnalysisId] = results

    def _create_example_analysis(self) -> None:
        """Create a pre-existing completed example analysis."""
        exampleAnalysis = resources.GenomeAnalysis(
            genomeAnalysisId=EXAMPLE_ANALYSIS_ID,
            fileName='example_genome_23andme.txt',
            fileType='text/plain',
            detectedFormat='23andme',
            status='completed',
            createdDate=date_util.datetime_to_string(date_util.datetime_from_now()),
        )
        self.genomeAnalysisStore[EXAMPLE_ANALYSIS_ID] = exampleAnalysis
        self._create_mock_results(EXAMPLE_ANALYSIS_ID, exampleAnalysis.fileName, exampleAnalysis.fileType)
