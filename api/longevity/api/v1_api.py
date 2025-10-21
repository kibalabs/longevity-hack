import logging
import time

from core.api.api_request import KibaApiRequest
from core.api.json_route import json_route
from core.store.database import Database
from starlette.requests import Request
from starlette.responses import JSONResponse
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

    @json_route(requestType=endpoints.GetGenomeAnalysisOverviewRequest, responseType=endpoints.GetGenomeAnalysisOverviewResponse)
    async def get_genome_analysis_overview(request: KibaApiRequest[endpoints.GetGenomeAnalysisOverviewRequest]) -> endpoints.GetGenomeAnalysisOverviewResponse:
        startTime = time.time()
        logging.info(f'[PERF] API get_genome_analysis_overview started for {request.data.genomeAnalysisId}')

        overview = await appManager.get_genome_analysis_overview(genomeAnalysisId=request.data.genomeAnalysisId)

        totalTime = time.time() - startTime
        logging.info(f'[PERF] API get_genome_analysis_overview completed in {totalTime:.2f}s')

        return endpoints.GetGenomeAnalysisOverviewResponse(overview=overview)

    @json_route(requestType=endpoints.ListCategorySnpsRequest, responseType=endpoints.ListCategorySnpsResponse)
    async def list_category_snps(request: KibaApiRequest[endpoints.ListCategorySnpsRequest]) -> endpoints.ListCategorySnpsResponse:
        categorySnpsPage = await appManager.list_category_snps(
            genomeAnalysisId=request.data.genomeAnalysisId,
            genomeAnalysisResultId=request.data.genomeAnalysisResultId,
            offset=request.data.offset,
            limit=request.data.limit,
            minImportanceScore=request.data.minImportanceScore,
        )
        return endpoints.ListCategorySnpsResponse(categorySnpsPage=categorySnpsPage)

    @json_route(requestType=endpoints.GetGenomeAnalysisResultRequest, responseType=endpoints.GetGenomeAnalysisResultResponse)
    async def get_genome_analysis_result(request: KibaApiRequest[endpoints.GetGenomeAnalysisResultRequest]) -> endpoints.GetGenomeAnalysisResultResponse:
        genomeAnalysisResult = await appManager.get_genome_analysis_result(genomeAnalysisId=request.data.genomeAnalysisId, genomeAnalysisResultId=request.data.genomeAnalysisResultId)
        return endpoints.GetGenomeAnalysisResultResponse(genomeAnalysisResult=genomeAnalysisResult)

    @json_route(requestType=endpoints.GetExampleAnalysisIdRequest, responseType=endpoints.GetExampleAnalysisIdResponse)
    async def get_example_analysis_id(request: KibaApiRequest[endpoints.GetExampleAnalysisIdRequest]) -> endpoints.GetExampleAnalysisIdResponse:  # noqa: ARG001
        genomeAnalysisId = await appManager.get_example_analysis_id()
        return endpoints.GetExampleAnalysisIdResponse(genomeAnalysisId=genomeAnalysisId)

    @json_route(requestType=endpoints.AnalyzeCategoryRequest, responseType=endpoints.AnalyzeCategoryResponse)
    async def analyze_category(request: KibaApiRequest[endpoints.AnalyzeCategoryRequest]) -> endpoints.AnalyzeCategoryResponse:
        categoryAnalysis = await appManager.analyze_category(genomeAnalysisId=request.data.genomeAnalysisId, genomeAnalysisResultId=request.data.genomeAnalysisResultId)
        return endpoints.AnalyzeCategoryResponse(categoryAnalysis=categoryAnalysis)

    @json_route(requestType=endpoints.SubscribeToNotificationsRequest, responseType=endpoints.SubscribeToNotificationsResponse)
    async def subscribe_to_notifications(request: KibaApiRequest[endpoints.SubscribeToNotificationsRequest]) -> endpoints.SubscribeToNotificationsResponse:
        await appManager.send_subscription_notification(email=request.data.email)
        return endpoints.SubscribeToNotificationsResponse()

    async def upload_genome_file(request: Request) -> JSONResponse:
        """Handle multipart file upload for genome analysis."""
        genomeAnalysisId = request.path_params['genomeAnalysisId']

        # Get the uploaded file from multipart form data
        form = await request.form()
        file = form.get('file')

        if not file:
            return JSONResponse({'error': 'No file provided'}, status_code=400)

        # Start the upload and analysis process
        genomeAnalysis = await appManager.upload_and_analyze_genome_file(genomeAnalysisId=genomeAnalysisId, file=file)

        # Return the updated analysis object
        return JSONResponse(
            {
                'genomeAnalysis': {
                    'genomeAnalysisId': genomeAnalysis.genomeAnalysisId,
                    'fileName': genomeAnalysis.fileName,
                    'fileType': genomeAnalysis.fileType,
                    'detectedFormat': genomeAnalysis.detectedFormat,
                    'status': genomeAnalysis.status,
                    'createdDate': genomeAnalysis.createdDate,
                }
            }
        )

    return [
        Route('/health', health_check, methods=['GET']),
        Route('/genome-analyses', create_genome_analysis, methods=['POST']),
        Route('/genome-analyses/{genomeAnalysisId}', get_genome_analysis, methods=['GET']),
        Route('/genome-analyses/{genomeAnalysisId}/upload', upload_genome_file, methods=['POST']),
        Route('/genome-analyses/{genomeAnalysisId}/overview', get_genome_analysis_overview, methods=['GET']),
        Route('/genome-analyses/{genomeAnalysisId}/results/{genomeAnalysisResultId}/snps', list_category_snps, methods=['GET']),
        Route('/genome-analyses/{genomeAnalysisId}/results/{genomeAnalysisResultId}', get_genome_analysis_result, methods=['GET']),
        Route('/genome-analyses/{genomeAnalysisId}/results/{genomeAnalysisResultId}/analyze', analyze_category, methods=['POST']),
        Route('/example-analysis', get_example_analysis_id, methods=['GET']),
        Route('/subscribe-to-notifications', subscribe_to_notifications, methods=['POST']),
    ]
