#!/usr/bin/env python3
"""
CLI wrapper for genome analysis.

This script provides a command-line interface to the GenomeAnalyzer class.
All core logic is in longevity.genome_analyzer.
"""

from collections import Counter
from pathlib import Path

import asyncclick as click
from core.util import file_util

import _path_fix  # noqa: F401
from longevity.create_app_manager import create_database
from longevity.genome_analyzer import GenomeAnalyzer


@click.command()
@click.option('-i', '--input', 'input_file', required=True, help='Input genome file path')
@click.option('-o', '--output', 'output_file', required=True, help='Output JSON file path')
@click.option('-b', '--batch-size', 'batch_size', type=int, default=10000, help='Batch size for processing SNPs (default: 10000)')
async def run(input_file: str, output_file: str, batch_size: int):
    database = await create_database()

    async with database.create_context_connection():
        analyzer = GenomeAnalyzer(database=database, batch_size=batch_size)
        print(f'Analyzing genome file: {input_file}')
        print(f'Output will be saved to: {output_file}')
        print(f'Batch size: {batch_size}')
        genomeContent = await file_util.read_file(input_file)
        result = await analyzer.analyze_genome(genomeContent=genomeContent)
        outputPath = Path(output_file)
        outputPath.parent.mkdir(parents=True, exist_ok=True)
        await file_util.write_file(str(outputPath), result.model_dump_json(indent=2))

        print(f'\n✓ Analysis complete!')
        print(f'  Total SNPs: {result.summary.totalSnps:,}')
        print(f'  Matched SNPs: {result.summary.matchedSnps:,}')
        print(f'  Total associations: {result.summary.totalAssociations:,}')
        print(f'  ClinVar variants: {result.summary.clinvarCount:,}')

        # Print top categories
        print('\n📊 Top Manual Categories:')
        category_counts = Counter(assoc.manualCategory for assoc in result.associations if assoc.manualCategory)
        for category, count in category_counts.most_common(10):
            print(f'  - {category}: {count} associations')

        # Show highest scoring associations
        print(f'\n⭐ Top 10 Associations by Importance Score:')
        for i, assoc in enumerate(result.associations[:10], 1):
            trait = assoc.trait[:60] + '...' if len(assoc.trait) > 60 else assoc.trait
            clinvar_marker = ' 🧬' if assoc.clinvarSignificance else ''
            category = assoc.manualCategory or 'Uncategorized'
            print(f'  {i:2d}. {trait}{clinvar_marker}')
            print(f'      Score: {assoc.importanceScore:.1f} | SNP: {assoc.rsid} ({assoc.genotype}) | Category: {category}')

        # Show clinically significant variants
        clinvar_associations = [a for a in result.associations if a.clinvarSignificance and a.clinvarSignificance >= 6]
        if clinvar_associations:
            print(f'\n🧬 Clinically Significant Variants ({len(clinvar_associations)}):')
            for i, assoc in enumerate(clinvar_associations[:10], 1):
                trait = assoc.trait[:60] + '...' if len(assoc.trait) > 60 else assoc.trait
                print(f'  {i:2d}. {assoc.rsid} ({assoc.genotype}): {trait}')
                if assoc.clinvarCondition:
                    print(f'      Condition: {assoc.clinvarCondition} | Significance: {assoc.clinvarSignificance}/10')

        print(f'\n📁 Full results saved to: {outputPath}')


if __name__ == '__main__':
    run(_anyio_backend='asyncio')  # pylint: disable=no-value-for-parameter
