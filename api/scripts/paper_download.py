"""Test script to fetch and display PubMed paper data."""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncclick as click
from longevity.create_app_manager import create_database
from core.requester import Requester
from longevity.pubmed_client import PubMedClient


@click.command()
@click.argument('pubmed_id')
@click.option('--raw', is_flag=True, help='Show raw API response')
async def test_paper(pubmed_id: str, raw: bool):
    """Fetch and display paper data from PubMed.

    Always refreshes data by deleting from cache first.

    Args:
        pubmed_id: PubMed ID to fetch
        raw: If True, show raw API response instead of parsed data
    """
    database = await create_database()
    requester = Requester()
    client = PubMedClient(database=database, requester=requester)

    if raw:
        print(f'Fetching raw API response for {pubmed_id}...')
        params = {'pmids': pubmed_id, 'full': 'true'}
        response = await requester.get(url='https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson', dataDict=params, timeout=30)
        data = response.json()
        print(json.dumps(data, indent=2))
        await database.disconnect()
        return

    # Always refresh - delete from cache first
    print(f'Deleting {pubmed_id} from cache to force refresh...')
    from longevity.store import schema
    async with database.create_transaction() as connection:
        await connection.execute(
            schema.PubmedPapersTable.delete().where(
                schema.PubmedPapersTable.c.pubmedId == pubmed_id
            )
        )
    print('Deleted from cache')
    print()

    print(f'Fetching paper {pubmed_id}...')
    papers = await client.fetch_papers([pubmed_id])

    if pubmed_id not in papers:
        print(f'ERROR: Paper {pubmed_id} not found!')
    else:
        paper = papers[pubmed_id]
        print('=' * 80)
        print(f'PubMed ID: {paper.pubmedId}')
        print(f'Title: {paper.title}')
        print(f'Authors: {paper.authors}')
        print(f'Journal: {paper.journal}')
        print(f'Year: {paper.year}')
        print(f'Abstract Length: {len(paper.abstract)} characters')
        print(f'Full Text Length: {len(paper.fullText)} characters')
        print('=' * 80)
        print('Abstract:')
        print(paper.abstract)
        print()
        print('=' * 80)
        print('Full Text Preview (first 500 chars):')
        print(paper.fullText[:500])
        print('...')
        print('=' * 80)

    await database.disconnect()

if __name__ == '__main__':
    test_paper()
