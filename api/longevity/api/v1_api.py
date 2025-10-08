from core.api.api_request import KibaApiRequest
from core.api.json_route import json_route
from core.store.database import Database
from starlette.routing import Route

from longevity.api import v1_endpoints as endpoints
from longevity.api import v1_resources as resources
from longevity.api.v1_resource_builder import ResourceBuilderV1
from longevity.app_manager import AppManager


def create_v1_routes(appManager: AppManager, database: Database, resourceBuilder: ResourceBuilderV1) -> list[Route]:  # noqa: ARG001
    @json_route(requestType=endpoints.HealthCheckRequest, responseType=endpoints.HealthCheckResponse)
    async def health_check(request: KibaApiRequest[endpoints.HealthCheckRequest]) -> endpoints.HealthCheckResponse:  # noqa: ARG001
        healthStatus = resources.HealthStatus(status='ok', message='API is healthy')
        return endpoints.HealthCheckResponse(healthStatus=healthStatus)

    return [
        Route('/health', health_check, methods=['GET']),
    ]
