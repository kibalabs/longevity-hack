import { RestMethod, ServiceClient } from '@kibalabs/core';

import * as Endpoints from './endpoints';
import * as Resources from './resources';

export class LongevityClient extends ServiceClient {
  // eslint-disable-next-line class-methods-use-this
  private getHeaders = (): Record<string, string> => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    return headers;
  };

  public healthCheck = async (): Promise<Resources.HealthStatus> => {
    const method = RestMethod.GET;
    const path = 'v1/health-check';
    const request = new Endpoints.HealthCheckRequest();
    const response = await this.makeRequest(method, path, request, Endpoints.HealthCheckResponse, this.getHeaders());
    return response.healthStatus;
  };
}
