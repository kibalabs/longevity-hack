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
