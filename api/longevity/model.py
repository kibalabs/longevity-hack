from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ClinvarSubmission(BaseModel):
    accession: str
    clinicalSignificance: str
    significanceScore: int
    condition: str
    reviewStatus: str
    reviewScore: int
    lastEvaluated: str
    numberSubmitters: int


class ClinvarInfo(BaseModel):
    hasClinvar: bool
    gene: str | None = None
    maxSignificanceScore: int = 0
    maxReviewScore: int = 0
    submissionCount: int = 0
    submissions: list[ClinvarSubmission] = []


class GenomeAssociation(BaseModel):
    rsid: str
    genotype: str
    chromosome: str
    position: str
    trait: str
    pvalue: float | str | None = None
    importanceScore: float
    effectStrength: str | None = None
    riskAllele: str | None = None
    clinvarCondition: str | None = None
    clinvarSignificance: int | None = None
    manualCategory: str | None = None  # Manual expert-curated category (trait-specific)
    oddsRatio: float | None = None  # OR value showing relative risk (e.g., 1.22 means 22% increased risk)
    riskAlleleFrequency: float | None = None  # Population frequency of risk allele
    studyDescription: str | None = None  # Brief description of the study
    pubmedId: str | None = None  # PubMed ID for the research paper
    userHasRiskAllele: bool | None = None  # Whether user's genotype contains the risk allele


class SnpAnalysisResult(BaseModel):
    associations: list[GenomeAssociation]
    hasClinvar: bool = False


class GenomeAnalysisSummary(BaseModel):
    totalSnps: int
    matchedSnps: int
    totalAssociations: int
    clinvarCount: int


class GenomeAnalysisResult(BaseModel):
    summary: GenomeAnalysisSummary
    associations: list[GenomeAssociation]


class SnpGwas(BaseModel):
    snpGwasId: int
    rsid: str
    trait: str
    traitCategory: str | None = None
    pvalue: str | None = None
    pvalueMlog: float | None = None
    effectAllele: str | None = None
    effectType: str | None = None
    orOrBeta: str | None = None
    riskAlleleFrequency: str | None = None
    studyDescription: str | None = None
    pubmedId: str | None = None
    chromosome: str | None = None
    position: str | None = None
    mappedGene: str | None = None


class SnpClinvar(BaseModel):
    snpClinvarId: int
    rsid: str
    gene: str | None = None
    accession: str | None = None
    clinicalSignificance: str | None = None
    condition: str | None = None
    reviewStatus: str | None = None
    lastEvaluated: str | None = None
    numberSubmitters: int | None = None


class UserSnp(BaseModel):
    rsid: str
    chromosome: str
    position: str
    genotype: str


class GwasAssociation(BaseModel):
    trait: str
    traitCategory: str | None = None
    pvalue: str | None = None
    pvalueMlog: float | None = None
    effectAllele: str | None = None
    effectType: str | None = None
    orOrBeta: str | None = None
    riskAlleleFrequency: str | None = None
    studyDescription: str | None = None
    pubmedId: str | None = None
    chromosome: str | None = None
    position: str | None = None
    mappedGene: str | None = None


class GenomeAnalysis(BaseModel):
    genomeAnalysisId: str
    userId: str
    fileName: str
    status: str  # 'parsing', 'building_baseline', 'completed', 'error'
    totalSnps: int | None = None
    matchedSnps: int | None = None
    totalAssociations: int | None = None
    clinvarCount: int | None = None
    createdDate: datetime
    updatedDate: datetime


class GenomeAnalysisCategoryResult(BaseModel):
    resultId: str
    genomeAnalysisId: str
    category: str
    categoryDescription: str | None = None
    createdDate: datetime
    updatedDate: datetime


class GenomeAnalysisSnp(BaseModel):
    snpResultId: str
    createdDate: datetime
    updatedDate: datetime
    resultId: str
    genomeAnalysisId: str
    rsid: str
    genotype: str
    chromosome: str
    position: int
    trait: str
    importanceScore: float
    pValue: str
    riskAllele: str
    oddsRatio: float | None = None
    riskAlleleFrequency: float | None = None
    userHasRiskAllele: bool
    clinvarCondition: str | None = None
    clinvarSignificance: int | None = None
    studyDescription: str | None = None
    pubmedId: str | None = None
    annotation: str


class PubmedPaper(BaseModel):
    pubmedId: str
    createdDate: datetime
    updatedDate: datetime
    title: str
    abstract: str
    fullText: str
    authors: str
    journal: str
    year: str
    fetchedDate: datetime


class CategoryAnalysisCached(BaseModel):
    analysisId: str
    createdDate: datetime
    updatedDate: datetime
    genomeAnalysisId: str
    resultId: str
    category: str
    categoryDescription: str | None = None
    analysis: str
    papersUsed: list[dict[str, str | None]]  # JSON list of paper references
    snpsAnalyzed: int
