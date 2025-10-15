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
    readonly trait: string | null,
    readonly importanceScore: number | null,
    readonly pValue: string | null,
    readonly effectStrength: string | null,
    readonly riskAllele: string | null,
    readonly clinvarCondition: string | null,
    readonly clinvarSignificance: number | null,
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
      obj.trait ? String(obj.trait) : null,
      obj.importanceScore ? Number(obj.importanceScore) : null,
      obj.pValue ? String(obj.pValue) : null,
      obj.effectStrength ? String(obj.effectStrength) : null,
      obj.riskAllele ? String(obj.riskAllele) : null,
      obj.clinvarCondition ? String(obj.clinvarCondition) : null,
      obj.clinvarSignificance ? Number(obj.clinvarSignificance) : null,
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

export class GenomeAnalysisSummary {
  public constructor(
    readonly totalSnps: number | null,
    readonly matchedSnps: number | null,
    readonly totalAssociations: number | null,
    readonly topCategories: string[] | null,
    readonly clinvarCount: number | null,
  ) { }

  public static fromObject = (obj: RawObject): GenomeAnalysisSummary => {
    return new GenomeAnalysisSummary(
      obj.totalSnps ? Number(obj.totalSnps) : null,
      obj.matchedSnps ? Number(obj.matchedSnps) : null,
      obj.totalAssociations ? Number(obj.totalAssociations) : null,
      obj.topCategories ? (obj.topCategories as string[]) : null,
      obj.clinvarCount ? Number(obj.clinvarCount) : null,
    );
  };
}

export class GenomeAnalysis {
  public readonly genomeAnalysisId: string;

  public readonly fileName: string;

  public readonly fileType: string;

  public readonly detectedFormat: string | null;

  public readonly status: string;

  public readonly createdDate: string;

  public readonly summary: GenomeAnalysisSummary | null;

  public constructor(
    genomeAnalysisId: string,
    fileName: string,
    fileType: string,
    detectedFormat: string | null,
    status: string,
    createdDate: string,
    summary: GenomeAnalysisSummary | null,
  ) {
    this.genomeAnalysisId = genomeAnalysisId;
    this.fileName = fileName;
    this.fileType = fileType;
    this.detectedFormat = detectedFormat;
    this.status = status;
    this.createdDate = createdDate;
    this.summary = summary;
  }

  public static fromObject = (obj: RawObject): GenomeAnalysis => {
    return new GenomeAnalysis(
      String(obj.genomeAnalysisId),
      String(obj.fileName),
      String(obj.fileType),
      obj.detectedFormat ? String(obj.detectedFormat) : null,
      String(obj.status),
      String(obj.createdDate),
      obj.summary ? GenomeAnalysisSummary.fromObject(obj.summary as RawObject) : null,
    );
  };
}
