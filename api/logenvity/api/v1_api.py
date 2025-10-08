import datetime

from core.api.api_request import KibaApiRequest
from core.api.json_route import json_route
from core.store.database import Database
from starlette.routing import Route

from logenvity.api import v1_endpoints as endpoints
from logenvity.api import v1_resources as resources
from logenvity.api.v1_resource_builder import ResourceBuilderV1
from logenvity.app_manager import AppManager


def create_v1_routes(appManager: AppManager, database: Database, resourceBuilder: ResourceBuilderV1) -> list[Route]:
    @json_route(requestType=endpoints.HealthCheckRequest, responseType=endpoints.HealthCheckResponse)
    async def health_check(request: KibaApiRequest[endpoints.HealthCheckRequest]) -> endpoints.HealthCheckResponse:  # noqa: ARG001
        healthStatus = resources.HealthStatus(status='ok', message='API is healthy', timestamp=datetime.datetime.now().isoformat())
        return endpoints.HealthCheckResponse(healthStatus=healthStatus)

    return [
        Route('/health', health_check, methods=['GET']),
    ]
