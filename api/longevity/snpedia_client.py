"""
SNPedia client for fetching human-readable SNP summaries.

SNPedia (https://www.snpedia.com) is a wiki-based database of SNPs with
community-curated clinical interpretations.
"""

import json
import re
from pathlib import Path

from core.requester import Requester


class SNPediaClient:
    """Client for accessing SNPedia via MediaWiki API."""

    BASE_URL = 'https://bots.snpedia.com/api.php'
    CACHE_DIR = Path('./.data/snpedia-cache')

    def __init__(self, requester: Requester, cacheEnabled: bool = True) -> None:
        """
        Initialize SNPedia client.

        Args:
            requester: HTTP requester for making API calls
            cacheEnabled: Whether to cache responses to disk
        """
        self.requester = requester
        self.cacheEnabled = cacheEnabled
        if cacheEnabled:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, rsid: str) -> Path:
        """Get cache file path for an rsid."""
        return self.CACHE_DIR / f'{rsid}.json'

    async def _fetch_from_api(self, rsid: str) -> dict | None:
        """
        Fetch SNP page content from SNPedia MediaWiki API.

        Args:
            rsid: SNP identifier (e.g., 'rs429358')

        Returns:
            Dictionary with page content and metadata, or None if not found
        """
        params = {'action': 'query', 'titles': rsid, 'prop': 'revisions', 'rvprop': 'content', 'format': 'json', 'formatversion': '2'}

        try:
            response = await self.requester.get(url=self.BASE_URL, dataDict=params, timeout=10)
            data = response.json()

            pages = data.get('query', {}).get('pages', [])
            if not pages:
                return None

            page = pages[0]
            if 'missing' in page:
                return None

            revisions = page.get('revisions', [])
            if not revisions:
                return None

            content = revisions[0].get('content', '')

            return {
                'rsid': rsid,
                'title': page.get('title', rsid),
                'content': content,
                'pageid': page.get('pageid'),
            }

        except Exception as e:
            print(f'Warning: Failed to fetch {rsid} from SNPedia: {e}')
            return None

    def _parse_summary(self, wikiContent: str) -> str:
        """
        Extract human-readable summary from SNPedia wiki content.

        Args:
            wikiContent: Raw wiki markup text

        Returns:
            Cleaned summary text
        """
        if not wikiContent:
            return ''

        # Remove wiki templates
        content = re.sub(r'\{\{[^}]+\}\}', '', wikiContent)

        # Remove references
        content = re.sub(r'<ref[^>]*>.*?</ref>', '', content, flags=re.DOTALL)

        # Remove wiki links but keep text: [[link|text]] -> text
        content = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', content)
        content = re.sub(r'\[\[([^\]]+)\]\]', r'\1', content)

        # Remove external links
        content = re.sub(r'\[http[^\]]+\]', '', content)

        # Extract first paragraph (usually the summary)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if not paragraphs:
            return ''

        # Take first substantive paragraph
        for para in paragraphs:
            # Skip section headers
            if para.startswith('=') or para.startswith('__'):
                continue
            # Skip very short paragraphs
            if len(para) < 50:
                continue
            # Clean up
            para = re.sub(r'\s+', ' ', para)
            return para[:500]  # Limit to 500 chars

        return ''

    async def get_snp_summary(self, rsid: str) -> dict | None:
        """
        Get SNP summary from SNPedia with caching.

        Args:
            rsid: SNP identifier (e.g., 'rs429358')

        Returns:
            Dictionary with:
                - rsid: SNP identifier
                - summary: Human-readable summary text
                - url: Link to SNPedia page
            Or None if not found
        """
        # Check cache first
        if self.cacheEnabled:
            cachePath = self._get_cache_path(rsid)
            if cachePath.exists():
                try:
                    with open(cachePath, 'r') as f:
                        return json.load(f)
                except Exception:
                    pass

        # Fetch from API
        pageData = await self._fetch_from_api(rsid)
        if not pageData:
            return None

        # Parse summary
        summary = self._parse_summary(pageData['content'])

        result = {
            'rsid': rsid,
            'summary': summary,
            'url': f'https://www.snpedia.com/index.php/{rsid}',
            'title': pageData.get('title', rsid),
        }

        # Cache result
        if self.cacheEnabled:
            cachePath = self._get_cache_path(rsid)
            with open(cachePath, 'w') as f:
                json.dump(result, f, indent=2)

        return result
