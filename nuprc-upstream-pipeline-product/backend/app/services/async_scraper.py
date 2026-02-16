# backend/app/services/async_scraper.py
"""
Async web scraping service using aiohttp for concurrent requests.
"""
import asyncio
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup

from app.services.sources import SourceConfig


async def extract_file_links_async(html_content: str, base_url: str, source_id: str = None) -> List[Dict[str, str]]:
    """
    Extract file links from HTML content.
    For oil/gas/rig: ONLY Excel files (not PDF)
    For concession: PDF files (or both if needed)
    Returns list of dicts with 'url', 'filename', 'file_type'.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    
    # Determine file type filter based on source
    # Oil, Gas, Rig: Prefer Excel, but allow PDF if Excel not available (e.g., 2025 rig is PDF)
    # Concession: PDF only
    excel_preferred_sources = ['oil_production_status', 'gas_production_status', 'rig_disposition']
    prefer_excel = source_id in excel_preferred_sources if source_id else False
    
    # Find all anchor tags with href
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        full_url = urljoin(base_url, href)
        
        # Check if it's a PDF or Excel file
        parsed = urlparse(full_url)
        path_lower = parsed.path.lower()
        
        if prefer_excel:
            # Prefer Excel for oil/gas/rig, but allow PDF as fallback (e.g., 2025 rig)
            if path_lower.endswith(('.xlsx', '.xls')):
                links.append({
                    'url': full_url,
                    'filename': parsed.path.split('/')[-1],
                    'file_type': 'excel'
                })
            elif path_lower.endswith('.pdf'):
                # Allow PDF for rig when Excel not available (e.g., 2025)
                links.append({
                    'url': full_url,
                    'filename': parsed.path.split('/')[-1],
                    'file_type': 'pdf'
                })
        else:
            # PDF files for concession (or both if not specified)
            if path_lower.endswith('.pdf'):
                links.append({
                    'url': full_url,
                    'filename': parsed.path.split('/')[-1],
                    'file_type': 'pdf'
                })
            elif path_lower.endswith(('.xlsx', '.xls')):
                links.append({
                    'url': full_url,
                    'filename': parsed.path.split('/')[-1],
                    'file_type': 'excel'
                })
    
    # Also check for direct file links in page content
    for link in soup.find_all(['link', 'source'], href=True):
        href = link.get('href', '')
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        path_lower = parsed.path.lower()
        
        if prefer_excel:
            # Prefer Excel, but allow PDF as fallback
            if path_lower.endswith(('.xlsx', '.xls')):
                links.append({
                    'url': full_url,
                    'filename': parsed.path.split('/')[-1],
                    'file_type': 'excel'
                })
            elif path_lower.endswith('.pdf'):
                # Allow PDF for rig when Excel not available (e.g., 2025)
                links.append({
                    'url': full_url,
                    'filename': parsed.path.split('/')[-1],
                    'file_type': 'pdf'
                })
        else:
            # PDF or Excel
            if path_lower.endswith(('.pdf', '.xlsx', '.xls')):
                links.append({
                    'url': full_url,
                    'filename': parsed.path.split('/')[-1],
                    'file_type': 'pdf' if path_lower.endswith('.pdf') else 'excel'
                })
    
    # Deduplicate by URL and prefer Excel when both Excel and PDF exist for same filename
    seen = set()
    unique_links = []
    # Track Excel files by base filename (without extension) to prefer over PDF
    excel_files = {}
    
    for link in links:
        if link['url'] not in seen:
            seen.add(link['url'])
            # For Excel-preferred sources, track Excel files to avoid PDF duplicates
            if prefer_excel and link['file_type'] == 'excel':
                # Extract base filename (without extension) to match with PDF
                base_name = link['filename'].rsplit('.', 1)[0].lower()
                excel_files[base_name] = link
            
            unique_links.append(link)
    
    # If Excel preferred, remove PDF files that have Excel equivalents
    if prefer_excel:
        filtered_links = []
        for link in unique_links:
            if link['file_type'] == 'pdf':
                # Check if there's an Excel version of this file
                base_name = link['filename'].rsplit('.', 1)[0].lower()
                if base_name not in excel_files:
                    # No Excel version, keep PDF
                    filtered_links.append(link)
                # If Excel exists, skip PDF (Excel already in list)
            else:
                # Keep all Excel files
                filtered_links.append(link)
        return filtered_links
    
    return unique_links


async def scrape_source_page_async(
    session: aiohttp.ClientSession,
    source: SourceConfig
) -> List[Dict[str, str]]:
    """
    Async scrape a source page and extract all downloadable file links.
    For direct PDF/Excel files, return the link itself.
    For oil/gas/rig: ONLY Excel files (filters out PDF)
    For concession: PDF files
    """
    try:
        # If base_url is a direct PDF/Excel file, return it
        parsed = urlparse(source.base_url)
        path_lower = parsed.path.lower()
        
        if path_lower.endswith(('.pdf', '.xlsx', '.xls')):
            # For oil/gas/rig, prefer Excel but allow PDF (e.g., 2025 rig is PDF)
            excel_preferred_sources = ['oil_production_status', 'gas_production_status', 'rig_disposition']
            # Allow both Excel and PDF for these sources (prefer Excel when both available)
            
            return [{
                'url': source.base_url,
                'filename': parsed.path.split('/')[-1],
                'file_type': 'pdf' if path_lower.endswith('.pdf') else 'excel'
            }]
        
        # Otherwise, fetch the HTML page and extract links
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with session.get(source.base_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
            response.raise_for_status()
            html_content = await response.text()
            # Pass source_id to filter by file type
            return await extract_file_links_async(html_content, source.base_url, source.source_id)
        
    except Exception as e:
        raise Exception(f"Failed to scrape {source.name}: {str(e)}")


async def scrape_all_sources_async(sources: List[SourceConfig], log_func=None) -> Dict[str, List[Dict[str, str]]]:
    """
    Scrape all sources concurrently using async.
    Returns dict mapping source_id to list of file links.
    
    Args:
        sources: List of source configurations to scrape
        log_func: Optional logging function (run_id, level, message)
    """
    # Create session with shorter timeout and connection limits
    timeout = aiohttp.ClientTimeout(total=20, connect=10)
    connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        tasks = [
            scrape_source_page_async(session, source) 
            for source in sources
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Map results to sources
        source_links = {}
        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                error_msg = f"Failed to scrape {source.name}: {str(result)}"
                if log_func:
                    log_func("", "ERROR", error_msg)
                else:
                    print(f"ERROR: {error_msg}")
                source_links[source.source_id] = []
            else:
                source_links[source.source_id] = result
        
        return source_links
