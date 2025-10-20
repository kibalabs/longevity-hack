/* eslint-disable class-methods-use-this */
import { RequestData, ResponseData } from '@kibalabs/core';

import * as Resources from './resources';

export type RawObject = Record<string, unknown>;

export class HealthCheckRequest extends RequestData {
  public constructor() {
    super();
  }

  public toObject = (): RawObject => {
    return {};
  };
}

export class HealthCheckResponse extends ResponseData {
  public constructor(
    readonly healthStatus: Resources.HealthStatus,
  ) {
    super();
  }

  public static fromObject = (obj: RawObject): HealthCheckResponse => {
    return new HealthCheckResponse(
      Resources.HealthStatus.fromObject(obj.healthStatus as RawObject),
    );
  };
}

export class CreateGenomeAnalysisRequest extends RequestData {
  public constructor(
    readonly fileName: string,
    readonly fileType: string,
  ) {
    super();
  }

  public toObject = (): RawObject => {
    return {
      fileName: this.fileName,
      fileType: this.fileType,
    };
  };
}

export class CreateGenomeAnalysisResponse extends ResponseData {
  public constructor(
    readonly genomeAnalysis: Resources.GenomeAnalysis,
  ) {
    super();
  }

  public static fromObject = (obj: RawObject): CreateGenomeAnalysisResponse => {
    return new CreateGenomeAnalysisResponse(
      Resources.GenomeAnalysis.fromObject(obj.genomeAnalysis as RawObject),
    );
  };
}

export class GetGenomeAnalysisRequest extends RequestData {
  public constructor(
    readonly genomeAnalysisId: string,
  ) {
    super();
  }

  public toObject = (): RawObject => {
    return {};
  };
}

export class GetGenomeAnalysisResponse extends ResponseData {
  public constructor(
    readonly genomeAnalysis: Resources.GenomeAnalysis,
  ) {
    super();
  }

  public static fromObject = (obj: RawObject): GetGenomeAnalysisResponse => {
    return new GetGenomeAnalysisResponse(
      Resources.GenomeAnalysis.fromObject(obj.genomeAnalysis as RawObject),
    );
  };
}

export class GetGenomeAnalysisOverviewRequest extends RequestData {
  public constructor(
    readonly genomeAnalysisId: string,
  ) {
    super();
  }

  public toObject = (): RawObject => {
    return {};
  };
}

export class GetGenomeAnalysisOverviewResponse extends ResponseData {
  public constructor(
    readonly overview: Resources.GenomeAnalysisOverview,
  ) {
    super();
  }

  public static fromObject = (obj: RawObject): GetGenomeAnalysisOverviewResponse => {
    return new GetGenomeAnalysisOverviewResponse(
      Resources.GenomeAnalysisOverview.fromObject(obj.overview as RawObject),
    );
  };
}

export class ListCategorySnpsRequest extends RequestData {
  public constructor(
    readonly genomeAnalysisId: string,
    readonly genomeAnalysisResultId: string,
    readonly offset: number = 0,
    readonly limit: number = 20,
    readonly minImportanceScore: number | null = null,
  ) {
    super();
  }

  public toObject = (): RawObject => {
    return {};
  };
}

export class ListCategorySnpsResponse extends ResponseData {
  public constructor(
    readonly categorySnpsPage: Resources.CategorySnpsPage,
  ) {
    super();
  }

  public static fromObject = (obj: RawObject): ListCategorySnpsResponse => {
    return new ListCategorySnpsResponse(
      Resources.CategorySnpsPage.fromObject(obj.categorySnpsPage as RawObject),
    );
  };
}

export class GetGenomeAnalysisResultRequest extends RequestData {
  public constructor(
    readonly genomeAnalysisId: string,
    readonly genomeAnalysisResultId: string,
  ) {
    super();
  }

  public toObject = (): RawObject => {
    return {};
  };
}

export class GetGenomeAnalysisResultResponse extends ResponseData {
  public constructor(
    readonly genomeAnalysisResult: Resources.GenomeAnalysisResult,
  ) {
    super();
  }

  public static fromObject = (obj: RawObject): GetGenomeAnalysisResultResponse => {
    return new GetGenomeAnalysisResultResponse(
      Resources.GenomeAnalysisResult.fromObject(obj.genomeAnalysisResult as RawObject),
    );
  };
}

export class GetExampleAnalysisIdRequest extends RequestData {
  public constructor() {
    super();
  }

  public toObject = (): RawObject => {
    return {};
  };
}

export class GetExampleAnalysisIdResponse extends ResponseData {
  public constructor(
    readonly genomeAnalysisId: string,
  ) {
    super();
  }

  public static fromObject = (obj: RawObject): GetExampleAnalysisIdResponse => {
    return new GetExampleAnalysisIdResponse(
      String(obj.genomeAnalysisId),
    );
  };
}
