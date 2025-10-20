import sqlalchemy
from sqlalchemy.dialects.postgresql import JSONB

from longevity import model
from longevity.store.entity_repository import EntityRepository

metadata = sqlalchemy.MetaData()

BigInt = sqlalchemy.Numeric(precision=78, scale=0)

SnpsGwasTable = sqlalchemy.Table(
    'tbl_snps_gwas',
    metadata,
    sqlalchemy.Column(key='snpGwasId', name='id', type_=sqlalchemy.Integer, autoincrement=True, primary_key=True, nullable=False),
    sqlalchemy.Column(key='createdDate', name='created_date', type_=sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column(key='updatedDate', name='updated_date', type_=sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column(key='rsid', name='rsid', type_=sqlalchemy.Text, nullable=False, index=True),
    sqlalchemy.Column(key='trait', name='trait', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='traitCategory', name='trait_category', type_=sqlalchemy.Text, nullable=True, index=True),
    sqlalchemy.Column(key='pvalue', name='pvalue', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='pvalueMlog', name='pvalue_mlog', type_=sqlalchemy.Float, nullable=True),
    sqlalchemy.Column(key='effectAllele', name='effect_allele', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='effectType', name='effect_type', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='orOrBeta', name='or_or_beta', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='riskAlleleFrequency', name='risk_allele_frequency', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='studyDescription', name='study_description', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='pubmedId', name='pubmed_id', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='chromosome', name='chromosome', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='position', name='position', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='mappedGene', name='mapped_gene', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.UniqueConstraint('rsid', 'trait', 'pubmedId', name='tbl_snps_gwas_ux_rsid_trait_pubmed_id'),
)

sqlalchemy.Index('idx_snps_gwas_rsid_effect_allele', SnpsGwasTable.c.rsid, SnpsGwasTable.c.effectAllele)

SnpsGwasRepository = EntityRepository(table=SnpsGwasTable, modelClass=model.SnpGwas)

SnpsClinvarTable = sqlalchemy.Table(
    'tbl_snps_clinvar',
    metadata,
    sqlalchemy.Column(key='snpClinvarId', name='id', type_=sqlalchemy.Integer, autoincrement=True, primary_key=True, nullable=False),
    sqlalchemy.Column(key='createdDate', name='created_date', type_=sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column(key='updatedDate', name='updated_date', type_=sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column(key='rsid', name='rsid', type_=sqlalchemy.Text, nullable=False, index=True),
    sqlalchemy.Column(key='gene', name='gene', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='accession', name='accession', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='clinicalSignificance', name='clinical_significance', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='condition', name='condition', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='reviewStatus', name='review_status', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='lastEvaluated', name='last_evaluated', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='numberSubmitters', name='number_submitters', type_=sqlalchemy.Integer, nullable=True),
    sqlalchemy.UniqueConstraint('rsid', 'accession', name='tbl_snps_clinvar_ux_rsid_accession'),
)

SnpsClinvarRepository = EntityRepository(table=SnpsClinvarTable, modelClass=model.SnpClinvar)

GenomeAnalysesTable = sqlalchemy.Table(
    'tbl_genome_analyses',
    metadata,
    sqlalchemy.Column(key='genomeAnalysisId', name='genome_analysis_id', type_=sqlalchemy.Text, primary_key=True, nullable=False),
    sqlalchemy.Column(key='userId', name='user_id', type_=sqlalchemy.Text, nullable=False, index=True),
    sqlalchemy.Column(key='fileName', name='file_name', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='status', name='status', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='totalSnps', name='total_snps', type_=sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column(key='matchedSnps', name='matched_snps', type_=sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column(key='totalAssociations', name='total_associations', type_=sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column(key='clinvarCount', name='clinvar_count', type_=sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column(key='createdDate', name='created_date', type_=sqlalchemy.DateTime, nullable=False, index=True),
    sqlalchemy.Column(key='updatedDate', name='updated_date', type_=sqlalchemy.DateTime, nullable=False),
)

sqlalchemy.Index('idx_genome_analyses_created_date_desc', GenomeAnalysesTable.c.createdDate.desc())

GenomeAnalysesRepository = EntityRepository(table=GenomeAnalysesTable, modelClass=model.GenomeAnalysis)

GenomeAnalysisResultsTable = sqlalchemy.Table(
    'tbl_genome_analysis_results',
    metadata,
    sqlalchemy.Column(key='resultId', name='result_id', type_=sqlalchemy.Text, primary_key=True, nullable=False),
    sqlalchemy.Column(key='genomeAnalysisId', name='genome_analysis_id', type_=sqlalchemy.Text, nullable=False, index=True),
    sqlalchemy.Column(key='category', name='category', type_=sqlalchemy.Text, nullable=False, index=True),
    sqlalchemy.Column(key='categoryDescription', name='category_description', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='createdDate', name='created_date', type_=sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column(key='updatedDate', name='updated_date', type_=sqlalchemy.DateTime, nullable=False),
)

GenomeAnalysisResultsRepository = EntityRepository(table=GenomeAnalysisResultsTable, modelClass=model.GenomeAnalysisCategoryResult)

GenomeAnalysisSnpsTable = sqlalchemy.Table(
    'tbl_genome_analysis_snps',
    metadata,
    sqlalchemy.Column(key='snpResultId', name='snp_result_id', type_=sqlalchemy.Text, primary_key=True, nullable=False),
    sqlalchemy.Column(key='createdDate', name='created_date', type_=sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column(key='updatedDate', name='updated_date', type_=sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column(key='resultId', name='result_id', type_=sqlalchemy.Text, nullable=False, index=True),
    sqlalchemy.Column(key='genomeAnalysisId', name='genome_analysis_id', type_=sqlalchemy.Text, nullable=False, index=True),
    sqlalchemy.Column(key='rsid', name='rsid', type_=sqlalchemy.Text, nullable=False, index=True),
    sqlalchemy.Column(key='genotype', name='genotype', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='chromosome', name='chromosome', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='position', name='position', type_=sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column(key='trait', name='trait', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='importanceScore', name='importance_score', type_=sqlalchemy.Float, nullable=False, index=True),
    sqlalchemy.Column(key='pValue', name='p_value', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='riskAllele', name='risk_allele', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='oddsRatio', name='odds_ratio', type_=sqlalchemy.Float, nullable=True),
    sqlalchemy.Column(key='riskAlleleFrequency', name='risk_allele_frequency', type_=sqlalchemy.Float, nullable=True),
    sqlalchemy.Column(key='userHasRiskAllele', name='user_has_risk_allele', type_=sqlalchemy.Boolean, nullable=False),
    sqlalchemy.Column(key='clinvarCondition', name='clinvar_condition', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='clinvarSignificance', name='clinvar_significance', type_=sqlalchemy.Integer, nullable=True),
    sqlalchemy.Column(key='studyDescription', name='study_description', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='pubmedId', name='pubmed_id', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='annotation', name='annotation', type_=sqlalchemy.Text, nullable=False),
)

sqlalchemy.Index('idx_genome_analysis_snps_result_importance', GenomeAnalysisSnpsTable.c.resultId, GenomeAnalysisSnpsTable.c.importanceScore.desc())
sqlalchemy.Index('idx_genome_analysis_snps_analysis_category', GenomeAnalysisSnpsTable.c.genomeAnalysisId, GenomeAnalysisSnpsTable.c.resultId)

GenomeAnalysisSnpsRepository = EntityRepository(table=GenomeAnalysisSnpsTable, modelClass=model.GenomeAnalysisSnp)

PubmedPapersTable = sqlalchemy.Table(
    'tbl_pubmed_papers',
    metadata,
    sqlalchemy.Column(key='pubmedId', name='pubmed_id', type_=sqlalchemy.Text, primary_key=True, nullable=False),
    sqlalchemy.Column(key='createdDate', name='created_date', type_=sqlalchemy.DateTime, nullable=False, index=True),
    sqlalchemy.Column(key='updatedDate', name='updated_date', type_=sqlalchemy.DateTime, nullable=False, index=True),
    sqlalchemy.Column(key='title', name='title', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='abstract', name='abstract', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='fullText', name='full_text', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='authors', name='authors', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='journal', name='journal', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='year', name='year', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='fetchedDate', name='fetched_date', type_=sqlalchemy.DateTime, nullable=False, index=True),
)

PubmedPapersRepository = EntityRepository(table=PubmedPapersTable, modelClass=model.PubmedPaper)

CategoryAnalysesTable = sqlalchemy.Table(
    'tbl_category_analyses',
    metadata,
    sqlalchemy.Column(key='analysisId', name='analysis_id', type_=sqlalchemy.Text, primary_key=True, nullable=False),
    sqlalchemy.Column(key='createdDate', name='created_date', type_=sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column(key='updatedDate', name='updated_date', type_=sqlalchemy.DateTime, nullable=False),
    sqlalchemy.Column(key='genomeAnalysisId', name='genome_analysis_id', type_=sqlalchemy.Text, nullable=False, index=True),
    sqlalchemy.Column(key='resultId', name='result_id', type_=sqlalchemy.Text, nullable=False, index=True),
    sqlalchemy.Column(key='category', name='category', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='categoryDescription', name='category_description', type_=sqlalchemy.Text, nullable=True),
    sqlalchemy.Column(key='analysis', name='analysis', type_=sqlalchemy.Text, nullable=False),
    sqlalchemy.Column(key='papersUsed', name='papers_used', type_=JSONB, nullable=False),
    sqlalchemy.Column(key='snpsAnalyzed', name='snps_analyzed', type_=sqlalchemy.Integer, nullable=False),
)

sqlalchemy.Index('idx_category_analyses_genome_result', CategoryAnalysesTable.c.genomeAnalysisId, CategoryAnalysesTable.c.resultId)

CategoryAnalysesRepository = EntityRepository(table=CategoryAnalysesTable, modelClass=model.CategoryAnalysisCached)
