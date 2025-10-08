from core.api.api_request import KibaApiRequest
from core.api.json_route import json_route
from core.store.database import Database
from starlette.routing import Route

from longevity.api import v1_endpoints as endpoints
from longevity.api import v1_resources as resources
from longevity.api.v1_resource_builder import ResourceBuilderV1
from longevity.app_manager import AppManager


class GenomeAnalysisNotFoundError(Exception):
    pass


class GenomeAnalysisResultNotFoundError(Exception):
    pass


def create_v1_routes(appManager: AppManager, database: Database, resourceBuilder: ResourceBuilderV1) -> list[Route]:  # noqa: ARG001
    @json_route(requestType=endpoints.HealthCheckRequest, responseType=endpoints.HealthCheckResponse)
    async def health_check(request: KibaApiRequest[endpoints.HealthCheckRequest]) -> endpoints.HealthCheckResponse:  # noqa: ARG001
        healthStatus = resources.HealthStatus(status='ok', message='API is healthy')
        return endpoints.HealthCheckResponse(healthStatus=healthStatus)

    @json_route(requestType=endpoints.CreateGenomeAnalysisRequest, responseType=endpoints.CreateGenomeAnalysisResponse)
    async def create_genome_analysis(request: KibaApiRequest[endpoints.CreateGenomeAnalysisRequest]) -> endpoints.CreateGenomeAnalysisResponse:
        genomeAnalysis = await appManager.create_genome_analysis(fileName=request.data.fileName, fileType=request.data.fileType)
        return endpoints.CreateGenomeAnalysisResponse(genomeAnalysis=genomeAnalysis)

    @json_route(requestType=endpoints.GetGenomeAnalysisRequest, responseType=endpoints.GetGenomeAnalysisResponse)
    async def get_genome_analysis(request: KibaApiRequest[endpoints.GetGenomeAnalysisRequest]) -> endpoints.GetGenomeAnalysisResponse:
        genomeAnalysis = await appManager.get_genome_analysis(genomeAnalysisId=request.data.genomeAnalysisId)
        return endpoints.GetGenomeAnalysisResponse(genomeAnalysis=genomeAnalysis)

    @json_route(requestType=endpoints.ListGenomeAnalysisResultsRequest, responseType=endpoints.ListGenomeAnalysisResultsResponse)
    async def list_genome_analysis_results(request: KibaApiRequest[endpoints.ListGenomeAnalysisResultsRequest]) -> endpoints.ListGenomeAnalysisResultsResponse:
        genomeAnalysisResults = await appManager.list_genome_analysis_results(genomeAnalysisId=request.data.genomeAnalysisId, phenotypeGroup=request.data.phenotypeGroup)
        return endpoints.ListGenomeAnalysisResultsResponse(genomeAnalysisResults=genomeAnalysisResults)

    @json_route(requestType=endpoints.GetGenomeAnalysisResultRequest, responseType=endpoints.GetGenomeAnalysisResultResponse)
    async def get_genome_analysis_result(request: KibaApiRequest[endpoints.GetGenomeAnalysisResultRequest]) -> endpoints.GetGenomeAnalysisResultResponse:
        genomeAnalysisResult = await appManager.get_genome_analysis_result(genomeAnalysisId=request.data.genomeAnalysisId, genomeAnalysisResultId=request.data.genomeAnalysisResultId)
        return endpoints.GetGenomeAnalysisResultResponse(genomeAnalysisResult=genomeAnalysisResult)

    @json_route(requestType=endpoints.GetExampleAnalysisIdRequest, responseType=endpoints.GetExampleAnalysisIdResponse)
    async def get_example_analysis_id(request: KibaApiRequest[endpoints.GetExampleAnalysisIdRequest]) -> endpoints.GetExampleAnalysisIdResponse:  # noqa: ARG001
        genomeAnalysisId = await appManager.get_example_analysis_id()
        return endpoints.GetExampleAnalysisIdResponse(genomeAnalysisId=genomeAnalysisId)

    return [
        Route('/health', health_check, methods=['GET']),
        Route('/genome-analyses', create_genome_analysis, methods=['POST']),
        Route('/genome-analyses/{genomeAnalysisId}', get_genome_analysis, methods=['GET']),
        Route('/genome-analyses/{genomeAnalysisId}/results', list_genome_analysis_results, methods=['GET']),
        Route('/genome-analyses/{genomeAnalysisId}/results/{genomeAnalysisResultId}', get_genome_analysis_result, methods=['GET']),
        Route('/example-analysis', get_example_analysis_id, methods=['GET']),
    ]
