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


class GenomeAnalysisResult(BaseModel):
    genomeAnalysisResultId: str
    genomeAnalysisId: str
    phenotypeGroup: str
    phenotypeDescription: str
    snps: list[SNP]


class GenomeAnalysis(BaseModel):
    genomeAnalysisId: str
    fileName: str
    fileType: str
    status: str  # "processing", "completed", "failed"
    createdDate: str
