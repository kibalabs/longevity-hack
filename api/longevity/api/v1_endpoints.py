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


class GetGenomeAnalysisOverviewRequest(BaseModel):
    genomeAnalysisId: str


class GetGenomeAnalysisOverviewResponse(BaseModel):
    overview: resources.GenomeAnalysisOverview


class ListCategorySnpsRequest(BaseModel):
    genomeAnalysisId: str
    genomeAnalysisResultId: str  # Category ID
    offset: int = 0  # Number of SNPs to skip (default: 0)
    limit: int = 20  # Max SNPs to return (default: 20)
    minImportanceScore: float | None = None  # Filter by minimum importance score


class ListCategorySnpsResponse(BaseModel):
    categorySnpsPage: resources.CategorySnpsPage


class GetGenomeAnalysisResultRequest(BaseModel):
    genomeAnalysisId: str
    genomeAnalysisResultId: str


class GetGenomeAnalysisResultResponse(BaseModel):
    genomeAnalysisResult: resources.GenomeAnalysisResult


class GetExampleAnalysisIdRequest(BaseModel):
    pass


class GetExampleAnalysisIdResponse(BaseModel):
    genomeAnalysisId: str


class UploadGenomeFileRequest(BaseModel):
    genomeAnalysisId: str
    # Note: file will be in request.form['file'] in the actual handler


class UploadGenomeFileResponse(BaseModel):
    genomeAnalysis: resources.GenomeAnalysis


class AnalyzeCategoryRequest(BaseModel):
    genomeAnalysisId: str
    genomeAnalysisResultId: str  # Category ID to analyze


class AnalyzeCategoryResponse(BaseModel):
    categoryAnalysis: resources.CategoryAnalysis


class SubscribeToNotificationsRequest(BaseModel):
    email: str


class SubscribeToNotificationsResponse(BaseModel):
    pass


class ChatWithAgentRequest(BaseModel):
    genomeAnalysisId: str
    genomeAnalysisResultId: str
    message: str


class ChatWithAgentResponse(BaseModel):
    response: str
