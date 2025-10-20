"""PubMed/NCBI PubTator3 client for fetching paper full texts with database caching."""

import asyncio
import logging
import time
from typing import Any

from core.requester import Requester
from core.store.database import Database
from core.util import date_util

from longevity import model
from longevity.store import schema
from longevity.store.entity_repository import StringFieldFilter


class PubMedClient:
    """Client for fetching paper full texts from PubMed using PubTator3 API with caching."""

    PUBTATOR_URL = 'https://www.ncbi.nlm.nih.gov/research/pubtator3-api/publications/export/biocjson'
    MAX_IDS_PER_REQUEST = 100  # PubTator3 allows up to 100 IDs per request
    RATE_LIMIT_DELAY = 0.34  # ~3 requests per second (conservative)

    def __init__(self, database: Database, requester: Requester) -> None:
        self.database = database
        self.requester = requester
        self.last_request_time = 0.0

    async def _rate_limit(self) -> None:
        """Enforce rate limiting to comply with NCBI's 3 requests/second limit."""
        currentTime = time.time()
        timeSinceLastRequest = currentTime - self.last_request_time
        if timeSinceLastRequest < self.RATE_LIMIT_DELAY:
            await asyncio.sleep(self.RATE_LIMIT_DELAY - timeSinceLastRequest)
        self.last_request_time = time.time()

    async def fetch_paper(self, pubmedId: str) -> model.PubmedPaper | None:
        """Fetch a single paper from PubMed.

        Args:
            pubmedId: The PubMed ID of the paper

        Returns:
            PubmedPaper object or None if not found
        """
        result = await self.fetch_papers([pubmedId])
        return result.get(pubmedId)

    async def fetch_papers(self, pubmedIds: list[str]) -> dict[str, model.PubmedPaper]:
        """Fetch papers with full text, using cache when available.

        Args:
            pubmedIds: List of PubMed IDs

        Returns:
            Dictionary mapping PubMed ID to PubmedPaper objects
        """
        if not pubmedIds:
            return {}

        # Check cache first
        cachedPapers = await self._get_cached_papers(pubmedIds)
        missingIds = [pid for pid in pubmedIds if pid not in cachedPapers]

        if not missingIds:
            logging.info(f'All {len(pubmedIds)} papers found in cache')
            return cachedPapers

        logging.info(f'Found {len(cachedPapers)} papers in cache, fetching {len(missingIds)} from PubMed')

        # Fetch missing papers from PubMed
        params = {'pmids': ','.join(missingIds), 'full': 'true'}
        await self._rate_limit()
        response = await self.requester.get(url=self.PUBTATOR_URL, dataDict=params, timeout=30)
        data = response.json()

        now = date_util.datetime_from_now()
        fetchedPapers = {}

        async with self.database.create_transaction() as connection:
            for paper in data['PubTator3']:
                # When full=true, the API returns PMC IDs in the 'id' field
                # The actual PubMed ID is in the first passage's infons
                pubmedId = None
                title = ''
                abstract = ''
                fullTextParts = []
                journal = ''
                year = ''
                authors = ''

                # Parse passages - separate abstract from full text body
                for passage in paper.get('passages', []):
                    infons = passage.get('infons', {})
                    passageType = infons.get('type', '')
                    sectionType = infons.get('section_type', '')
                    text = passage.get('text', '').strip()

                    # Extract PubMed ID from first passage's infons
                    if pubmedId is None:
                        pubmedId = infons.get('article-id_pmid', paper['id'])

                    # Extract title and metadata - can be in different formats
                    # Full text papers: section_type == 'TITLE' or passageType == 'front'
                    # Abstract-only papers: passageType == 'title'
                    is_title_section = sectionType == 'TITLE' or passageType == 'front' or passageType == 'title'

                    if is_title_section:
                        if not title:  # Only take first title we find
                            title = text
                        # Extract metadata from title passage
                        if not year:
                            year = infons.get('year', '')
                        if not journal:
                            journal = infons.get('journal', '')

                        # Parse authors - they can be in different formats
                        if not authors:
                            # Format 1: name_0, name_1, etc. fields (full text papers)
                            authorList = []
                            i = 0
                            while f'name_{i}' in infons:
                                name_str = infons[f'name_{i}']
                                # Format: "surname:LastName;given-names:FirstName"
                                parts = name_str.split(';')
                                surname = parts[0].replace('surname:', '').strip()
                                given = parts[1].replace('given-names:', '').strip() if len(parts) > 1 else ''
                                if given:
                                    authorList.append(f'{given} {surname}')
                                else:
                                    authorList.append(surname)
                                i += 1
                            if authorList:
                                authors = ', '.join(authorList)
                            # Format 2: authors field (abstract-only papers)
                            elif 'authors' in infons:
                                authors = infons['authors']
                    elif text:
                        # Separate abstract from other body text
                        if passageType == 'abstract' or sectionType == 'ABSTRACT':
                            abstract = text
                        elif passageType not in ['front', 'title']:
                            # Collect all non-title, non-abstract passages as full text
                            fullTextParts.append(text)

                # Join all text parts with double newline
                fullText = '\n\n'.join(fullTextParts) if fullTextParts else abstract

                # Validate required fields - fail loudly if missing
                if not pubmedId:
                    raise ValueError(f'Missing PubMed ID in paper data: {paper}')
                if not title:
                    raise ValueError(f'Missing title for PubMed ID {pubmedId}')
                if not abstract:
                    raise ValueError(f'Missing abstract for PubMed ID {pubmedId}')
                if not fullText:
                    raise ValueError(f'Missing full text for PubMed ID {pubmedId}')
                if not authors:
                    raise ValueError(f'Missing authors for PubMed ID {pubmedId}')
                if not year:
                    raise ValueError(f'Missing year for PubMed ID {pubmedId}')

                # Save to database and add to results
                dbPaper = await schema.PubmedPapersRepository.upsert(
                    database=self.database,
                    connection=connection,
                    constraintColumnNames=['pubmedId'],
                    pubmedId=pubmedId,
                    title=title,
                    abstract=abstract,
                    fullText=fullText,
                    authors=authors,
                    journal=journal,
                    year=year,
                    fetchedDate=now,
                )
                fetchedPapers[pubmedId] = dbPaper

        logging.info(f'Fetched and saved {len(fetchedPapers)} papers')

        # Combine cached and fetched results
        return {**cachedPapers, **fetchedPapers}

    async def _get_cached_papers(self, pubmedIds: list[str]) -> dict[str, model.PubmedPaper]:
        """Get papers from database cache.

        Args:
            pubmedIds: List of PubMed IDs to check

        Returns:
            Dictionary mapping PubMed ID to PubmedPaper objects
        """
        if not pubmedIds:
            return {}

        async with self.database.create_transaction() as connection:
            dbPapers = await schema.PubmedPapersRepository.list_many(
                database=self.database,
                connection=connection,
                fieldFilters=[StringFieldFilter(fieldName='pubmedId', containedIn=pubmedIds)],
            )

        return {dbPaper.pubmedId: dbPaper for dbPaper in dbPapers}
