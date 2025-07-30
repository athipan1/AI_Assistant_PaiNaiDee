"""
Tourism content crawler for fetching data from external sources.
Handles RSS feeds, APIs, and web scraping with respect for robots.txt.
"""

import asyncio
import aiohttp
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import time
import re
from bs4 import BeautifulSoup

# Optional import for RSS parsing
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False
    feedparser = None

logger = logging.getLogger(__name__)

class TourismCrawler:
    """Crawler for tourism-related content from various sources."""
    
    def __init__(self, respect_robots=True, delay_between_requests=1.0):
        self.respect_robots = respect_robots
        self.delay_between_requests = delay_between_requests
        self.last_request_time = 0
        self.robots_cache = {}
        
        # Tourism sources focused on Thailand (using web scraping since RSS dependencies are not available)
        self.sources = {
            "tat_tourism": {
                "type": "web",
                "url": "https://www.tourismthailand.org/",
                "name": "Tourism Authority of Thailand",
                "enabled": True
            },
            "sample_web_source": {
                "type": "web", 
                "url": "https://example.com/thailand-tourism",
                "name": "Sample Thailand Tourism Site",
                "enabled": False  # Disabled by default since it's a placeholder
            }
        }
    
    async def crawl_all_sources(self) -> List[Dict[str, Any]]:
        """Crawl all enabled sources and return documents."""
        all_documents = []
        
        for source_id, source_config in self.sources.items():
            if not source_config.get("enabled", False):
                continue
                
            try:
                logger.info(f"Crawling source: {source_config['name']}")
                documents = await self._crawl_source(source_id, source_config)
                all_documents.extend(documents)
                
                # Rate limiting
                await asyncio.sleep(self.delay_between_requests)
                
            except Exception as e:
                logger.error(f"Error crawling {source_id}: {e}")
        
        logger.info(f"Total documents crawled: {len(all_documents)}")
        return all_documents
    
    async def _crawl_source(self, source_id: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crawl a specific source based on its type."""
        if config["type"] == "rss":
            return await self._crawl_rss(source_id, config)
        elif config["type"] == "web":
            return await self._crawl_web(source_id, config)
        elif config["type"] == "api":
            return await self._crawl_api(source_id, config)
        else:
            logger.warning(f"Unknown source type: {config['type']}")
            return []
    
    async def _crawl_rss(self, source_id: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crawl RSS feeds."""
        documents = []
        
        if not HAS_FEEDPARSER:
            logger.warning("feedparser not available, skipping RSS crawling for {config['url']}")
            return []
        
        try:
            # Check robots.txt if enabled
            if self.respect_robots and not self._can_fetch(config["url"]):
                logger.warning(f"Robots.txt disallows crawling {config['url']}")
                return []
            
            # Parse RSS feed
            feed = feedparser.parse(config["url"])
            
            if feed.bozo:
                logger.warning(f"RSS feed {config['url']} has parsing issues")
            
            for entry in feed.entries[:10]:  # Limit to recent 10 entries
                doc = {
                    "id": f"{source_id}_{hash(entry.link)}",
                    "content": self._extract_text_content(entry),
                    "metadata": {
                        "source": config["name"],
                        "source_id": source_id,
                        "url": entry.link,
                        "title": getattr(entry, 'title', ''),
                        "published": getattr(entry, 'published', ''),
                        "crawled_at": datetime.now().isoformat(),
                        "type": "rss_article"
                    }
                }
                documents.append(doc)
            
        except Exception as e:
            logger.error(f"Error crawling RSS {config['url']}: {e}")
        
        return documents
    
    async def _crawl_web(self, source_id: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crawl web pages for content."""
        documents = []
        
        try:
            # Check robots.txt if enabled
            if self.respect_robots and not self._can_fetch(config["url"]):
                logger.warning(f"Robots.txt disallows crawling {config['url']}")
                return []
            
            # Fetch page content
            async with aiohttp.ClientSession() as session:
                async with session.get(config["url"], timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        
                        # Parse with BeautifulSoup
                        soup = BeautifulSoup(content, 'html.parser')
                        
                        # Extract articles/content blocks
                        articles = self._extract_articles(soup, config)
                        
                        for idx, article in enumerate(articles[:5]):  # Limit to 5 articles
                            doc = {
                                "id": f"{source_id}_{hash(article['content'])}",
                                "content": article['content'],
                                "metadata": {
                                    "source": config["name"],
                                    "source_id": source_id,
                                    "url": article.get('url', config["url"]),
                                    "title": article.get('title', ''),
                                    "crawled_at": datetime.now().isoformat(),
                                    "type": "web_article"
                                }
                            }
                            documents.append(doc)
                    
        except Exception as e:
            logger.error(f"Error crawling web {config['url']}: {e}")
        
        return documents
    
    async def _crawl_api(self, source_id: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Crawl API endpoints."""
        documents = []
        
        try:
            headers = config.get("headers", {})
            params = config.get("params", {})
            
            async with aiohttp.ClientSession() as session:
                async with session.get(config["url"], headers=headers, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Process API response based on expected format
                        documents = self._process_api_response(source_id, config, data)
                        
        except Exception as e:
            logger.error(f"Error crawling API {config['url']}: {e}")
        
        return documents
    
    def _extract_text_content(self, entry) -> str:
        """Extract clean text content from RSS entry."""
        content_parts = []
        
        # Title
        if hasattr(entry, 'title'):
            content_parts.append(entry.title)
        
        # Summary/Description
        if hasattr(entry, 'summary'):
            # Remove HTML tags
            clean_summary = re.sub(r'<[^>]+>', '', entry.summary)
            content_parts.append(clean_summary)
        
        return '\n\n'.join(content_parts)
    
    def _extract_articles(self, soup: BeautifulSoup, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract article content from web page."""
        articles = []
        
        # Generic selectors for common article structures
        selectors = [
            'article',
            '.article',
            '.post',
            '.content',
            '.entry',
            'h2, h3',  # Headings as content indicators
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            
            for element in elements[:10]:  # Limit extraction
                text = element.get_text(strip=True)
                
                if len(text) > 100:  # Only meaningful content
                    # Try to find title
                    title_elem = element.find(['h1', 'h2', 'h3', 'h4'])
                    title = title_elem.get_text(strip=True) if title_elem else ''
                    
                    # Try to find link
                    link_elem = element.find('a')
                    url = ''
                    if link_elem and link_elem.get('href'):
                        url = urljoin(config["url"], link_elem['href'])
                    
                    articles.append({
                        'content': text,
                        'title': title,
                        'url': url
                    })
            
            if articles:  # If we found articles with this selector, stop
                break
        
        return articles
    
    def _process_api_response(self, source_id: str, config: Dict[str, Any], data: Any) -> List[Dict[str, Any]]:
        """Process API response and convert to documents."""
        documents = []
        
        # This would be customized based on specific API formats
        # For now, implement a generic handler
        if isinstance(data, dict):
            if 'results' in data:
                items = data['results']
            elif 'data' in data:
                items = data['data']
            elif 'items' in data:
                items = data['items']
            else:
                items = [data]
        elif isinstance(data, list):
            items = data
        else:
            items = []
        
        for idx, item in enumerate(items[:10]):
            if isinstance(item, dict):
                content = self._extract_api_content(item)
                if content:
                    doc = {
                        "id": f"{source_id}_api_{idx}",
                        "content": content,
                        "metadata": {
                            "source": config["name"],
                            "source_id": source_id,
                            "crawled_at": datetime.now().isoformat(),
                            "type": "api_data",
                            "raw_data": item
                        }
                    }
                    documents.append(doc)
        
        return documents
    
    def _extract_api_content(self, item: Dict[str, Any]) -> str:
        """Extract text content from API response item."""
        content_fields = ['content', 'description', 'summary', 'text', 'title', 'name']
        content_parts = []
        
        for field in content_fields:
            if field in item and item[field]:
                content_parts.append(str(item[field]))
        
        return '\n\n'.join(content_parts)
    
    def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        if not self.respect_robots:
            return True
        
        try:
            parsed_url = urlparse(url)
            robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
            
            # Check cache first
            if robots_url in self.robots_cache:
                robots_parser = self.robots_cache[robots_url]
            else:
                robots_parser = RobotFileParser()
                robots_parser.set_url(robots_url)
                robots_parser.read()
                self.robots_cache[robots_url] = robots_parser
            
            # Check if we can fetch the URL
            return robots_parser.can_fetch('*', url)
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            return True  # Default to allowing if robots.txt check fails
    
    def add_source(self, source_id: str, config: Dict[str, Any]) -> None:
        """Add a new source to crawl."""
        required_fields = ['type', 'url', 'name']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Source config must include '{field}'")
        
        config.setdefault('enabled', True)
        self.sources[source_id] = config
        logger.info(f"Added new source: {config['name']}")
    
    def remove_source(self, source_id: str) -> bool:
        """Remove a source from crawling."""
        if source_id in self.sources:
            del self.sources[source_id]
            logger.info(f"Removed source: {source_id}")
            return True
        return False
    
    def get_sources(self) -> Dict[str, Any]:
        """Get all configured sources."""
        return self.sources.copy()
    
    def enable_source(self, source_id: str) -> bool:
        """Enable a source for crawling."""
        if source_id in self.sources:
            self.sources[source_id]['enabled'] = True
            return True
        return False
    
    def disable_source(self, source_id: str) -> bool:
        """Disable a source from crawling."""
        if source_id in self.sources:
            self.sources[source_id]['enabled'] = False
            return True
        return False