#!/usr/bin/env python3
"""
CLI wrapper for genome analysis.

This script provides a command-line interface to the GenomeAnalyzer class.
All core logic is in longevity.genome_analyzer.
"""

import json
import shutil
import uuid
from pathlib import Path

import asyncclick as click

import _path_fix  # noqa: F401
from longevity.genome_analyzer import GenomeAnalyzer


@click.command()
@click.option('-i', '--input-file', 'inputFilePath', required=True, type=click.Path(exists=True))
@click.option('-o', '--output-file', 'outputFilePath', required=False, type=str, default='./.data/personal_genome_analysis.json')
async def run(inputFilePath: str, outputFilePath: str) -> None:
    """Analyze personal genome data against GWAS catalog and ClinVar."""

    # Create analyzer instance
    uploadsDir = Path('./.data/uploads')
    outputsDir = Path('./.data/outputs')
    gwasDir = Path('./.data/snps-gwas')
    annotationsDir = Path('./.data/snps')

    analyzer = GenomeAnalyzer(
        uploadsDir=uploadsDir,
        outputsDir=outputsDir,
        gwasDir=gwasDir,
        annotationsDir=annotationsDir
    )

    # Run analysis
    print(f'Analyzing genome file: {inputFilePath}')
    print(f'Output will be saved to: {outputFilePath}')

    # Use a temporary ID for CLI usage
    analysisId = str(uuid.uuid4())

    # Copy input file to uploads directory (analyzer expects it there)
    inputPath = Path(inputFilePath)
    uploadPath = analyzer.get_upload_path(analysisId, inputPath.name)

    shutil.copy(inputPath, uploadPath)

    # Run analysis
    result = await analyzer.analyze_genome_file(analysisId, uploadPath)

    # Move output to desired location
    outputPath = Path(outputFilePath)
    outputPath.parent.mkdir(parents=True, exist_ok=True)

    with open(outputPath, 'w') as f:
        json.dump(result, f, indent=2)

    print(f'\n✓ Analysis complete!')
    print(f'  Total SNPs: {result["summary"]["total_snps"]:,}')
    print(f'  Matched SNPs: {result["summary"]["matched_snps"]:,}')
    print(f'  Total associations: {result["summary"]["total_associations"]:,}')
    print(f'  ClinVar variants: {result["summary"]["clinvar_count"]:,}')
    print(f'\nResults saved to: {outputPath}')


if __name__ == '__main__':
    run(_anyio_backend='asyncio')  # pylint: disable=no-value-for-parameter
