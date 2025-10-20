from pydantic import BaseModel


class HealthStatus(BaseModel):
    status: str
    message: str


class SNP(BaseModel):
    rsid: str
    genotype: str
    chromosome: str
    position: int
    annotation: str
    confidence: str
    sources: list[str]
    # Additional fields from real analysis
    trait: str | None = None
    importanceScore: float | None = None
    pValue: str | None = None
    effectStrength: str | None = None
    riskAllele: str | None = None
    clinvarCondition: str | None = None
    clinvarSignificance: int | None = None
    oddsRatio: float | None = None
    riskAlleleFrequency: float | None = None
    studyDescription: str | None = None
    userHasRiskAllele: bool | None = None
    riskLevel: str | None = None  # "very_high", "high", "moderate", "slight", "lower", "unknown"


class GenomeAnalysisResult(BaseModel):
    genomeAnalysisResultId: str
    genomeAnalysisId: str
    phenotypeGroup: str
    phenotypeDescription: str
    snps: list[SNP]


class GenomeAnalysisCategoryGroup(BaseModel):
    """A category group with basic info. SNPs are loaded on-demand by frontend."""

    genomeAnalysisResultId: str
    phenotypeGroup: str
    phenotypeDescription: str
    totalCount: int  # Total number of SNPs in this category
    topSnps: list[SNP] = []  # Empty in overview, frontend loads on-demand when category opens


class GenomeAnalysisSummary(BaseModel):
    totalSnps: int | None = None
    matchedSnps: int | None = None
    totalAssociations: int | None = None
    clinvarCount: int | None = None


class GenomeAnalysisOverview(BaseModel):
    """Overview of genome analysis with all categories and their top results."""

    genomeAnalysisId: str
    summary: GenomeAnalysisSummary
    categoryGroups: list[GenomeAnalysisCategoryGroup]


class CategorySnpsPage(BaseModel):
    """Paginated SNPs for a specific category."""

    genomeAnalysisResultId: str
    phenotypeGroup: str
    phenotypeDescription: str
    totalCount: int
    offset: int
    limit: int
    snps: list[SNP]


class GenomeAnalysis(BaseModel):
    genomeAnalysisId: str
    fileName: str
    fileType: str
    detectedFormat: str | None  # "23andme", "ancestry", "vcf", "unknown", or None if not yet detected
    status: str  # "uploading", "validating", "parsing", "building_baseline", "completed", "failed"
    createdDate: str
    summary: GenomeAnalysisSummary | None = None
