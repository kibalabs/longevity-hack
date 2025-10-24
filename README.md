# GenomeAgent: AI-Powered Personal Genomics Analysis

**GenomeAgent** is a comprehensive genomics analysis platform that empowers individuals to understand their genetic predispositions for longevity-related health conditions through AI-assisted interpretation of personal genetic data.

## 🎯 Project Goals

### Primary Objectives

1. **Democratize Genetic Insights**: Make advanced genomics analysis accessible to everyone by providing free, AI-powered interpretation of personal genetic data from services like 23andMe, AncestryDNA, and others.

2. **Focus on Longevity & Health**: Analyze genetic variants associated with conditions that impact lifespan and healthspan, including:
   - Alzheimer's disease and cognitive decline
   - Cardiovascular disease and cholesterol metabolism
   - Type 2 diabetes and metabolic conditions
   - Chronic kidney disease
   - Various cancers (lung, colorectal, breast, prostate, pancreatic, melanoma)
   - Inflammatory conditions
   - Bone health and osteoarthritis
   - General longevity markers

3. **Evidence-Based Analysis**: Ground all genetic interpretations in peer-reviewed scientific research by:
   - Integrating data from the GWAS Catalog (genome-wide association studies)
   - Incorporating clinical significance data from ClinVar
   - Fetching and analyzing full-text research papers from PubMed
   - Using AI (Google Gemini) to synthesize research findings into actionable insights

4. **Privacy-First Approach**: Enable users to analyze their genetic data without uploading it to third-party services or creating accounts - analysis happens on the platform and data is processed securely.

5. **Interactive Exploration**: Provide an intuitive interface for exploring genetic results, with:
   - Risk-stratified categorization (very high, high, moderate, slight, lower risk)
   - On-demand deep dives into specific health categories
   - AI chat interface for personalized Q&A about genetic findings
   - Research paper citations for all findings

## 🏗️ Technical Architecture

### System Overview

GenomeAgent is built as a modern web application with a Python backend API and React frontend, designed for scalability and performance.

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend (React)                     │
│  - File upload interface                                     │
│  - Results visualization with risk stratification            │
│  - Interactive category exploration                          │
│  - AI chat interface                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (Python/FastAPI)              │
│  - RESTful endpoints for analysis workflow                   │
│  - File upload and format detection                          │
│  - Genome analysis orchestration                             │
│  - Paginated results delivery                                │
└─────────────────────────────────────────────────────────────┘
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│   Message Queue (SQS)   │   │   PostgreSQL Database   │
│  - Async analysis jobs   │   │  - GWAS associations    │
│  - Background processing │   │  - ClinVar data         │
└─────────────────────────┘   │  - User analyses        │
                              │  - Cached AI insights   │
                              └─────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Worker Process                            │
│  - Genome parsing & analysis                                 │
│  - Database querying (GWAS + ClinVar)                        │
│  - Risk scoring algorithm                                    │
│  - Category classification                                   │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 External Services                            │
│  - PubMed/PubTator3 API (research papers)                   │
│  - Google Gemini AI (analysis generation)                   │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

#### Backend (`/api`)
- **Framework**: Python 3.12+ with FastAPI/Starlette
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Queue**: AWS SQS for async job processing
- **AI/ML**:
  - Google Gemini API for natural language analysis
  - Sentence transformers for trait embeddings (categorization)
- **Data Sources**:
  - GWAS Catalog (genome-wide association studies)
  - ClinVar (clinical variant interpretations)
  - PubMed/PubTator3 (research paper full texts)
  - SNPedia (community-curated SNP annotations)

#### Frontend (`/app`)
- **Framework**: React 19 with TypeScript
- **UI Library**: Custom component library (@kibalabs/ui-react)
- **State Management**: TanStack Query for server state
- **Styling**: Styled Components with custom theming
- **Charts**: Recharts for data visualization

#### Infrastructure (`/infra`)
- **IaC**: Terraform for AWS resource management
- **Deployment**: Containerized with Docker
- **Database Migrations**: Alembic for schema versioning

### Core Components

#### 1. Genome Analyzer (`genome_analyzer.py`)
The heart of the analysis engine that:
- Parses raw genome files (23andMe, AncestryDNA formats)
- Validates genetic data quality
- Performs batch querying against GWAS and ClinVar databases
- Calculates importance scores based on:
  - P-value significance (-log10 transformation)
  - Clinical significance (ClinVar pathogenicity)
  - Population frequency of risk alleles
  - Odds ratios for disease risk
- Classifies variants into risk levels (very_high → lower)
- Maps variants to expert-curated health categories

**Key Algorithm**:
- Filters user's genome to ~700 manually curated SNPs linked to longevity conditions
- Uses composite database index (rsid + effect_allele) for high-performance matching
- Processes in batches of 10,000 SNPs for scalability

#### 2. Category Analyzer (`category_analyzer.py`)
AI-powered insight generation that:
- Extracts PubMed IDs from genetic associations
- Fetches full-text research papers via PubTator3 API
- Constructs context with user's variants + research
- Generates plain-text analysis via Gemini AI
- Caches results to reduce API costs

#### 3. Manual Categorization System (`manual_categories.py`)
Expert-curated mapping of (rsid, trait) tuples to health categories to handle:
- Pleiotropic SNPs (one variant → multiple conditions)
- Trait-specific categorization
- Focus on longevity-relevant conditions

Categories include:
- Alzheimer, Parkinson (neurodegeneration)
- Cardiological (heart disease, cholesterol, stroke)
- T2D (Type 2 diabetes)
- CKD (chronic kidney disease)
- AF (atrial fibrillation)
- Various cancers
- Longevity markers

#### 4. Database Schema
**Reference Data (populated once):**
- `tbl_snps_gwas`: GWAS Catalog associations (~2M+ rows)
- `tbl_snps_clinvar`: ClinVar clinical annotations (~500K+ rows)
- `tbl_pubmed_papers`: Cached research papers

**User Data:**
- `tbl_genome_analyses`: Analysis sessions (UUID primary key)
- `tbl_genome_analysis_results`: Category groupings per analysis
- `tbl_genome_analysis_snps`: Individual variant results with annotations
- `tbl_category_analyses`: Cached AI-generated insights

**Optimizations:**
- Composite index on (rsid, effect_allele) for fast variant matching
- Denormalized importance scores for quick sorting
- JSONB storage for flexible paper metadata

### API Endpoints

**Core Workflow:**
```
POST /v1/genome-analyses
  → Create analysis (returns ID)

POST /v1/genome-analyses/{id}/upload
  → Upload genome file (queues async processing)

GET /v1/genome-analyses/{id}
  → Poll analysis status

GET /v1/genome-analyses/{id}/overview
  → Get all categories with risk summaries

GET /v1/genome-analyses/{id}/results/{categoryId}/snps
  → Paginated SNPs for a category (offset/limit)

POST /v1/genome-analyses/{id}/results/{categoryId}/analyze
  → Generate AI analysis for category

POST /v1/genome-analyses/{id}/results/{categoryId}/chat
  → Chat with AI about category
```

### Data Flow

**Analysis Pipeline:**

1. **Upload**: User uploads genome file (23andMe .txt format)
2. **Queue**: File stored, job queued to SQS
3. **Parse**: Worker detects format, parses ~700K SNPs
4. **Filter**: Narrow to ~700 curated longevity-related SNPs
5. **Match**: Batch query against GWAS + ClinVar databases
6. **Score**: Calculate importance scores and risk levels
7. **Categorize**: Group by health conditions
8. **Store**: Save results to PostgreSQL
9. **Notify**: Update status to "completed"

**Category Analysis Pipeline:**

1. User requests analysis for category (e.g., "Alzheimer")
2. Backend fetches top SNPs for category
3. Extract PubMed IDs from associations
4. Fetch full-text papers from PubMed (cached)
5. Construct prompt with variants + research
6. Generate analysis via Gemini AI
7. Cache result for future requests
8. Return analysis with paper citations

### Performance Optimizations

- **Batch Processing**: Process 10K SNPs at a time to balance memory/speed
- **Database Indexing**: Composite indices on (rsid, effect_allele) for O(1) lookups
- **Lazy Loading**: Frontend loads category SNPs on-demand (paginated)
- **Caching**: AI analyses cached to avoid redundant API calls
- **Query Optimization**: Use temporary tables for large IN queries
- **Rate Limiting**: Respect PubMed API limits (3 req/sec)

### Security & Privacy

- **No Authentication Required**: Users can analyze without creating accounts
- **Ephemeral Data**: Analysis results not tied to user identities
- **Local Processing**: Genetic data processed server-side, not shared with third parties
- **CORS Protection**: API restricted to authorized frontend domains
- **Input Validation**: File format detection before processing

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- PostgreSQL 14+
- AWS account (for SQS queue)
- Google Gemini API key

### Backend Setup

```bash
cd api

# Install dependencies
uv pip install -e .

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost/longevity"
export GEMINI_API_KEY="your-api-key"
export AWS_REGION="us-east-1"

# Run migrations
cd alembic
./run-migrations.sh

# Populate SNP databases (one-time)
python scripts/populate_snp_database.py

# Start API server
make run

# Start worker (separate terminal)
python worker.py
```

### Frontend Setup

```bash
cd app

# Install dependencies
npm install

# Set API URL (optional, defaults to production)
export KRT_API_URL="http://localhost:8000"

# Start dev server
npm start
```

### Database Population

The system requires reference data from GWAS Catalog and ClinVar:

```bash
# Download GWAS Catalog
wget https://www.ebi.ac.uk/gwas/api/search/downloads/full

# Process and import
python scripts/process_gwas_catalog.py
python scripts/populate_snp_database.py
```

## 📊 Data Sources

### GWAS Catalog
- **Purpose**: Genome-wide association studies
- **Size**: ~2M+ variant-trait associations
- **Update Frequency**: Quarterly
- **URL**: https://www.ebi.ac.uk/gwas/

### ClinVar
- **Purpose**: Clinical significance of variants
- **Size**: ~500K+ variant annotations
- **Update Frequency**: Monthly
- **URL**: https://www.ncbi.nlm.nih.gov/clinvar/

### PubMed/PubTator3
- **Purpose**: Full-text research papers
- **Access**: Via NCBI API
- **Rate Limit**: 3 requests/second
- **URL**: https://www.ncbi.nlm.nih.gov/research/pubtator3/

### Manual Curation
- Expert-curated list of ~700 SNPs linked to longevity conditions
- Based on literature review and clinical relevance
- Trait-specific mapping to handle pleiotropic effects

## 🔬 Analysis Methodology

### Risk Scoring Algorithm

Each variant receives an **importance score** based on:

1. **Statistical Significance**: -log10(p-value) from GWAS studies
2. **Clinical Impact**: ClinVar pathogenicity score (0-10)
3. **Effect Size**: Odds ratio for disease risk
4. **Population Frequency**: Downweight common variants (>80% frequency)

### Risk Level Classification

Variants are classified into 6 risk levels:

- **Very High**: Strong evidence + high odds ratio + user has risk allele + rare variant
- **High**: Strong evidence + moderate odds ratio + user has risk allele + rare variant
- **Moderate**: Moderate evidence OR common variant with risk allele
- **Slight**: Weak evidence with risk allele OR common variant
- **Lower**: User does NOT have risk allele
- **Unknown**: Missing data or insufficient evidence

### Category Grouping

Results are organized into health categories:
- Each category contains all relevant variants
- Categories sorted by highest risk level, then count
- Enables focused exploration of specific conditions

## 🤝 Contributing

This is a hackathon/research project. Contributions are welcome but please note:
- Not intended for clinical use
- Results should be verified with healthcare professionals
- Code is provided as-is for educational purposes

## ⚖️ Legal & Ethical Considerations

**IMPORTANT DISCLAIMERS:**

- This tool is for **research and educational purposes only**
- Results are **not medical advice** and should not be used for clinical decisions
- Always consult qualified healthcare professionals for health concerns
- Genetic predisposition ≠ destiny - lifestyle and environment matter significantly
- Privacy: While we don't store identifiable information, genetic data is inherently sensitive

## 📝 License

[Specify your license here]

## 🙏 Acknowledgments

- GWAS Catalog team at EMBL-EBI
- ClinVar database at NCBI
- PubMed and PubTator3 teams
- Google Gemini AI team
- Open source genomics community
