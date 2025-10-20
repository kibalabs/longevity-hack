"""Script to populate SNP database tables from JSON files."""

import asyncio
import json
from pathlib import Path

from core import logging
from core.store.database import Database

import _path_fix  # noqa: F401
from longevity.create_app_manager import create_database
from longevity.store import schema


async def populate_gwas_data(database: Database, gwasDir: Path):
    """Populate tbl_snps_gwas from JSON files."""
    logging.basicConfig()

    gwasFiles = list(gwasDir.glob('*.json'))
    logging.info(f'Found {len(gwasFiles)} GWAS files to process')

    insertedCount = 0

    for gwasFile in gwasFiles:
        with open(gwasFile, 'r') as f:
            gwasData = json.load(f)

        rsid = gwasData.get('rsid')
        if not rsid:
            logging.warning(f'No rsid found in {gwasFile.name}, skipping')
            continue

        associations = gwasData.get('associations', [])

        for assoc in associations:
            trait = assoc.get('DISEASE/TRAIT') or assoc.get('trait', '')
            if not trait:
                continue

            pvalueMlogRaw = assoc.get('PVALUE_MLOG') or assoc.get('pvalue_mlog_calculated')
            pvalueMlog = float(pvalueMlogRaw) if pvalueMlogRaw else None

            await schema.SnpsGwasRepository.upsert(
                database=database,
                constraintColumnNames=[
                    schema.SnpsGwasTable.c.rsid.key,
                    schema.SnpsGwasTable.c.trait.key,
                    schema.SnpsGwasTable.c.pubmedId.key,
                ],
                rsid=rsid,
                trait=trait,
                traitCategory=assoc.get('trait_category'),
                pvalue=assoc.get('P-VALUE') or assoc.get('pvalue'),
                pvalueMlog=pvalueMlog,
                effectAllele=assoc.get('effect_allele') or assoc.get('risk_allele'),
                effectType=assoc.get('effect_type'),
                orOrBeta=assoc.get('OR or BETA'),
                riskAlleleFrequency=assoc.get('RISK ALLELE FREQUENCY'),
                studyDescription=assoc.get('STUDY'),
                pubmedId=assoc.get('PUBMEDID'),
                chromosome=assoc.get('CHR_ID'),
                position=assoc.get('CHR_POS'),
                mappedGene=assoc.get('MAPPED_GENE'),
            )
            insertedCount += 1

        if insertedCount % 1000 == 0:
            logging.info(f'Inserted {insertedCount} GWAS associations')

    logging.info(f'GWAS population complete: {insertedCount} inserted')


async def populate_clinvar_data(database: Database, annotationsDir: Path):
    """Populate tbl_snps_clinvar from JSON annotation files."""
    annotationFiles = list(annotationsDir.glob('*.json'))
    logging.info(f'Found {len(annotationFiles)} annotation files to process')

    insertedCount = 0

    for annotationFile in annotationFiles:
        with open(annotationFile, 'r') as f:
            annotation = json.load(f)

        rsid = annotationFile.stem

        # Extract ClinVar data from annotation
        clinvar = annotation.get('clinvar')
        if not clinvar:
            continue

        # Get gene symbol from nested structure
        geneData = clinvar.get('gene', {})
        gene = geneData.get('symbol', 'Unknown') if isinstance(geneData, dict) else str(geneData)

        # Get RCV records (submissions) - can be a list or a single dict
        rcvData = clinvar.get('rcv')
        if not rcvData:
            continue

        # Normalize to list
        rcvRecords = [rcvData] if isinstance(rcvData, dict) else rcvData

        # Insert each ClinVar RCV record
        for rcv in rcvRecords:
            # Get condition name
            conditions = rcv.get('conditions', {})
            conditionName = conditions.get('name', 'Unknown') if isinstance(conditions, dict) else 'Unknown'

            await schema.SnpsClinvarRepository.upsert(
                database=database,
                constraintColumnNames=[
                    schema.SnpsClinvarTable.c.rsid.key,
                    schema.SnpsClinvarTable.c.accession.key,
                ],
                rsid=rsid,
                gene=gene,
                accession=rcv.get('accession', 'Unknown'),
                clinicalSignificance=rcv.get('clinical_significance', 'Unknown'),
                condition=conditionName,
                reviewStatus=rcv.get('review_status', 'Unknown'),
                lastEvaluated=rcv.get('last_evaluated'),
                numberSubmitters=rcv.get('number_submitters', 0),
            )
            insertedCount += 1

        if insertedCount % 1000 == 0:
            logging.info(f'Inserted {insertedCount} ClinVar submissions')

    logging.info(f'ClinVar population complete: {insertedCount} inserted')


async def main():
    logging.basicConfig()
    logging.info('Starting SNP database population')

    database = await create_database()

    gwasDir = Path('./.data/snps-gwas')
    annotationsDir = Path('./.data/snps')

    async with database.create_context_connection():
        logging.info('Populating GWAS data...')
        # await populate_gwas_data(database=database, gwasDir=gwasDir)

        logging.info('Populating ClinVar data...')
        await populate_clinvar_data(database=database, annotationsDir=annotationsDir)

    logging.info('SNP database population complete!')


if __name__ == '__main__':
    asyncio.run(main())
