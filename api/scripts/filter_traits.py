#!/usr/bin/env python3
"""Filter genome analysis results by trait term and output RSIDs with importance scores."""

import json
from pathlib import Path

import click


def load_json(filePath: str) -> dict:
    """Load JSON file."""
    with open(filePath) as f:
        return json.load(f)


def filter_by_trait(data: dict, traitTerm: str) -> list:
    """Filter associations by trait term and return RSID/score pairs."""
    results = []

    # Handle new format with phenotypeGroups
    if 'phenotypeGroups' in data:
        for category, associations in data['phenotypeGroups'].items():
            for assoc in associations:
                trait = assoc.get('trait', '')
                if traitTerm.lower() in trait.lower():
                    results.append(
                        {
                            'rsid': assoc['rsid'],
                            'importanceScore': assoc['importanceScore'],
                            'trait': trait,
                            'genotype': assoc.get('genotype', ''),
                            'pvalue': assoc.get('pvalue', ''),
                            'category': category,
                            'clinvarCondition': assoc.get('clinvarCondition'),
                            'clinvarSignificance': assoc.get('clinvarSignificance'),
                        }
                    )

    # Handle old format with top_50_associations
    elif 'top_50_associations' in data:
        for assoc in data['top_50_associations']:
            trait = assoc.get('trait', '')
            if traitTerm.lower() in trait.lower():
                results.append(
                    {
                        'rsid': assoc['rsid'],
                        'importanceScore': assoc.get('importance_score', 0),
                        'trait': trait,
                        'genotype': assoc.get('genotype', ''),
                        'pvalue': assoc.get('p_value_text', ''),
                    }
                )

    return results


@click.command()
@click.option('-i', '--input', 'inputPath', required=True, type=click.Path(exists=True), help='Path to genome analysis JSON file')
@click.option('-t', '--trait', 'traitTerm', required=True, help='Trait term to search for (case-insensitive, partial match)')
@click.option('-o', '--output', 'outputPath', default=None, help='Optional: Save results to JSON file')
@click.option('--csv', 'csvOutput', is_flag=True, help='Output in CSV format instead of JSON')
def run(inputPath: str, traitTerm: str, outputPath: str, csvOutput: bool) -> None:
    """Filter genome analysis by trait term and output RSIDs with importance scores."""

    print(f'Loading genome analysis: {inputPath}')
    data = load_json(inputPath)

    print(f'Filtering by trait term: "{traitTerm}"')
    results = filter_by_trait(data, traitTerm)

    print(f'\nFound {len(results)} associations matching "{traitTerm}":')
    print()

    if csvOutput:
        # CSV output
        print('rsid,importanceScore,trait,genotype,pvalue,category,clinvarCondition,clinvarSignificance')
        for result in results:
            category = result.get('category', '')
            clinvarCondition = result.get('clinvarCondition', '')
            clinvarSignificance = result.get('clinvarSignificance', '')

            print(f'{result["rsid"]},{result["importanceScore"]},"{result["trait"]}",{result["genotype"]},{result["pvalue"]},{category},"{clinvarCondition}",{clinvarSignificance}')
    else:
        # Pretty print to console
        for i, result in enumerate(results, 1):
            print(f'{i}. {result["rsid"]} (score: {result["importanceScore"]})')
            print(f'   Trait: {result["trait"]}')
            print(f'   Genotype: {result["genotype"]}')
            print(f'   P-value: {result["pvalue"]}')
            if 'category' in result:
                print(f'   Category: {result["category"]}')
            if result.get('clinvarCondition'):
                print(f'   ClinVar: {result["clinvarCondition"]} (significance: {result["clinvarSignificance"]})')
            print()

    # Save to file if requested
    if outputPath:
        Path(outputPath).parent.mkdir(parents=True, exist_ok=True)

        if csvOutput or outputPath.endswith('.csv'):
            # Save as CSV
            with open(outputPath, 'w') as f:
                f.write('rsid,importanceScore,trait,genotype,pvalue,category,clinvarCondition,clinvarSignificance\n')
                for result in results:
                    category = result.get('category', '')
                    clinvarCondition = result.get('clinvarCondition', '')
                    clinvarSignificance = result.get('clinvarSignificance', '')

                    f.write(f'{result["rsid"]},{result["importanceScore"]},"{result["trait"]}",{result["genotype"]},{result["pvalue"]},{category},"{clinvarCondition}",{clinvarSignificance}\n')
        else:
            # Save as JSON
            with open(outputPath, 'w') as f:
                json.dump({'traitTerm': traitTerm, 'totalMatches': len(results), 'results': results}, f, indent=2)

        print(f'Results saved to: {outputPath}')

    # Summary statistics
    uniqueRsids = set(r['rsid'] for r in results)
    avgScore = sum(r['importanceScore'] for r in results) / len(results) if results else 0

    print(f'\nSummary:')
    print(f'  Total associations: {len(results)}')
    print(f'  Unique RSIDs: {len(uniqueRsids)}')
    print(f'  Average importance score: {avgScore:.2f}')

    if results:
        maxScore = max(r['importanceScore'] for r in results)
        minScore = min(r['importanceScore'] for r in results)
        print(f'  Score range: {minScore:.1f} - {maxScore:.1f}')


if __name__ == '__main__':
    run()
