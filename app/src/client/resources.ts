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

export class SNP {
  public constructor(
    readonly rsid: string,
    readonly genotype: string,
    readonly chromosome: string,
    readonly position: number,
    readonly annotation: string,
    readonly confidence: string,
    readonly sources: string[],
  ) { }

  public static fromObject = (obj: RawObject): SNP => {
    return new SNP(
      String(obj.rsid),
      String(obj.genotype),
      String(obj.chromosome),
      Number(obj.position),
      String(obj.annotation),
      String(obj.confidence),
      (obj.sources as string[]) || [],
    );
  };
}

export class GenomeAnalysisResult {
  public constructor(
    readonly genomeAnalysisResultId: string,
    readonly genomeAnalysisId: string,
    readonly phenotypeGroup: string,
    readonly phenotypeDescription: string,
    readonly snps: SNP[],
  ) { }

  public static fromObject = (obj: RawObject): GenomeAnalysisResult => {
    return new GenomeAnalysisResult(
      String(obj.genomeAnalysisResultId),
      String(obj.genomeAnalysisId),
      String(obj.phenotypeGroup),
      String(obj.phenotypeDescription),
      ((obj.snps || []) as RawObject[]).map(SNP.fromObject),
    );
  };
}

export class GenomeAnalysis {
  public readonly genomeAnalysisId: string;

  public readonly fileName: string;

  public readonly fileType: string;

  public readonly status: string;

  public readonly createdDate: string;

  public constructor(
    genomeAnalysisId: string,
    fileName: string,
    fileType: string,
    status: string,
    createdDate: string,
  ) {
    this.genomeAnalysisId = genomeAnalysisId;
    this.fileName = fileName;
    this.fileType = fileType;
    this.status = status;
    this.createdDate = createdDate;
  }

  public static fromObject = (obj: RawObject): GenomeAnalysis => {
    return new GenomeAnalysis(
      String(obj.genomeAnalysisId),
      String(obj.fileName),
      String(obj.fileType),
      String(obj.status),
      String(obj.createdDate),
    );
  };
}
