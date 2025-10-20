"""Service for analyzing genetic categories using AI and research papers."""

import logging
from typing import Any

from longevity.gemini_client import GeminiClient
from longevity.pubmed_client import PubMedClient


class CategoryAnalyzer:
    """Orchestrates category analysis using PubMed and Gemini AI."""

    def __init__(self, pubmed_client: PubMedClient, gemini_client: GeminiClient) -> None:
        """Initialize the analyzer.

        Args:
            pubmed_client: Client for fetching research papers
            gemini_client: Client for AI analysis
        """
        self.pubmed_client = pubmed_client
        self.gemini_client = gemini_client

    async def analyze_category(
        self,
        category: str,
        category_description: str,
        snps: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Analyze a category of genetic variants.

        Args:
            category: Category code (e.g., "T2D", "CKD")
            category_description: Human-readable category description
            snps: List of SNP data dictionaries containing rsid, genotype, trait, etc.

        Returns:
            Dictionary containing:
                - analysis: Generated AI analysis text
                - papers_used: List of papers that were referenced
                - snps_analyzed: Number of SNPs analyzed
                - category: The category analyzed
        """
        try:
            # Extract unique PubMed IDs from SNPs
            pubmed_ids = self._extract_pubmed_ids(snps)

            if not pubmed_ids:
                logging.warning(f'No PubMed IDs found for category {category}')
                papers = {}
            else:
                # Fetch research papers
                logging.info(f'Fetching {len(pubmed_ids)} papers for category {category}')
                papers = await self.pubmed_client.fetch_papers(list(pubmed_ids))
                logging.info(f'Successfully fetched {len(papers)} papers')

            # Generate AI analysis
            logging.info(f'Generating AI analysis for category {category}')
            analysis_text = await self.gemini_client.analyze_category_risk(
                category=category,
                category_description=category_description,
                snps=snps,
                papers=papers,
            )

            # Build response
            papers_used = [
                {
                    'pubmedId': paper.pubmedId,
                    'title': paper.title,
                    'authors': paper.authors,
                    'journal': paper.journal,
                    'year': paper.year,
                    'abstract': paper.abstract,
                }
                for paper in papers.values()
            ]

            return {
                'analysis': analysis_text,
                'papersUsed': papers_used,
                'snpsAnalyzed': len(snps),
                'category': category,
                'categoryDescription': category_description,
            }

        except Exception as e:
            logging.exception(f'Error analyzing category {category}: {e}')
            raise

    def _extract_pubmed_ids(self, snps: list[dict[str, Any]]) -> set[str]:
        """Extract unique PubMed IDs from SNP data.

        Args:
            snps: List of SNP dictionaries

        Returns:
            Set of PubMed ID strings
        """
        pubmed_ids = set()

        for snp in snps:
            pubmed_id = snp.get('pubmedId')
            if pubmed_id and pubmed_id.strip():
                # Clean up the ID (remove any prefixes or whitespace)
                cleaned_id = pubmed_id.strip()
                if cleaned_id.isdigit():  # Validate it's numeric
                    pubmed_ids.add(cleaned_id)

        return pubmed_ids
