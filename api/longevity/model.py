from __future__ import annotations

from pydantic import BaseModel


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


class GenomeAnalysisSummary(BaseModel):
    totalSnps: int
    matchedSnps: int
    totalAssociations: int
    topCategories: list[str]
    clinvarCount: int


class GenomeAnalysisResult(BaseModel):
    summary: GenomeAnalysisSummary
    phenotypeGroups: dict[str, list[GenomeAssociation]]
    top50Associations: list[GenomeAssociation]
    clinvarVariants: list[dict]  # TODO: Create proper ClinVar model
