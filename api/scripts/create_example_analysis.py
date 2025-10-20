#!/usr/bin/env python3
"""Create example genome analysis in database.

This script:
1. Uses AppManager to create a genome analysis
2. Simulates uploading the example genome file
3. Processes it through the analysis pipeline
4. Prints the analysis ID to use as EXAMPLE_ANALYSIS_ID in constants.py

Usage:
    python3 scripts/create_example_analysis.py

After running, update EXAMPLE_ANALYSIS_ID in longevity/constants.py with the printed ID.
"""
import asyncio
import sys
import uuid
from pathlib import Path
from io import BytesIO

# Add parent directory to path to import longevity modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from longevity.create_app_manager import create_app_manager
from longevity.store import schema
from core.util import file_util
from core import logging
from starlette.datastructures import UploadFile


class SimpleUploadFile(UploadFile):
    """Simple implementation of UploadFile for testing."""

    def __init__(self, filename: str, content: bytes) -> None:
        self._content = content
        self._filename = filename
        super().__init__(file=BytesIO(content), filename=filename)

    async def read(self, size: int = -1) -> bytes:
        return self._content if size == -1 else self._content[:size]


async def create_example_analysis() -> None:
    """Create the example analysis in the database using AppManager."""
    appManager = create_app_manager()

    await appManager.database.connect()
    print('Connected to database')

    try:
        async with appManager.database.create_context_connection():
            # Find the example genome file
            exampleFilePath = Path(__file__).parent.parent / 'examples' / 'genome_Lilly_Mendel_v4_ui2.txt'
            if not exampleFilePath.exists():
                print(f'Error: Example file not found at {exampleFilePath}')
                return

            print(f'Found example file: {exampleFilePath}')

            # Generate a new ID for this example
            newExampleId = str(uuid.uuid4())
            print(f'Creating new example with ID: {newExampleId}')

            # Read the file content
            genomeContent = await file_util.read_file(str(exampleFilePath))
            contentBytes = genomeContent.encode('utf-8')

            # Create the genome analysis using AppManager with the specific ID
            print('Creating genome analysis record...')
            async with appManager.database.create_transaction() as connection:
                genomeAnalysis = await schema.GenomeAnalysesRepository.create(
                    database=appManager.database,
                    connection=connection,
                    genomeAnalysisId=newExampleId,
                    userId='example-user',
                    fileName='genome_Lilly_Mendel_v4_ui2.txt',
                    status='waiting_for_upload',
                    totalSnps=None,
                    matchedSnps=None,
                    totalAssociations=None,
                    clinvarCount=None,
                )
            print(f'Created genome analysis with ID: {newExampleId}')

            # Write the file to the uploads directory directly (skip the upload API call)
            uploadPath = appManager.uploadsDir / f'{newExampleId}_genome_Lilly_Mendel_v4_ui2.txt'
            await file_util.write_file(str(uploadPath), genomeContent)
            print(f'Copied file to: {uploadPath}')

            # Update status to queued
            async with appManager.database.create_transaction() as connection:
                await schema.GenomeAnalysesRepository.update(
                    database=appManager.database,
                    connection=connection,
                    genomeAnalysisId=newExampleId,
                    status='queued',
                )

            # Run the analysis directly (bypassing queue)
            print(f'Running analysis directly (bypassing queue)...')
            await appManager.run_genome_analysis(
                genomeAnalysisId=newExampleId,
                inputFilePath=str(uploadPath),
            )

            print('\n' + '='*80)
            print('✓ Example analysis created successfully!')
            print('='*80)

            # Get final status using AppManager
            finalAnalysis = await appManager.get_genome_analysis(newExampleId)
            print(f'  Status: {finalAnalysis.status}')
            if finalAnalysis.summary:
                print(f'  Total SNPs: {finalAnalysis.summary.totalSnps:,}')
                print(f'  Matched SNPs: {finalAnalysis.summary.matchedSnps:,}')
                print(f'  Total Associations: {finalAnalysis.summary.totalAssociations:,}')
                print(f'  ClinVar entries: {finalAnalysis.summary.clinvarCount:,}')

            print('\n' + '='*80)
            print('📝 UPDATE REQUIRED:')
            print('='*80)
            print(f'Update EXAMPLE_ANALYSIS_ID in longevity/constants.py to:')
            print(f'\n  EXAMPLE_ANALYSIS_ID = \'{newExampleId}\'')
            print('\n' + '='*80)

            # Generate AI analyses for top categories
            print('\n' + '='*80)
            print('🤖 Generating AI analyses for top categories...')
            print('='*80)

            overview = await appManager.get_genome_analysis_overview(newExampleId)

            # Get top 5 categories by SNP count
            topCategories = sorted(overview.categoryGroups, key=lambda x: x.totalCount, reverse=True)[:5]

            for i, category in enumerate(topCategories, 1):
                print(f'\n[{i}/5] Analyzing: {category.category} ({category.totalCount} SNPs)...')
                analysis = await appManager.analyze_category(
                    genomeAnalysisId=newExampleId,
                    genomeAnalysisResultId=category.genomeAnalysisResultId,
                    useCache=False,  # Force fresh generation
                )
                print(f'  ✓ Generated analysis ({len(analysis.analysis)} chars, {analysis.snpsAnalyzed} SNPs, {len(analysis.papersUsed)} papers)')

            print('\n✓ AI analysis generation complete!')

    finally:
        await appManager.database.disconnect()
        print('\nDisconnected from database')


if __name__ == '__main__':
    logging.init_basic_logging()
    asyncio.run(create_example_analysis())
