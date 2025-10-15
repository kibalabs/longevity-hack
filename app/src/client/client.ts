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

  public createGenomeAnalysis = async (fileName: string, fileType: string): Promise<Resources.GenomeAnalysis> => {
    const method = RestMethod.POST;
    const path = 'v1/genome-analyses';
    const request = new Endpoints.CreateGenomeAnalysisRequest(fileName, fileType);
    const response = await this.makeRequest(method, path, request, Endpoints.CreateGenomeAnalysisResponse, this.getHeaders());
    return response.genomeAnalysis;
  };

  public getGenomeAnalysis = async (genomeAnalysisId: string): Promise<Resources.GenomeAnalysis> => {
    const method = RestMethod.GET;
    const path = `v1/genome-analyses/${genomeAnalysisId}`;
    const request = new Endpoints.GetGenomeAnalysisRequest(genomeAnalysisId);
    const response = await this.makeRequest(method, path, request, Endpoints.GetGenomeAnalysisResponse, this.getHeaders());
    return response.genomeAnalysis;
  };

  public listGenomeAnalysisResults = async (genomeAnalysisId: string, phenotypeGroup: string | null = null): Promise<Resources.GenomeAnalysisResult[]> => {
    const method = RestMethod.GET;
    const pathBase = `v1/genome-analyses/${genomeAnalysisId}/results`;
    const path = phenotypeGroup ? `${pathBase}?phenotypeGroup=${encodeURIComponent(phenotypeGroup)}` : pathBase;
    const request = new Endpoints.ListGenomeAnalysisResultsRequest(genomeAnalysisId, phenotypeGroup);
    const response = await this.makeRequest(method, path, request, Endpoints.ListGenomeAnalysisResultsResponse, this.getHeaders());
    return response.genomeAnalysisResults;
  };

  public getGenomeAnalysisResult = async (genomeAnalysisId: string, genomeAnalysisResultId: string): Promise<Resources.GenomeAnalysisResult> => {
    const method = RestMethod.GET;
    const path = `v1/genome-analyses/${genomeAnalysisId}/results/${genomeAnalysisResultId}`;
    const request = new Endpoints.GetGenomeAnalysisResultRequest(genomeAnalysisId, genomeAnalysisResultId);
    const response = await this.makeRequest(method, path, request, Endpoints.GetGenomeAnalysisResultResponse, this.getHeaders());
    return response.genomeAnalysisResult;
  };

  public getExampleAnalysisId = async (): Promise<string> => {
    const method = RestMethod.GET;
    const path = 'v1/example-analysis';
    const request = new Endpoints.GetExampleAnalysisIdRequest();
    const response = await this.makeRequest(method, path, request, Endpoints.GetExampleAnalysisIdResponse, this.getHeaders());
    return response.genomeAnalysisId;
  };

  public uploadGenomeFile = async (genomeAnalysisId: string, file: File): Promise<Resources.GenomeAnalysis> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${this.baseUrl}/v1/genome-analyses/${genomeAnalysisId}/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }

    const data = await response.json();
    return Resources.GenomeAnalysis.fromObject(data.genomeAnalysis);
  };
}
