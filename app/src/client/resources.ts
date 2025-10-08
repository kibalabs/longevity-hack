import { RawObject } from './endpoints';

export class HealthStatus {
  public constructor(
    readonly status: string,
    readonly timestamp: Date,
  ) { }

  public static fromObject = (obj: RawObject): HealthStatus => {
    return new HealthStatus(
      String(obj.status),
      new Date(String(obj.timestamp)),
    );
  };
}
