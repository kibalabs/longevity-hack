#!/usr/bin/env python3
"""Parse Promethease HTML output to JSON format."""

import json
from pathlib import Path

import asyncclick as click
from playwright.async_api import async_playwright


async def parse_promethease_html(htmlFilePath: str) -> dict:
    """Parse Promethease HTML using browser automation."""
    htmlPath = Path(htmlFilePath).resolve()

    async with async_playwright() as p:
        print('Launching browser...')
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f'Loading HTML: {htmlPath}')
        await page.goto(f'file://{htmlPath}')

        print('Waiting for JS to decompress data...')
        await page.wait_for_timeout(3000)

        print('Extracting genotype data...')
        mygenos = await page.evaluate('() => window.model._all || []')

        await browser.close()

        print(f'Extracted {len(mygenos)} genotypes')

        genotypes = []
        for geno in mygenos:
            genotypes.append(
                {
                    'rsid': geno.get('title', ''),
                    'genotype': geno.get('genosummary', ''),
                    'magnitude': geno.get('magnitude'),
                    'repute': geno.get('repute'),
                    'summary': geno.get('genobody'),
                    'topics': geno.get('topic', []),
                    'conditions': geno.get('cond', []),
                    'genotime': geno.get('genotime'),
                }
            )

        return {'source': 'promethease', 'file': str(htmlPath.name), 'total_genotypes': len(genotypes), 'genotypes': genotypes}


@click.command()
@click.option('-i', '--input-file', 'inputFilePath', required=True, type=click.Path(exists=True))
@click.option('-o', '--output-file', 'outputFilePath', required=True, type=click.Path())
async def run(inputFilePath: str, outputFilePath: str) -> None:
    """Parse Promethease HTML and save as JSON."""
    print(f'Parsing: {inputFilePath}')

    result = await parse_promethease_html(inputFilePath)

    Path(outputFilePath).parent.mkdir(parents=True, exist_ok=True)
    with open(outputFilePath, 'w') as f:
        json.dump(result, f, indent=2)

    print(f'Saved {result["total_genotypes"]} genotypes to {outputFilePath}')


if __name__ == '__main__':
    run(_anyio_backend='asyncio')
