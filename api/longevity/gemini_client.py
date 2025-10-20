"""Gemini AI client for generating category risk analysis."""

import logging
import os
import re
import time
from typing import Any

import google.generativeai as genai

from longevity import model
from longevity import constants as longevity_constants


class GeminiClient:
    """Client for interacting with Google's Gemini AI API."""

    def __init__(self, api_key: str | None = None, model_name: str = 'models/gemini-flash-latest') -> None:
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError('GEMINI_API_KEY must be provided or set in environment')

        self.model_name = model_name
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    async def generate_content(self, prompt: str, **kwargs: Any) -> str:
        """Generate content using Gemini.

        Args:
            prompt: The prompt to send to Gemini
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)

        Returns:
            Generated text response
        """
        try:
            generation_config = {
                'temperature': kwargs.get('temperature', 0.0),
                'top_p': kwargs.get('top_p', 0.95),
                'top_k': kwargs.get('top_k', 40),
                'max_output_tokens': kwargs.get('max_output_tokens', 8192),
            }

            response = self.model.generate_content(prompt, generation_config=generation_config)

            if not response.text:
                logging.error('Gemini returned empty response')
                return ''

            return response.text

        except Exception as e:
            logging.exception(f'Error generating content with Gemini: {e}')
            raise

    async def analyze_category_risk(
        self,
        category: str,
        category_description: str,
        snps: list[dict[str, Any]],
        papers: dict[str, model.PubmedPaper],
    ) -> str:
        """Generate a personalized risk analysis for a genetic category.

        Args:
            category: Category name (e.g., "Cardiological", "T2D")
            category_description: Description of the category
            snps: List of user's genetic variants in this category
            papers: Dictionary mapping PubMed ID to PubmedPaper objects

        Returns:
            Generated analysis text
        """
        # Build the prompt
        prompt = self._build_analysis_prompt(category, category_description, snps, papers)

        # Try generating plain-text output, retrying if the model emits markdown-like formatting.
        max_attempts = 3
        attempt = 0
        result = ''

        while attempt < max_attempts:
            attempt += 1
            logging.debug(f'Gemini generation attempt {attempt} for category {category}')
            result = await self.generate_content(
                prompt,
                temperature=0.0,  # deterministic, factual output
                max_output_tokens=4096,  # Allow longer responses
            )

            if not result:
                logging.warning('Empty response from Gemini on attempt %s', attempt)
                continue

            if not self._contains_markdown(result):
                # Good plain-text response
                return result.strip()

            logging.warning('Gemini output appears to contain markdown/formatting on attempt %s. Retrying...', attempt)
            # Slight pause to vary generation seed/context
            time.sleep(0.3)

        # If we reach here, the model repeatedly produced formatted output. Strip markdown as a fallback.
        logging.warning('Gemini produced formatted output after %s attempts; stripping markdown as fallback.', max_attempts)
        return self._strip_markdown(result).strip()

    def _build_analysis_prompt(
        self,
        category: str,
        category_description: str,
        snps: list[dict[str, Any]],
        papers: dict[str, model.PubmedPaper],
    ) -> str:
        """Build the prompt for category analysis.

        Args:
            category: Category name
            category_description: Category description
            snps: List of SNPs
            papers: Dictionary mapping PubMed ID to PubmedPaper objects

        Returns:
            Formatted prompt string
        """
        # Format SNP list
        snp_list = []
        for i, snp in enumerate(snps[:15], 1):  # Limit to top 15 SNPs
            risk_status = 'Has risk allele' if snp.get('userHasRiskAllele') else 'Does not have risk allele'
            snp_list.append(
                f'{i}. {snp.get("rsid")} ({snp.get("genotype")})\n'
                f'   Trait: {snp.get("trait")}\n'
                f'   {risk_status}\n'
                f'   Risk Allele: {snp.get("riskAllele", "N/A")}\n'
                f'   P-value: {snp.get("pValue", "N/A")}\n'
                f'   Odds Ratio: {snp.get("oddsRatio", "N/A")}\n'
                f'   Population Frequency: {snp.get("riskAlleleFrequency", "N/A")}'
            )

        # Format papers
        paper_list = []
        for i, paper in enumerate(list(papers.values())[:10], 1):  # Limit to 10 papers
            fullText = paper.fullText
            # Truncate very long texts
            if len(fullText) > 1000:
                fullText = fullText[:1000] + '...'

            paper_list.append(
                f'{i}. {paper.authors} ({paper.year})\n'
                f'   Title: {paper.title}\n'
                f'   Journal: {paper.journal}\n'
                f'   Full Text: {fullText}\n'
                f'   PubMed ID: {paper.pubmedId}'
            )

        # Build a concise context string and then append the editable plain-text prompt
        context_parts = [
            f"CATEGORY: {category}",
            f"DESCRIPTION: {category_description}",
            "USER'S GENETIC VARIANTS:",
            chr(10).join(snp_list),
            f"Total variants analyzed: {len(snps)}",
            "RELEVANT SCIENTIFIC RESEARCH:",
            chr(10).join(paper_list) if paper_list else 'No research papers available for these variants.',
        ]

        context = chr(10).join(context_parts)

        # Place the editable prompt constant at the top to ensure model follows the plain-text instructions
        prompt = f"{longevity_constants.AI_PLAIN_TEXT_ANALYSIS_PROMPT}\n\n{context}\n\nPlease write the analysis now in 2-4 short paragraphs."

        return prompt

    def _contains_markdown(self, text: str) -> bool:
        """Simple heuristic to detect markdown-like formatting in model output.

        Returns True if the text contains headings, horizontal rules, markdown tables, code fences, or common list markers.
        """
        if not text:
            return False

        # Headings (#, ##, ###), code fences, horizontal rules, markdown tables, bold/italic markers, bullet list markers
        patterns = [
            r'(?m)^#{1,6}\s+',
            r'(?m)^\s*[-*_]{3,}\s*$',
            r'```',
            r'\|\s*[-:]+\s*\|',  # table header separator
            r'\|',  # any table-like pipe usage
            r'\*\*',
            r'\* ',
            r'•',
            r'(?m)^\s*\d+\.\s+',
        ]

        for p in patterns:
            if re.search(p, text):
                return True

        return False

    def _strip_markdown(self, text: str) -> str:
        """Best-effort removal of common markdown constructs to produce plain paragraphs.

        This is a fallback and may change formatting; prefer regenerating the model output when possible.
        """
        if not text:
            return text

        # Remove ATX headings (e.g., ## Heading)
        text = re.sub(r'(?m)^#{1,6}\s*', '', text)

        # Remove horizontal rules
        text = re.sub(r'(?m)^\s*[-*_]{3,}\s*$', '', text)

        # Remove code fences
        text = text.replace('```', '')

        # Remove bold/italic markers
        text = text.replace('**', '').replace('__', '').replace('*', '')

        # Convert markdown tables/pipes into simple line breaks: replace pipes with ' | ' -> ' - '
        text = re.sub(r'\|', ' - ', text)

        # Convert numbered/list items at line starts into sentence fragments
        text = re.sub(r'(?m)^\s*\d+\.\s+', '', text)
        text = re.sub(r'(?m)^\s*[-+\*]\s+', '', text)

        # Collapse multiple blank lines into double newline (paragraph separators)
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Trim
        return text.strip()
