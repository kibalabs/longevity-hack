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
    traitCategory: str
    oddsRatio: float | None = None  # OR value showing relative risk (e.g., 1.22 means 22% increased risk)
    riskAlleleFrequency: float | None = None  # Population frequency of risk allele
    studyDescription: str | None = None  # Brief description of the study
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
    """A single SNP from a user's genome file."""

    rsid: str
    chromosome: str
    position: str
    genotype: str


class GwasAssociation(BaseModel):
    """Single GWAS association for a SNP."""

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
    """Metadata and summary statistics for a genome analysis."""

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
    """Category-level results for a genome analysis with JSONB SNP data."""

    resultId: str
    genomeAnalysisId: str
    phenotypeGroup: str
    phenotypeDescription: str
    snps: list[dict]  # List of SNP dictionaries (will be converted to/from SNP resources)
    createdDate: datetime
