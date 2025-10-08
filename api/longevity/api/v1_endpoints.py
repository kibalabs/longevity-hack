from pydantic import BaseModel

from longevity.api import v1_resources as resources


class HealthCheckRequest(BaseModel):
    pass


class HealthCheckResponse(BaseModel):
    healthStatus: resources.HealthStatus
