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
    manualCategory: str | None = None  # Manual category from categories_spiros.csv
    oddsRatio: float | None = None
    riskAlleleFrequency: float | None = None
    studyDescription: str | None = None
    userHasRiskAllele: bool | None = None
    riskLevel: str | None = None  # "very_high", "high", "moderate", "slight", "lower", "unknown"
    pubmedId: str | None = None


class GenomeAnalysisResult(BaseModel):
    genomeAnalysisResultId: str
    genomeAnalysisId: str
    category: str
    categoryDescription: str
    snps: list[SNP]


class GenomeAnalysisCategoryGroup(BaseModel):
    """A category group with basic info. SNPs are loaded on-demand by frontend."""

    genomeAnalysisResultId: str
    category: str
    categoryDescription: str
    totalCount: int  # Total number of SNPs in this category
    riskCounts: dict[str, int] = {}  # Count of SNPs by risk level
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
    category: str
    categoryDescription: str
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


class PaperReference(BaseModel):
    """Reference to a research paper."""

    pubmedId: str
    title: str | None = None
    authors: str | None = None
    journal: str | None = None
    year: str | None = None
    abstract: str | None = None


class CategoryAnalysis(BaseModel):
    """AI-generated analysis of a genetic category."""

    category: str
    categoryDescription: str
    analysis: str  # The AI-generated analysis text
    papersUsed: list[PaperReference]
    snpsAnalyzed: int
