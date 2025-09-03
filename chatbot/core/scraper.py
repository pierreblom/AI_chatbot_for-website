"""
Web scraping module for the Chatbot API
Scrapes websites and extracts content for the knowledge base
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse, urlunparse
from typing import Dict, List, Set, Any
import re
from dataclasses import dataclass
from .config import Config

logger = logging.getLogger(__name__)

@dataclass
class ScrapedPage:
    """Data class for a scraped page"""
    url: str
    title: str
    content: str
    metadata: Dict[str, Any]
    links: List[str]

class WebScraper:
    """Web scraper for extracting content from websites"""
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.scraper_config = self.config.get_scraper_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.scraper_config['user_agent']
        })
        self.visited_urls: Set[str] = set()
    
    def scrape_website(self, url: str, include_links: bool = True, max_depth: int = 2) -> Dict[str, Any]:
        """
        Scrape a website starting from the given URL
        
        Args:
            url: Starting URL to scrape
            include_links: Whether to follow internal links
            max_depth: Maximum depth to follow links
            
        Returns:
            Dict with success status, pages scraped, and any errors
        """
        try:
            # Reset visited URLs for new scraping session
            self.visited_urls.clear()
            
            # Validate URL
            if not self._is_valid_url(url):
                return {"success": False, "error": "Invalid URL provided"}
            
            # Check if domain is allowed
            domain = urlparse(url).netloc
            if not self.config.is_domain_allowed(domain):
                return {"success": False, "error": f"Domain {domain} is not in allowed domains list"}
            
            pages = []
            urls_to_scrape = [(url, 0)]  # (url, depth)
            max_pages = self.scraper_config['max_pages']
            
            logger.info(f"Starting scrape of {url} with max_depth={max_depth}")
            
            while urls_to_scrape and len(pages) < max_pages:
                current_url, depth = urls_to_scrape.pop(0)
                
                # Skip if already visited or too deep
                if current_url in self.visited_urls or depth > max_depth:
                    continue
                
                logger.info(f"Scraping {current_url} (depth: {depth})")
                
                # Scrape the page
                page_data = self._scrape_page(current_url)
                if page_data:
                    pages.append(page_data)
                    self.visited_urls.add(current_url)
                    
                    # Add internal links for next level if we should follow links
                    if include_links and depth < max_depth:
                        base_domain = urlparse(url).netloc
                        for link in page_data.links:
                            link_domain = urlparse(link).netloc
                            # Only follow links within the same domain
                            if link_domain == base_domain and link not in self.visited_urls:
                                urls_to_scrape.append((link, depth + 1))
                
                # Rate limiting
                time.sleep(self.scraper_config['delay'])
            
            logger.info(f"Scraping completed. {len(pages)} pages scraped.")
            
            return {
                "success": True,
                "pages": [self._page_to_dict(page) for page in pages],
                "total_pages": len(pages),
                "urls_visited": list(self.visited_urls)
            }
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            return {"success": False, "error": str(e)}
    
    def _scrape_page(self, url: str) -> ScrapedPage:
        """Scrape a single page"""
        try:
            # Check if file extension is blocked
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            for ext in self.scraper_config['blocked_extensions']:
                if path.endswith(ext):
                    logger.warning(f"Skipping {url} - blocked extension")
                    return None
            
            # Make request
            response = self.session.get(
                url, 
                timeout=self.scraper_config['timeout'],
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Check content length
            if len(response.content) > self.scraper_config['max_content_length']:
                logger.warning(f"Skipping {url} - content too large")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract main content
            content = self._extract_content(soup)
            
            # Extract links
            links = self._extract_links(soup, url)
            
            # Extract metadata
            metadata = self._extract_metadata(soup, response)
            
            return ScrapedPage(
                url=url,
                title=title,
                content=content,
                metadata=metadata,
                links=links
            )
            
        except requests.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Parse error for {url}: {e}")
            return None
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main text content from HTML"""
        # Try to find main content areas first
        main_content = None
        
        # Look for common content containers
        for selector in ['main', 'article', '.content', '#content', '.main', '#main']:
            element = soup.select_one(selector)
            if element:
                main_content = element
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Extract text
        text = main_content.get_text()
        
        # Clean up text
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]  # Remove empty lines
        
        # Join with single spaces and limit length
        content = ' '.join(lines)
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract internal links from the page"""
        links = []
        base_domain = urlparse(base_url).netloc
        
        for link_tag in soup.find_all('a', href=True):
            href = link_tag['href']
            
            # Convert relative URLs to absolute
            absolute_url = urljoin(base_url, href)
            
            # Only include HTTP/HTTPS links from the same domain
            parsed = urlparse(absolute_url)
            if (parsed.scheme in ['http', 'https'] and 
                parsed.netloc == base_domain and
                absolute_url not in links):
                
                # Clean the URL (remove fragments)
                clean_url = urlunparse((
                    parsed.scheme, parsed.netloc, parsed.path,
                    parsed.params, parsed.query, ''
                ))
                links.append(clean_url)
        
        return links
    
    def _extract_metadata(self, soup: BeautifulSoup, response: requests.Response) -> Dict[str, Any]:
        """Extract metadata from the page"""
        metadata = {
            'scraped_at': time.time(),
            'content_type': response.headers.get('content-type', ''),
            'status_code': response.status_code,
            'content_length': len(response.content)
        }
        
        # Extract meta tags
        meta_tags = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                meta_tags[name] = content
        
        metadata['meta_tags'] = meta_tags
        
        # Extract headings
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    'level': i,
                    'text': heading.get_text().strip()
                })
        
        metadata['headings'] = headings[:20]  # Limit to first 20 headings
        
        return metadata
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _page_to_dict(self, page: ScrapedPage) -> Dict[str, Any]:
        """Convert ScrapedPage to dictionary"""
        return {
            'url': page.url,
            'title': page.title,
            'content': page.content,
            'metadata': page.metadata,
            'links': page.links,
            'content_length': len(page.content),
            'links_count': len(page.links)
        }
    
    def get_page_summary(self, url: str) -> Dict[str, Any]:
        """Get a quick summary of a single page without full scraping"""
        try:
            response = self.session.head(url, timeout=10)
            return {
                'url': url,
                'status_code': response.status_code,
                'content_type': response.headers.get('content-type', ''),
                'content_length': response.headers.get('content-length', 'unknown'),
                'accessible': response.status_code == 200
            }
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'accessible': False
            }