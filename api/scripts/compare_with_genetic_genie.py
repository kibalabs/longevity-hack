#!/usr/bin/env python3
"""
Compare our GWAS analysis with Genetic Genie results.

Takes the output from analyze_personal_genome.py and the parsed Genie JSON report
and compares findings for overlapping variants.
"""

import json
from pathlib import Path

import asyncclick as click

import _path_fix  # noqa: F401


def analyze_snp(rsid: str, genotype: str, gene: str, genie_findings: str, our_data: dict | None = None):
    """Analyze a specific SNP and compare with our GWAS data."""
    gwas_file = Path(f'.data/snps-gwas/{rsid}.json')

    print('=' * 120)
    print(f'{rsid} - {gene}')
    print('Genetic Genie:', genie_findings)
    print('=' * 120)
    print(f'Genotype: {genotype}')
    print()

    if our_data:
        print('OUR ANALYSIS:')
        print(f'  Importance Score: {our_data.get("importance_score", "N/A"):.2f}')
        print(f'  Priority: {our_data.get("priority_tier", "N/A")}')
        print(f'  Trait: {our_data.get("trait", "N/A")}')
        print(f'  Risk Allele: {our_data.get("risk_allele", "N/A")} ({our_data.get("risk_allele_count", 0)} copies)')
        if our_data.get('has_clinvar'):
            print(f'  ClinVar: {our_data.get("clinvar_top_condition", "N/A")}')
        print()

    if not gwas_file.exists():
        print('❌ NO GWAS DATA FOUND')
        return

    with open(gwas_file, 'r') as f:
        gwas_data = json.load(f)

    print(f'Total GWAS associations: {gwas_data["association_count"]}')
    print()

    # Process associations
    all_assocs = []
    for assoc in gwas_data['associations']:
        # Extract risk allele
        risk_allele_str = assoc.get('STRONGEST SNP-RISK ALLELE', '')
        risk_allele = None
        if '-' in risk_allele_str:
            allele = risk_allele_str.split('-')[-1]
            if allele and allele != '?':
                risk_allele = allele

        if not risk_allele:
            continue

        # Count risk alleles
        risk_count = 0
        if len(genotype) == 2:
            if genotype[0] == risk_allele:
                risk_count += 1
            if genotype[1] == risk_allele:
                risk_count += 1

        if risk_count == 0:
            continue

        # Get p-value
        try:
            p_value = float(assoc.get('P-VALUE', 1.0))
        except (ValueError, TypeError):
            p_value = 1.0

        # Get effect info
        or_value = assoc.get('OR or BETA', '')
        ci_text = assoc.get('95% CI (TEXT)', '')

        all_assocs.append(
            {
                'trait': assoc.get('DISEASE/TRAIT', 'Unknown'),
                'risk_allele': risk_allele,
                'risk_count': risk_count,
                'p_value': p_value,
                'or_beta': or_value,
                'ci_text': ci_text,
                'category': assoc.get('trait_category', 'Unknown'),
                'effect_strength': assoc.get('effect_strength', 'Unknown'),
            }
        )

    # Sort by p-value (most significant first)
    all_assocs.sort(key=lambda x: x['p_value'])

    print(f'Associations with risk alleles: {len(all_assocs)}')
    print()

    # Show top associations by significance
    print('TOP ASSOCIATIONS (by statistical significance):')
    print('-' * 120)
    for i, assoc in enumerate(all_assocs[:20], 1):
        copies_text = '2 copies (homozygous)' if assoc['risk_count'] == 2 else '1 copy (heterozygous)'
        print(f'{i}. {assoc["trait"]}')
        print(f'   Risk allele: {assoc["risk_allele"]} - {copies_text}')
        print(f'   P-value: {assoc["p_value"]:.2e} | Effect: {assoc["or_beta"]} | {assoc["ci_text"]}')
        print(f'   Category: {assoc["category"]} | Strength: {assoc["effect_strength"]}')
        print()


def run_comparison(ourAnalysisPath: str, genieReportPath: str) -> None:
    """Compare our analysis with Genie report."""
    print()
    print('*' * 120)
    print('COMPARISON: OUR GWAS ANALYSIS vs GENETIC GENIE')
    print('*' * 120)
    print()
    our_analysis_file = Path(ourAnalysisPath)
    genie_report_file = Path(genieReportPath)
    if not our_analysis_file.exists():
        print(f'❌ Our analysis file not found: {our_analysis_file}')
        return
    if not genie_report_file.exists():
        print(f'❌ Genie report file not found: {genie_report_file}')
        return
    with open(our_analysis_file, 'r') as f:
        our_data = json.load(f)
    with open(genie_report_file, 'r') as f:
        genie_data = json.load(f)
    our_associations = our_data.get('top_50_associations', [])
    genie_variants = genie_data.get('variants', [])
    print(f'Our analysis: {len(our_associations)} top associations')
    print(f'Genie report: {len(genie_variants)} variants')
    print()
    our_by_rsid = {assoc['rsid']: assoc for assoc in our_associations}
    overlapping = []
    for genie_variant in genie_variants:
        rsid = genie_variant.get('rsid')
        if rsid in our_by_rsid:
            overlapping.append(
                {
                    'rsid': rsid,
                    'gene': genie_variant.get('gene', 'Unknown'),
                    'genotype': genie_variant.get('genotype', 'Unknown'),
                    'genie_data': genie_variant,
                    'our_data': our_by_rsid[rsid],
                }
            )
    print(f'Found {len(overlapping)} overlapping variants in top 50')
    print()
    overlapping.sort(key=lambda x: x['our_data'].get('importance_score', 0), reverse=True)
    for overlap in overlapping:
        genie_annotation = overlap['genie_data'].get('annotation', 'No annotation')
        genie_clinsig = overlap['genie_data'].get('clinical_significance', 'Unknown')
        genie_findings = f'{genie_annotation[:200]}... (ClinVar: {genie_clinsig})'
        analyze_snp(rsid=overlap['rsid'], genotype=overlap['genotype'], gene=overlap['gene'], genie_findings=genie_findings, our_data=overlap['our_data'])
        print()
    print('=' * 120)
    print(f'SUMMARY: Analyzed {len(overlapping)} overlapping variants')
    print('=' * 120)


@click.command()
@click.option('-a', '--our-analysis', 'ourAnalysisPath', required=True, type=click.Path(exists=True))
@click.option('-g', '--genie-report', 'genieReportPath', required=True, type=click.Path(exists=True))
async def run(ourAnalysisPath: str, genieReportPath: str) -> None:
    run_comparison(ourAnalysisPath, genieReportPath)


if __name__ == '__main__':
    run(_anyio_backend='asyncio')  # pylint: disable=no-value-for-parameter
