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


class GenomeAnalysisResult(BaseModel):
    genomeAnalysisResultId: str
    genomeAnalysisId: str
    phenotypeGroup: str
    phenotypeDescription: str
    snps: list[SNP]


class GenomeAnalysisSummary(BaseModel):
    totalSnps: int | None = None
    matchedSnps: int | None = None
    totalAssociations: int | None = None
    topCategories: list[str] | None = None
    clinvarCount: int | None = None


class GenomeAnalysis(BaseModel):
    genomeAnalysisId: str
    fileName: str
    fileType: str
    detectedFormat: str | None  # "23andme", "ancestry", "vcf", "unknown", or None if not yet detected
    status: str  # "uploading", "validating", "parsing", "building_baseline", "completed", "failed"
    createdDate: str
    summary: GenomeAnalysisSummary | None = None
