#!/usr/bin/env python3
"""
CLI wrapper for genome analysis.

This script provides a command-line interface to the GenomeAnalyzer class.
All core logic is in longevity.genome_analyzer.
"""

import json
from pathlib import Path

import asyncclick as click
from core.util import file_util

import _path_fix  # noqa: F401
from longevity.genome_analyzer import GenomeAnalyzer


@click.command()
@click.option('-i', '--input-file', 'inputFilePath', required=True, type=click.Path(exists=True))
@click.option('-o', '--output-file', 'outputFilePath', required=False, type=str, default='./.data/personal_genome_analysis.json')
async def run(inputFilePath: str, outputFilePath: str) -> None:
    """Analyze personal genome data against GWAS catalog and ClinVar."""

    gwasDir = Path('./.data/snps-gwas')
    annotationsDir = Path('./.data/snps')

    analyzer = GenomeAnalyzer(gwasDir=gwasDir, annotationsDir=annotationsDir)

    print(f'Analyzing genome file: {inputFilePath}')
    print(f'Output will be saved to: {outputFilePath}')

    # Read genome file
    genomeContent = await file_util.read_file(inputFilePath)

    # Define callbacks for reading GWAS and annotation data
    async def read_gwas_file(rsid: str):
        gwasFile = gwasDir / f'{rsid}.json'
        if not gwasFile.exists():
            return None
        content = await file_util.read_file(str(gwasFile))
        return json.loads(content)

    async def read_annotation_file(rsid: str):
        annotationFile = annotationsDir / f'{rsid}.json'
        if not annotationFile.exists():
            return None
        content = await file_util.read_file(str(annotationFile))
        return json.loads(content)

    # Run analysis
    result = await analyzer.analyze_genome(genomeContent=genomeContent, read_gwas_file=read_gwas_file, read_annotation_file=read_annotation_file)

    # Save output
    outputPath = Path(outputFilePath)
    outputPath.parent.mkdir(parents=True, exist_ok=True)
    await file_util.write_file(str(outputPath), result.model_dump_json(indent=2))

    print(f'\n✓ Analysis complete!')
    print(f'  Total SNPs: {result.summary.totalSnps:,}')
    print(f'  Matched SNPs: {result.summary.matchedSnps:,}')
    print(f'  Total associations: {result.summary.totalAssociations:,}')
    print(f'  Top categories: {", ".join(result.summary.topCategories[:5])}')
    print(f'  ClinVar variants: {result.summary.clinvarCount:,}')
    print(f'\nResults saved to: {outputPath}')


if __name__ == '__main__':
    run(_anyio_backend='asyncio')  # pylint: disable=no-value-for-parameter
