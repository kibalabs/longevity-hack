#!/usr/bin/env python3
"""
Parse Genetic Genie HTML report and convert to JSON format.

Extracts variant information from the HTML report including:
- rsID, gene, variant name
- Genotype and zygosity
- ClinVar submissions and clinical significance
- Annotations and clinical importance
- Frequency and CADD scores
"""

from pathlib import Path
from typing import List

import asyncclick as click
from bs4 import BeautifulSoup

import _path_fix  # noqa: F401


def parse_genie_html(htmlFolderPath: str) -> List[dict]:
    htmlFile = Path(htmlFolderPath) / 'index.html'
    if not htmlFile.exists():
        raise FileNotFoundError(f'HTML file not found: {htmlFile}')
    with open(htmlFile, 'r', encoding='utf-8') as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, 'html.parser')
    variants = []
    variant_divs = soup.find_all('div', class_='variant')
    for variant_div in variant_divs:
        try:
            variant_data = {}
            ltcolumn = variant_div.find('ltcolumn')
            if ltcolumn:
                gene_elem = ltcolumn.find('span', class_='genename')
                if gene_elem:
                    gene_link = gene_elem.find('a')
                    variant_data['gene'] = gene_link.text.strip() if gene_link else gene_elem.text.strip()
                variant_name_elem = ltcolumn.find('span', class_='variantname')
                if variant_name_elem:
                    variant_data['variant_name'] = variant_name_elem.get_text(strip=True)
                rsid_elem = ltcolumn.find('span', class_='rsid')
                if rsid_elem:
                    rsid_link = rsid_elem.find('a')
                    variant_data['rsid'] = rsid_link.text.strip() if rsid_link else rsid_elem.text.strip()
                text = ltcolumn.get_text()
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                for i, line in enumerate(lines):
                    if line.startswith('Ref Allele:'):
                        variant_data['ref_allele'] = line.replace('Ref Allele:', '').strip()
                    elif line.startswith('Alt Allele:'):
                        variant_data['alt_allele'] = line.replace('Alt Allele:', '').strip()
                    elif line.startswith('Freq:'):
                        freq_text = line.replace('Freq:', '').strip()
                        freq_parts = freq_text.split('%')
                        if freq_parts:
                            try:
                                variant_data['frequency'] = float(freq_parts[0].strip())
                            except ValueError:
                                variant_data['frequency'] = None
                        maf_elem = ltcolumn.find('span', class_='maf')
                        if maf_elem:
                            variant_data['frequency_category'] = maf_elem.text.strip()
                    elif line.startswith('CADD:'):
                        cadd_text = line.replace('CADD:', '').strip()
                        try:
                            variant_data['cadd_score'] = float(cadd_text)
                        except ValueError:
                            variant_data['cadd_score'] = None
            mdcolumn = variant_div.find('mdcolumn')
            if mdcolumn:
                clinvar_submissions = []
                phenotype_list = mdcolumn.find('div', class_='phenotypelist')
                if phenotype_list:
                    phenotype_items = phenotype_list.find_all('li')
                    for item in phenotype_items:
                        submission = {}
                        label = item.find('label')
                        if label:
                            condition_text = label.get_text(strip=True)
                            submission['condition'] = condition_text.replace('ℹ', '').strip()
                        modal_div = item.find('div', class_='modal__inner')
                        if modal_div:
                            modal_text = modal_div.get_text()
                            modal_lines = [line.strip() for line in modal_text.split('\n') if line.strip()]
                            for line in modal_lines:
                                if line.startswith('Last Evaluated:'):
                                    submission['last_evaluated'] = line.replace('Last Evaluated:', '').strip()
                                elif line.startswith('Review Status:'):
                                    submission['review_status'] = line.replace('Review Status:', '').strip()
                                elif line.startswith('Clinical Significance:'):
                                    submission['clinical_significance'] = line.replace('Clinical Significance:', '').strip()
                                elif line.startswith('Number of Submitters:'):
                                    try:
                                        submission['number_submitters'] = int(line.replace('Number of Submitters:', '').strip())
                                    except ValueError:
                                        submission['number_submitters'] = None
                        clinvar_submissions.append(submission)
                if clinvar_submissions:
                    variant_data['clinvar_submissions'] = clinvar_submissions
                annotation_elem = mdcolumn.find('p', class_='annotation')
                if annotation_elem:
                    annotation_text = annotation_elem.get_text(strip=True)
                    variant_data['annotation'] = annotation_text
                clinsig_elem = mdcolumn.find('span', class_='clinsig')
                if clinsig_elem:
                    variant_data['clinical_significance'] = clinsig_elem.text.strip()
            rtcolumn = variant_div.find('rtcolumn')
            if rtcolumn:
                zygosity_elem = rtcolumn.find('span', class_='zygosity')
                if zygosity_elem:
                    variant_data['zygosity'] = zygosity_elem.get_text(strip=True)
                genotype_elem = rtcolumn.find('div', class_='genotype')
                if genotype_elem:
                    variant_data['genotype'] = genotype_elem.text.strip()
            if 'rsid' in variant_data:
                variants.append(variant_data)
        except Exception as e:
            print(f'Error parsing variant: {e}')
            continue
    return variants


def run_parse_genie_html(inputFolderPath: str, outputFilePath: str) -> None:
    print(f'Parsing Genetic Genie HTML report from: {inputFolderPath}')
    variants = parse_genie_html(inputFolderPath)
    print(f'Found {len(variants)} variants')
    output_file = Path(outputFilePath)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    import json

    with open(output_file, 'w') as f:
        json.dump({'total_variants': len(variants), 'variants': variants}, f, indent=2)
    print(f'Saved to: {output_file}')


@click.command()
@click.option('-i', '--input-folder', 'inputFolderPath', required=True, type=click.Path(exists=True))
@click.option('-o', '--output-file', 'outputFilePath', required=False, type=str, default='./.data/genie_report.json')
async def run(inputFolderPath: str, outputFilePath: str) -> None:
    run_parse_genie_html(inputFolderPath, outputFilePath)


if __name__ == '__main__':
    run(_anyio_backend='asyncio')  # pylint: disable=no-value-for-parameter
