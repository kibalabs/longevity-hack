from pydantic import BaseModel

from longevity.api import v1_resources as resources


class HealthCheckRequest(BaseModel):
    pass


class HealthCheckResponse(BaseModel):
    healthStatus: resources.HealthStatus


class CreateGenomeAnalysisRequest(BaseModel):
    fileName: str
    fileType: str


class CreateGenomeAnalysisResponse(BaseModel):
    genomeAnalysis: resources.GenomeAnalysis


class GetGenomeAnalysisRequest(BaseModel):
    genomeAnalysisId: str


class GetGenomeAnalysisResponse(BaseModel):
    genomeAnalysis: resources.GenomeAnalysis


class ListGenomeAnalysisResultsRequest(BaseModel):
    genomeAnalysisId: str
    phenotypeGroup: str | None = None


class ListGenomeAnalysisResultsResponse(BaseModel):
    genomeAnalysisResults: list[resources.GenomeAnalysisResult]


class GetGenomeAnalysisResultRequest(BaseModel):
    genomeAnalysisId: str
    genomeAnalysisResultId: str


class GetGenomeAnalysisResultResponse(BaseModel):
    genomeAnalysisResult: resources.GenomeAnalysisResult


class GetExampleAnalysisIdRequest(BaseModel):
    pass


class GetExampleAnalysisIdResponse(BaseModel):
    genomeAnalysisId: str
