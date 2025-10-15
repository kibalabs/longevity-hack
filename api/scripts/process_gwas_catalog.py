#!/usr/bin/env python3
"""
Process GWAS Catalog file and create JSON files for each SNP.

This script reads the GWAS catalog TSV file and groups all associations by rsid,
creating individual JSON files for each SNP in the snps-gwas directory.
It also creates an enriched TSV with calculated effect, direction, and confidence metrics.
"""

import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import _path_fix  # noqa: F401


def parse_effect_allele(strongest_snp_risk_allele: str) -> str:
    """Parse effect allele from STRONGEST SNP-RISK ALLELE (the letter after the dash)."""
    if not strongest_snp_risk_allele or '-' not in strongest_snp_risk_allele:
        return ''
    parts = strongest_snp_risk_allele.split('-')
    if len(parts) >= 2:
        return parts[-1].strip()
    return ''


def parse_or_beta(or_beta_str: str) -> float | None:
    """Parse the OR or BETA value as a float."""
    if not or_beta_str:
        return None
    try:
        # Handle scientific notation and regular floats
        return float(or_beta_str.strip())
    except (ValueError, AttributeError):
        return None


def determine_effect_type(x: float, ci_text: str = '') -> str:
    """
    Determine if value is OR or beta using CI TEXT column when available.

    The 95% CI (TEXT) column provides reliable clues:
    - Beta values: includes "unit increase", "unit decrease", "SD increase", "SD unit",
      "cm increase", "z score", "z-score", etc.
    - OR values: typically just numeric range like "[1.05-1.15]" or "NR"
    - Reciprocal OR: may include "(OR reciprocal)" or similar

    Falls back to heuristic if CI text is not available or unclear.
    """
    if ci_text:
        ci_lower = ci_text.lower()
        # Beta indicators
        beta_indicators = [
            'unit increase',
            'unit decrease',
            'sd increase',
            'sd decrease',
            'sd unit',
            'cm increase',
            'cm decrease',
            'mm increase',
            'mm decrease',
            'kg increase',
            'kg decrease',
            'z score',
            'z-score',
            'year increase',
            'year decrease',
            'mmol/l',
            'mg/dl',
            'mg/l',
        ]
        for indicator in beta_indicators:
            if indicator in ci_lower:
                return 'beta'

        # OR reciprocal indicator
        if 'reciprocal' in ci_lower:
            return 'OR_reciprocal'

    # Fallback to heuristic based on value
    if x >= 1.01:
        return 'OR'
    if -1.0 <= x <= 1.0:
        return 'beta'
    return 'OR'


def calculate_direction(x: float, effect_type: str) -> int:
    """Calculate direction sign based on effect type."""
    if effect_type == 'OR_reciprocal':
        # For reciprocal OR, flip the value first
        if x <= 0:
            return 0  # Invalid OR value
        x = 1.0 / x
        return 1 if math.log(x) > 0 else -1
    if effect_type == 'OR':
        if x <= 0:
            return 0  # Invalid OR value
        return 1 if math.log(x) > 0 else -1
    # beta
    return 1 if x > 0 else -1


def calculate_per_allele_effect(x: float, effect_type: str) -> float:
    """Calculate per-allele SD effect."""
    if effect_type == 'beta':
        return abs(x)
    if effect_type == 'OR_reciprocal':
        # For reciprocal OR, flip the value first
        if x <= 0:
            return 0  # Invalid OR value
        x = 1.0 / x
        return 0.5513 * abs(math.log(x))
    # OR
    if x <= 0:
        return 0  # Invalid OR value
    return 0.5513 * abs(math.log(x))


def calculate_effect_bucket(per_allele_effect: float) -> str:
    """Calculate effect strength bucket using homozygote-equivalent (×2 alleles)."""
    homozygote_effect = per_allele_effect * 2
    if homozygote_effect >= 0.8:
        return 'Large'
    if homozygote_effect >= 0.5:
        return 'Moderate'
    if homozygote_effect >= 0.2:
        return 'Small'
    return 'Minimal'


def parse_sample_size(sample_size_str: str) -> int:
    """Parse sample size from text, extracting the largest integer found."""
    if not sample_size_str:
        return 0
    # Find all integers in the string
    numbers = re.findall(r'\d+(?:,\d+)*', sample_size_str.replace(',', ''))
    if numbers:
        return max(int(n) for n in numbers)
    return 0


def calculate_pvalue_mlog(pvalue_mlog_str: str, pvalue_str: str) -> float:
    """Calculate -log10(p-value), using PVALUE_MLOG if available, else P-VALUE."""
    # Try PVALUE_MLOG first
    if pvalue_mlog_str:
        try:
            return float(pvalue_mlog_str.strip())
        except (ValueError, AttributeError):
            pass

    # Fall back to P-VALUE
    if pvalue_str:
        try:
            pvalue = float(pvalue_str.strip())
            if pvalue > 0:
                return -math.log10(pvalue)
        except (ValueError, AttributeError):
            pass

    return 0.0


def calculate_confidence(pvalue_mlog: float, sample_size: int, is_meta: bool = False) -> tuple[float, str]:
    """Calculate confidence score (0-1) and label."""
    # Base confidence from p-value
    conf = min(1.0, pvalue_mlog / 10.0)

    # Add sample size component
    if sample_size > 0:
        conf += 0.3 * min(1.0, math.sqrt(sample_size) / math.sqrt(500000))

    # Optional meta-analysis bonus
    if is_meta:
        conf += 0.2

    conf = min(1.0, conf)

    # Determine label
    if conf >= 0.75:
        label = 'High'
    elif conf >= 0.50:
        label = 'Medium'
    else:
        label = 'Low'

    return conf, label


def is_meta_analysis(study_str: str) -> bool:
    """Simple heuristic to detect if a study is a meta-analysis."""
    if not study_str:
        return False
    study_lower = study_str.lower()
    return 'meta-analysis' in study_lower or 'meta analysis' in study_lower


def enrich_row(row: dict, trait_stats: dict = None, trait_categories: dict = None) -> dict:
    """Add calculated columns to a row."""
    enriched = row.copy()

    # Parse effect allele
    effect_allele = parse_effect_allele(row.get('STRONGEST SNP-RISK ALLELE', ''))
    enriched['effect_allele'] = effect_allele

    # Parse OR/beta value
    or_beta = parse_or_beta(row.get('OR or BETA', ''))

    # Get CI text for better classification
    ci_text = row.get('95% CI (TEXT)', '').strip()

    # Get trait for normalization
    trait = row.get('DISEASE/TRAIT', '').strip()

    if or_beta is not None and or_beta != 0:
        # Determine effect type using CI text
        effect_type = determine_effect_type(or_beta, ci_text)

        # Store both raw effect type and normalized version
        enriched['effect_type_raw'] = effect_type
        # Normalize OR_reciprocal to OR for display but track it
        enriched['effect_type'] = 'OR' if effect_type == 'OR_reciprocal' else effect_type
        enriched['is_reciprocal_or'] = 'Yes' if effect_type == 'OR_reciprocal' else 'No'

        # Add trait-level statistics for beta values only
        if effect_type == 'beta' and trait and trait_stats and trait in trait_stats:
            stats = trait_stats[trait]
            enriched['trait_beta_mean'] = f'{stats["mean"]:.4f}'
            enriched['trait_beta_median'] = f'{stats["median"]:.4f}'
            enriched['trait_beta_stdev'] = f'{stats["stdev"]:.4f}'
            enriched['trait_beta_iqr'] = f'{stats["iqr"]:.4f}'
            enriched['trait_beta_q1'] = f'{stats["q1"]:.4f}'
            enriched['trait_beta_q3'] = f'{stats["q3"]:.4f}'
            enriched['trait_beta_count'] = str(stats['count'])
            # Calculate z-score (normalized beta)
            if stats['stdev'] > 0:
                z_score = (or_beta - stats['mean']) / stats['stdev']
                enriched['beta_z_score'] = f'{z_score:.4f}'
                enriched['beta_abs_z_score'] = f'{abs(z_score):.4f}'
            else:
                enriched['beta_z_score'] = ''
                enriched['beta_abs_z_score'] = ''
            # Calculate IQR-based normalized score
            if stats['iqr'] > 0:
                iqr_score = (or_beta - stats['median']) / stats['iqr']
                enriched['beta_iqr_score'] = f'{iqr_score:.4f}'
                enriched['beta_abs_iqr_score'] = f'{abs(iqr_score):.4f}'
            else:
                enriched['beta_iqr_score'] = ''
                enriched['beta_abs_iqr_score'] = ''
        else:
            enriched['trait_beta_mean'] = ''
            enriched['trait_beta_median'] = ''
            enriched['trait_beta_stdev'] = ''
            enriched['trait_beta_iqr'] = ''
            enriched['trait_beta_q1'] = ''
            enriched['trait_beta_q3'] = ''
            enriched['trait_beta_count'] = ''
            enriched['beta_z_score'] = ''
            enriched['beta_abs_z_score'] = ''
            enriched['beta_iqr_score'] = ''
            enriched['beta_abs_iqr_score'] = ''

        # Calculate direction using raw effect type (to handle reciprocal)
        direction = calculate_direction(or_beta, effect_type)
        if direction == 0:
            # Invalid value, skip calculations
            enriched['direction'] = ''
            enriched['per_allele_effect'] = ''
            enriched['effect_strength'] = ''
        else:
            enriched['direction'] = '+' if direction > 0 else '-'

            # Calculate per-allele effect using raw effect type
            per_allele_effect = calculate_per_allele_effect(or_beta, effect_type)
            if per_allele_effect > 0:
                enriched['per_allele_effect'] = f'{per_allele_effect:.4f}'

                # Calculate effect bucket
                effect_bucket = calculate_effect_bucket(per_allele_effect)
                enriched['effect_strength'] = effect_bucket
            else:
                enriched['per_allele_effect'] = ''
                enriched['effect_strength'] = ''
    else:
        enriched['effect_type'] = ''
        enriched['effect_type_raw'] = ''
        enriched['is_reciprocal_or'] = 'No'
        enriched['direction'] = ''
        enriched['per_allele_effect'] = ''
        enriched['effect_strength'] = ''
        enriched['trait_beta_mean'] = ''
        enriched['trait_beta_median'] = ''
        enriched['trait_beta_stdev'] = ''
        enriched['trait_beta_iqr'] = ''
        enriched['trait_beta_q1'] = ''
        enriched['trait_beta_q3'] = ''
        enriched['trait_beta_count'] = ''
        enriched['beta_z_score'] = ''
        enriched['beta_abs_z_score'] = ''
        enriched['beta_iqr_score'] = ''
        enriched['beta_abs_iqr_score'] = ''

    # Calculate p-value mlog
    pvalue_mlog = calculate_pvalue_mlog(row.get('PVALUE_MLOG', ''), row.get('P-VALUE', ''))
    enriched['pvalue_mlog_calculated'] = f'{pvalue_mlog:.2f}' if pvalue_mlog > 0 else ''

    # Parse sample sizes
    initial_n = parse_sample_size(row.get('INITIAL SAMPLE SIZE', ''))
    replication_n = parse_sample_size(row.get('REPLICATION SAMPLE SIZE', ''))
    max_n = max(initial_n, replication_n)
    enriched['max_sample_size'] = str(max_n) if max_n > 0 else ''

    # Check if meta-analysis
    is_meta = is_meta_analysis(row.get('STUDY', ''))
    enriched['is_meta_analysis'] = 'Yes' if is_meta else 'No'

    # Calculate confidence
    if pvalue_mlog > 0:
        conf_score, conf_label = calculate_confidence(pvalue_mlog, max_n, is_meta)
        enriched['confidence_score'] = f'{conf_score:.3f}'
        enriched['confidence_label'] = conf_label
    else:
        enriched['confidence_score'] = ''
        enriched['confidence_label'] = ''

    # Add trait category (for display purposes only, not used in analysis)
    if trait_categories and trait:
        enriched['trait_category'] = trait_categories.get(trait, '')
    else:
        enriched['trait_category'] = ''

    return enriched


def process_gwas_catalog() -> None:
    # Input file paths
    input_file = Path('/Users/krishan/Projects/longevity-hack/api/gwas_catalog_v1.0.2-associations_e115_r2025-09-29.tsv')
    trait_mappings_file = Path('/Users/krishan/Projects/longevity-hack/api/gwas_catalog_trait-mappings_r2025-09-29.tsv')

    # Output directory and files
    output_dir = Path('./.data/snps-gwas')
    output_dir.mkdir(exist_ok=True)
    output_tsv = Path('./.data/gwas_catalog_enriched.tsv')

    print(f'Reading GWAS catalog from: {input_file}')
    print(f'Reading trait mappings from: {trait_mappings_file}')
    print(f'Output directory: {output_dir}')
    print(f'Output TSV: {output_tsv}')

    # Load trait mappings (Disease trait -> Parent term category)
    print('\nLoading trait category mappings...')
    trait_categories = {}
    with open(trait_mappings_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            disease_trait = row.get('Disease trait', '').strip()
            parent_term = row.get('Parent term', '').strip()
            if disease_trait and parent_term:
                # Store the first mapping for each trait (some traits have multiple mappings)
                if disease_trait not in trait_categories:
                    trait_categories[disease_trait] = parent_term

    print(f'Loaded {len(trait_categories):,} trait category mappings')

    # Dictionary to store associations by rsid
    snp_associations = defaultdict(list)

    # Set to track unique traits
    unique_traits = set()

    # List to store all enriched rows for TSV output
    enriched_rows = []

    # Counters for summary statistics
    effect_type_counts = defaultdict(int)
    effect_strength_counts = defaultdict(int)
    confidence_label_counts = defaultdict(int)
    reciprocal_or_count = 0
    category_counts = defaultdict(int)

    # First pass: collect all beta values per trait for normalization
    trait_beta_values = defaultdict(list)

    # Read the TSV file (first pass to collect trait statistics)
    print('\nFirst pass: collecting trait-level beta statistics...')
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')

        for row in reader:
            trait = row.get('DISEASE/TRAIT', '').strip()
            or_beta = parse_or_beta(row.get('OR or BETA', ''))
            ci_text = row.get('95% CI (TEXT)', '').strip()

            if trait and or_beta is not None:
                effect_type = determine_effect_type(or_beta, ci_text)
                # Only collect beta values (not OR_reciprocal)
                if effect_type == 'beta':
                    trait_beta_values[trait].append(or_beta)

    # Calculate trait-level statistics
    trait_stats = {}
    for trait, beta_values in trait_beta_values.items():
        if beta_values:
            import statistics

            sorted_values = sorted(beta_values)
            n = len(sorted_values)
            q1 = statistics.median(sorted_values[: n // 2]) if n > 1 else sorted_values[0]
            q3 = statistics.median(sorted_values[(n + 1) // 2 :]) if n > 1 else sorted_values[0]
            iqr = q3 - q1

            trait_stats[trait] = {
                'mean': statistics.mean(beta_values),
                'median': statistics.median(beta_values),
                'stdev': statistics.stdev(beta_values) if len(beta_values) > 1 else 0,
                'iqr': iqr,
                'q1': q1,
                'q3': q3,
                'count': len(beta_values),
            }

    print(f'Calculated statistics for {len(trait_stats):,} traits with beta values')

    # Read the TSV file (second pass for main processing)
    print('\nSecond pass: processing and enriching rows...')
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')

        # Store fieldnames for later
        original_fieldnames = reader.fieldnames

        total_rows = 0
        skipped_rows = 0

        for row in reader:
            total_rows += 1

            # Get the rsid from the SNPS column
            rsid_field = row.get('SNPS', '').strip()

            # Skip if no rsid
            if not rsid_field or rsid_field == '':
                skipped_rows += 1
                continue

            # Enrich the row with calculated fields
            enriched_row = enrich_row(row, trait_stats, trait_categories)
            enriched_rows.append(enriched_row)

            # Track summary statistics
            if enriched_row.get('effect_type'):
                effect_type_counts[enriched_row['effect_type']] += 1
            if enriched_row.get('is_reciprocal_or') == 'Yes':
                reciprocal_or_count += 1
            if enriched_row.get('effect_strength'):
                effect_strength_counts[enriched_row['effect_strength']] += 1
            if enriched_row.get('confidence_label'):
                confidence_label_counts[enriched_row['confidence_label']] += 1
            if enriched_row.get('trait_category'):
                category_counts[enriched_row['trait_category']] += 1

            # Split by multiple delimiters (/, ;, x) to handle multiple rsids in one field
            # First replace all delimiters with a common one
            rsid_field = rsid_field.replace(';', ',').replace('/', ',').replace(' x ', ',')
            rsids = [rsid.strip() for rsid in rsid_field.split(',')]

            # Add the enriched association to each rsid
            for rsid in rsids:
                if rsid:  # Make sure it's not empty after stripping
                    snp_associations[rsid].append(enriched_row)

            # Track unique traits
            trait = row.get('DISEASE/TRAIT', '').strip()
            if trait:
                unique_traits.add(trait)

            if total_rows % 100000 == 0:
                print(f'Processed {total_rows:,} rows, found {len(snp_associations):,} unique SNPs...')

    print(f'\nTotal rows processed: {total_rows:,}')
    print(f'Rows skipped (no rsid): {skipped_rows:,}')
    print(f'Unique SNPs found: {len(snp_associations):,}')
    print(f'Unique traits found: {len(unique_traits):,}')

    # Print summary statistics
    print(f'\n--- Effect Type Distribution ---')
    for effect_type in sorted(effect_type_counts.keys()):
        count = effect_type_counts[effect_type]
        percentage = (count / total_rows) * 100
        print(f'  {effect_type}: {count:,} ({percentage:.1f}%)')

    if reciprocal_or_count > 0:
        print(f'\n  Reciprocal OR detected: {reciprocal_or_count:,} ({(reciprocal_or_count / total_rows) * 100:.1f}%)')
        print(f'  Note: Reciprocal ORs are flipped and counted as regular OR above')

    print(f'\n--- Effect Strength Distribution ---')
    strength_order = ['Large', 'Moderate', 'Small', 'Minimal']
    for strength in strength_order:
        if strength in effect_strength_counts:
            count = effect_strength_counts[strength]
            percentage = (count / total_rows) * 100
            print(f'  {strength}: {count:,} ({percentage:.1f}%)')

    print(f'\n--- Confidence Level Distribution ---')
    conf_order = ['High', 'Medium', 'Low']
    for conf_label in conf_order:
        if conf_label in confidence_label_counts:
            count = confidence_label_counts[conf_label]
            percentage = (count / total_rows) * 100
            print(f'  {conf_label}: {count:,} ({percentage:.1f}%)')

    # Print trait category distribution
    if category_counts:
        print(f'\n--- Trait Category Distribution (for display only) ---')
        # Sort by count descending
        for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_rows) * 100
            print(f'  {category}: {count:,} ({percentage:.1f}%)')

        # Count rows without category
        rows_without_category = total_rows - sum(category_counts.values())
        if rows_without_category > 0:
            percentage = (rows_without_category / total_rows) * 100
            print(f'  (No category): {rows_without_category:,} ({percentage:.1f}%)')

    # Print beta z-score statistics
    beta_z_scores = []
    beta_iqr_scores = []
    for row in enriched_rows:
        if row.get('beta_abs_z_score'):
            try:
                beta_z_scores.append(float(row['beta_abs_z_score']))
            except ValueError:
                pass
        if row.get('beta_abs_iqr_score'):
            try:
                beta_iqr_scores.append(float(row['beta_abs_iqr_score']))
            except ValueError:
                pass

    if beta_z_scores:
        import statistics

        print(f'\n--- Beta Z-Score Statistics (for beta effects only) ---')
        print(f'  Total beta effects with z-scores: {len(beta_z_scores):,}')
        print(f'  Mean absolute z-score: {statistics.mean(beta_z_scores):.4f}')
        print(f'  Median absolute z-score: {statistics.median(beta_z_scores):.4f}')
        if len(beta_z_scores) > 1:
            print(f'  Stdev absolute z-score: {statistics.stdev(beta_z_scores):.4f}')

        # Show percentiles
        sorted_z = sorted(beta_z_scores)
        print(f'  95th percentile: {sorted_z[int(len(sorted_z) * 0.95)]:.4f}')
        print(f'  99th percentile: {sorted_z[int(len(sorted_z) * 0.99)]:.4f}')

        # Count by z-score buckets
        z_buckets = {
            'Very Large (|z| >= 3)': sum(1 for z in beta_z_scores if z >= 3),
            'Large (2 <= |z| < 3)': sum(1 for z in beta_z_scores if 2 <= z < 3),
            'Moderate (1 <= |z| < 2)': sum(1 for z in beta_z_scores if 1 <= z < 2),
            'Small (|z| < 1)': sum(1 for z in beta_z_scores if z < 1),
        }
        print(f'\n  Beta Effect by Z-Score Buckets:')
        for bucket, count in z_buckets.items():
            percentage = (count / len(beta_z_scores)) * 100
            print(f'    {bucket}: {count:,} ({percentage:.1f}%)')

    if beta_iqr_scores:
        import statistics

        print(f'\n--- Beta IQR-Score Statistics (for beta effects only) ---')
        print(f'  Total beta effects with IQR-scores: {len(beta_iqr_scores):,}')
        print(f'  Mean absolute IQR-score: {statistics.mean(beta_iqr_scores):.4f}')
        print(f'  Median absolute IQR-score: {statistics.median(beta_iqr_scores):.4f}')
        if len(beta_iqr_scores) > 1:
            print(f'  Stdev absolute IQR-score: {statistics.stdev(beta_iqr_scores):.4f}')

        # Show percentiles
        sorted_iqr = sorted(beta_iqr_scores)
        print(f'  95th percentile: {sorted_iqr[int(len(sorted_iqr) * 0.95)]:.4f}')
        print(f'  99th percentile: {sorted_iqr[int(len(sorted_iqr) * 0.99)]:.4f}')

        # Count by IQR-score buckets
        iqr_buckets = {
            'Very Large (|IQR| >= 3)': sum(1 for s in beta_iqr_scores if s >= 3),
            'Large (2 <= |IQR| < 3)': sum(1 for s in beta_iqr_scores if 2 <= s < 3),
            'Moderate (1 <= |IQR| < 2)': sum(1 for s in beta_iqr_scores if 1 <= s < 2),
            'Small (|IQR| < 1)': sum(1 for s in beta_iqr_scores if s < 1),
        }
        print(f'\n  Beta Effect by IQR-Score Buckets:')
        for bucket, count in iqr_buckets.items():
            percentage = (count / len(beta_iqr_scores)) * 100
            print(f'    {bucket}: {count:,} ({percentage:.1f}%)')

    # Write enriched TSV file
    print(f'\nWriting enriched TSV file...')
    new_fieldnames = list(original_fieldnames) + [
        'effect_allele',
        'effect_type',
        'effect_type_raw',
        'is_reciprocal_or',
        'direction',
        'per_allele_effect',
        'effect_strength',
        'trait_beta_mean',
        'trait_beta_median',
        'trait_beta_stdev',
        'trait_beta_iqr',
        'trait_beta_q1',
        'trait_beta_q3',
        'trait_beta_count',
        'beta_z_score',
        'beta_abs_z_score',
        'beta_iqr_score',
        'beta_abs_iqr_score',
        'pvalue_mlog_calculated',
        'max_sample_size',
        'is_meta_analysis',
        'confidence_score',
        'confidence_label',
        'trait_category',  # User-friendly category for display (not used in analysis)
    ]

    with open(output_tsv, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(enriched_rows)

    print(f'Written enriched TSV to {output_tsv}')

    # Write JSON files for each SNP
    print(f'\nWriting JSON files...')
    files_written = 0

    for rsid, associations in snp_associations.items():
        # Use rsid directly as filename (no need to sanitize slashes since we split them)
        output_file = output_dir / f'{rsid}.json'

        # Create output structure
        output_data = {
            'rsid': rsid,
            'association_count': len(associations),
            'associations': associations,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2)

        files_written += 1

        if files_written % 10000 == 0:
            print(f'Written {files_written:,} files...')

    print(f'\nDone! Written {files_written:,} JSON files to {output_dir}/')

    # Print some statistics
    if snp_associations:
        avg_associations = sum(len(assocs) for assocs in snp_associations.values()) / len(snp_associations)

        print(f'\nStatistics:')
        print(f'  Average associations per SNP: {avg_associations:.2f}')
        # Find SNP with most associations
        most_assoc_rsid = max(snp_associations.keys(), key=lambda k: len(snp_associations[k]))
        print(f'  SNP with most associations: {most_assoc_rsid} ({len(snp_associations[most_assoc_rsid])} associations)')


if __name__ == '__main__':
    process_gwas_catalog()
