#!/usr/bin/env python3
"""Compare our genome analysis output with Promethease output."""

import click
import json
from pathlib import Path
from collections import defaultdict


def load_json(filePath: str) -> dict:
    """Load JSON file."""
    with open(filePath) as f:
        return json.load(f)


def extract_rsids_from_promethease(promData: dict) -> dict:
    """Extract individual SNP IDs from Promethease genoset summaries."""
    rsidMap = {}

    for geno in promData['genotypes']:
        summary = geno.get('summary', '')
        if not summary:
            continue

        # Look for rs#### patterns in the summary
        import re
        rsids = re.findall(r'rs\d+', summary)

        for rsid in rsids:
            if rsid not in rsidMap:
                rsidMap[rsid] = []
            rsidMap[rsid].append({
                'genoset': geno['rsid'],
                'interpretation': geno['genotype'],
                'magnitude': geno['magnitude'],
                'repute': geno['repute'],
                'conditions': geno.get('conditions', []),
                'topics': geno.get('topics', [])
            })

    return rsidMap


def extract_top_snps_from_our_analysis(ourData: dict) -> dict:
    """Extract top SNPs from our analysis."""
    snpMap = {}

    for assoc in ourData.get('top_50_associations', []):
        rsid = assoc['rsid']
        if rsid not in snpMap:
            snpMap[rsid] = []
        snpMap[rsid].append({
            'genotype': assoc['genotype'],
            'importance_score': assoc['importance_score'],
            'trait': assoc['trait'],
            'p_value': assoc.get('p_value_text', ''),
            'study': assoc.get('study', '')
        })

    return snpMap


def compare_analyses(ourData: dict, promData: dict) -> dict:
    """Compare the two analyses."""
    ourSnps = extract_top_snps_from_our_analysis(ourData)
    promSnps = extract_rsids_from_promethease(promData)

    ourRsids = set(ourSnps.keys())
    promRsids = set(promSnps.keys())

    overlap = ourRsids & promRsids
    ourUnique = ourRsids - promRsids
    promUnique = promRsids - ourRsids

    # Analyze overlapping SNPs
    overlappingDetails = []
    for rsid in sorted(overlap):
        ourInfo = ourSnps[rsid]
        promInfo = promSnps[rsid]

        overlappingDetails.append({
            'rsid': rsid,
            'our_analysis': ourInfo,
            'promethease_analysis': promInfo
        })

    # Get details for unique SNPs
    ourUniqueDetails = [
        {'rsid': rsid, 'info': ourSnps[rsid]}
        for rsid in sorted(ourUnique)[:20]  # Top 20
    ]

    promUniqueDetails = [
        {'rsid': rsid, 'info': promSnps[rsid]}
        for rsid in sorted(promUnique)[:20]  # Top 20
    ]

    # Count by magnitude/importance
    ourByImportance = defaultdict(int)
    for rsid, info in ourSnps.items():
        for assoc in info:
            score = assoc['importance_score']
            if score >= 9:
                ourByImportance['critical'] += 1
            elif score >= 7:
                ourByImportance['high'] += 1
            elif score >= 5:
                ourByImportance['medium'] += 1
            else:
                ourByImportance['low'] += 1

    promByMagnitude = defaultdict(int)
    for rsid, info in promSnps.items():
        for geno in info:
            mag = geno['magnitude'] or 0
            if mag >= 4:
                promByMagnitude['very_high'] += 1
            elif mag >= 3:
                promByMagnitude['high'] += 1
            elif mag >= 2:
                promByMagnitude['medium'] += 1
            else:
                promByMagnitude['low'] += 1

    return {
        'summary': {
            'our_total_snps': ourData.get('total_snps', 0),
            'our_matched_snps': ourData.get('matched_snps', 0),
            'our_top_associations': len(ourSnps),
            'promethease_total_genotypes': promData.get('total_genotypes', 0),
            'promethease_snps_mentioned': len(promSnps),
            'overlap_count': len(overlap),
            'our_unique_count': len(ourUnique),
            'promethease_unique_count': len(promUnique)
        },
        'scoring_distribution': {
            'our_importance_scores': dict(ourByImportance),
            'promethease_magnitude_scores': dict(promByMagnitude)
        },
        'overlapping_snps': overlappingDetails[:20],  # Top 20 overlapping
        'our_unique_snps': ourUniqueDetails,
        'promethease_unique_snps': promUniqueDetails
    }


@click.command()
@click.option('-o', '--our-analysis', 'ourAnalysisPath', required=True, type=click.Path(exists=True),
              help='Path to our analysis JSON (processed-promethease-1.json)')
@click.option('-p', '--promethease', 'prometheasePath', required=True, type=click.Path(exists=True),
              help='Path to Promethease parsed JSON (promethease-1-parsed.json)')
@click.option('-r', '--report', 'reportPath', default='promethease_comparison.json',
              help='Output comparison report path')
def run(ourAnalysisPath: str, prometheasePath: str, reportPath: str) -> None:
    """Compare our genome analysis with Promethease output."""
    print(f'Loading our analysis: {ourAnalysisPath}')
    ourData = load_json(ourAnalysisPath)

    print(f'Loading Promethease data: {prometheasePath}')
    promData = load_json(prometheasePath)

    print('Comparing analyses...')
    comparison = compare_analyses(ourData, promData)

    # Save comparison
    Path(reportPath).parent.mkdir(parents=True, exist_ok=True)
    with open(reportPath, 'w') as f:
        json.dump(comparison, f, indent=2)

    print(f'\nComparison Summary:')
    print(f"  Our analysis: {comparison['summary']['our_total_snps']:,} total SNPs")
    print(f"  Our analysis: {comparison['summary']['our_matched_snps']:,} matched SNPs")
    print(f"  Our top associations: {comparison['summary']['our_top_associations']}")
    print(f"  Promethease genotypes: {comparison['summary']['promethease_total_genotypes']:,}")
    print(f"  Promethease SNPs mentioned: {comparison['summary']['promethease_snps_mentioned']}")
    print(f"  Overlapping SNPs: {comparison['summary']['overlap_count']}")
    print(f"  Our unique SNPs: {comparison['summary']['our_unique_count']}")
    print(f"  Promethease unique SNPs: {comparison['summary']['promethease_unique_count']}")

    print(f'\nFull comparison saved to: {reportPath}')


if __name__ == '__main__':
    run()
