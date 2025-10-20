import os
from typing import Any

import google.generativeai as genai
from core import logging
from core.exceptions import KibaException
from longevity import model
from longevity import constants as longevity_constants


class GeminiClient:

    def __init__(self, api_key: str | None = None, model_name: str = 'models/gemini-flash-latest') -> None:
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError('GEMINI_API_KEY must be provided or set in environment')

        self.model_name = model_name
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    async def generate_content(self, prompt: str, **kwargs: Any) -> str:
        generation_config = {
            'temperature': kwargs.get('temperature', 0.0),
            'top_p': kwargs.get('top_p', 0.95),
            'top_k': kwargs.get('top_k', 40),
            'max_output_tokens': kwargs.get('max_output_tokens', 8192),
        }
        response = self.model.generate_content(prompt, generation_config=generation_config)
        if not response.text:
            raise KibaException('Gemini returned empty response')
        return response.text

    async def analyze_category_risk(
        self,
        category: str,
        category_description: str,
        snps: list[dict[str, Any]],
        papers: dict[str, model.PubmedPaper],
    ) -> str:
        prompt = self._build_analysis_prompt(category, category_description, snps, papers)
        result = await self.generate_content(
            prompt,
            temperature=0.0,
            max_output_tokens=4096,
        )
        return result.strip() if result else ''

    def _build_analysis_prompt(
        self,
        category: str,
        category_description: str,
        snps: list[dict[str, Any]],
        papers: dict[str, model.PubmedPaper],
    ) -> str:
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
            "\n".join(snp_list),
            f"Total variants analyzed: {len(snps)}",
            "RELEVANT SCIENTIFIC RESEARCH:",
            "\n".join(paper_list) if paper_list else 'No research papers available for these variants.',
        ]
        context = "\n".join(context_parts)
        # Place the editable prompt constant at the top to ensure model follows the plain-text instructions
        prompt = f"{longevity_constants.AI_PLAIN_TEXT_ANALYSIS_PROMPT}\n\n{context}\n\nPlease write the analysis now in 2-4 short paragraphs."
        return prompt
