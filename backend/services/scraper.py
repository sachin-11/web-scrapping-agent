import asyncio
import random
import logging
import re
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

async def random_sleep(min_sec: float = 1.0, max_sec: float = 3.0):
    """Sleeps for a random duration to mimic human behavior."""
    delay = random.uniform(min_sec, max_sec)
    logger.info(f"Sleeping for {delay:.2f} seconds...")
    await asyncio.sleep(delay)

async def scrape_website(url: str) -> dict:
    """
    Scrapes a single webpage using headless Playwright Chromium.
    Extracts page title, raw text, all links, image URLs, and meta description.
    """
    result = {
        "url": url,
        "success": False,
        "page_title": "",
        "raw_text": "",
        "all_links": [],
        "image_urls": [],
        "meta_description": "",
        "error": None
    }
    
    # Simple validation
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        result["error"] = "Invalid URL structure. Ensure scheme (http/https) is included."
        return result

    try:
        async with async_playwright() as p:
            logger.info(f"Launching chromium to scrape: {url}")
            browser = await p.chromium.launch(headless=True)
            
            # Setup context with anti-bot configurations
            context = await browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 720},
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
                }
            )
            
            page = await context.new_page()
            
            # Set default navigation timeout (30 seconds)
            page.set_default_navigation_timeout(30000)
            page.set_default_timeout(10000)
            
            # Navigate to the page
            response = await page.goto(url, wait_until="domcontentloaded")
            
            if not response:
                raise Exception("Failed to load page response.")
                
            if response.status >= 400:
                result["error"] = f"HTTP Error Status: {response.status}"
                await browser.close()
                return result

            # Wait briefly for dynamic JS to load components
            await page.wait_for_timeout(1000)

            # 1. Page Title
            result["page_title"] = await page.title()

            # 2. Raw Text Extraction with Semantic Selector Trimming
            # Pre-processing: Remove non-content and junk elements directly from DOM
            await page.evaluate("""() => {
                const junkSelectors = ['header', 'footer', 'nav', 'aside', 'script', 'style', 'noscript', 'iframe'];
                junkSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => el.remove());
                });
            }""")

            # Prioritize extraction from core content containers if available
            core_selectors = ['main', 'article', '.product-list', '#content', '#main']
            core_text = ""
            for selector in core_selectors:
                elements = page.locator(selector)
                count = await elements.count()
                if count > 0:
                    texts = []
                    for i in range(count):
                        txt = await elements.nth(i).inner_text()
                        if txt.strip():
                            texts.append(txt.strip())
                    if texts:
                        core_text = "\n\n".join(texts)
                        logger.info(f"Extracted core text using selector: {selector}")
                        break

            if core_text:
                result["raw_text"] = core_text
            else:
                body_element = page.locator("body")
                if await body_element.count() > 0:
                    result["raw_text"] = await body_element.inner_text()
                else:
                    result["raw_text"] = await page.locator("html").inner_text()
                logger.info("Extracted text from full body after trimming junk selectors.")

            # 3. Meta Description
            meta_desc_loc = page.locator('meta[name="description"]')
            if await meta_desc_loc.count() > 0:
                result["meta_description"] = await meta_desc_loc.first.get_attribute("content") or ""
            else:
                # Try og:description
                meta_og_loc = page.locator('meta[property="og:description"]')
                if await meta_og_loc.count() > 0:
                    result["meta_description"] = await meta_og_loc.first.get_attribute("content") or ""

            # 4. Extract Links
            link_locators = page.locator("a")
            link_count = await link_locators.count()
            links = []
            for i in range(link_count):
                href = await link_locators.nth(i).get_attribute("href")
                if href:
                    # Resolve relative links
                    absolute_href = urljoin(url, href)
                    links.append(absolute_href)
            result["all_links"] = list(set(links)) # Deduplicate

            # 5. Extract Image URLs
            img_locators = page.locator("img")
            img_count = await img_locators.count()
            images = []
            for i in range(img_count):
                src = await img_locators.nth(i).get_attribute("src")
                if src:
                    absolute_src = urljoin(url, src)
                    images.append(absolute_src)
            result["image_urls"] = list(set(images)) # Deduplicate

            result["success"] = True
            await browser.close()
            logger.info(f"Successfully scraped: {url}")
            
    except PlaywrightTimeoutError:
        logger.error(f"Timeout occurred while scraping: {url}")
        result["error"] = "Timeout error: The page took too long to load."
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        result["error"] = str(e)

    return result


async def find_next_page_link(page, current_url: str) -> str:
    """
    Tries to detect and return the URL of the 'Next Page' button/link.
    Uses heuristic locator lookups based on common patterns.
    """
    # 1. Look for rel="next"
    try:
        next_rel = page.locator('a[rel="next"]')
        if await next_rel.count() > 0:
            href = await next_rel.first.get_attribute("href")
            if href:
                return urljoin(current_url, href)
    except Exception:
        pass

    # 2. Text heuristics for matching links (e.g. Next, Older, Right chevron)
    next_text_selectors = [
        "a:has-text('Next')",
        "a:has-text('next')",
        "a:has-text('Next Page')",
        "a:has-text('Older')",
        "a:has-text('>')",
        "a:has-text('»')",
        "a:has-text('→')"
    ]
    
    for selector in next_text_selectors:
        try:
            loc = page.locator(selector)
            count = await loc.count()
            for i in range(count):
                item = loc.nth(i)
                if await item.is_visible():
                    href = await item.get_attribute("href")
                    if href:
                        resolved_url = urljoin(current_url, href)
                        if resolved_url != current_url:
                            return resolved_url
        except Exception:
            continue

    # 3. Check for elements with class names containing next
    try:
        class_loc = page.locator('a[class*="next" i], a[class*="pagination-next" i]')
        count = await class_loc.count()
        for i in range(count):
            item = class_loc.nth(i)
            if await item.is_visible():
                href = await item.get_attribute("href")
                if href:
                    resolved_url = urljoin(current_url, href)
                    if resolved_url != current_url:
                        return resolved_url
    except Exception:
        pass

    return ""


def generate_pagination_urls(base_url: str, next_url: str, max_pages: int) -> list:
    """
    Analyzes base_url and next_url to predict and generate subsequent page URLs.
    """
    urls = []
    
    # 1. Parameter matching, e.g. page=2, p=2
    for param in ['page', 'p', 'pg', 'offset']:
        if f"{param}=2" in next_url:
            for n in range(2, max_pages + 1):
                urls.append(next_url.replace(f"{param}=2", f"{param}={n}"))
            return urls
            
    # 2. Common path pattern matching, e.g. page-2.html, page/2/
    for pattern in [r'page-2', r'page_2', r'page/2', r'/2/']:
        match = re.search(pattern, next_url)
        if match:
            matched_str = match.group(0)
            for n in range(2, max_pages + 1):
                urls.append(next_url.replace(matched_str, matched_str.replace('2', str(n))))
            return urls

    # Fallback to simple page incrementing if next_url is found but not matched by rules
    if next_url:
        logger.warning(f"Could not automatically parse page pattern for next_url: {next_url}. Scaping Page 2 only.")
        urls.append(next_url)
        
    return urls


async def scrape_single_page_task(url: str, page_num: int, stagger_seconds: float = 0.0) -> dict:
    """
    Helper task to scrape a single page with a short stagger delay to prevent CPU/Network spikes.
    """
    if stagger_seconds > 0:
        logger.info(f"Staggering page {page_num} launch by {stagger_seconds:.2f} seconds...")
        await asyncio.sleep(stagger_seconds)
        
    logger.info(f"Scraping Page {page_num} (Concurrent): {url}")
    page_result = await scrape_website(url)
    page_result["page_number"] = page_num
    return page_result


async def scrape_multiple_pages(base_url: str, max_pages: int = 5) -> list:
    """
    Crawls and scrapes multiple pages starting from base_url.
    Performs concurrent, asynchronous scraping using asyncio.gather for ultra-fast crawls.
    """
    scraped_pages = []
    
    logger.info(f"Starting CONCURRENT pagination scrape from: {base_url} (Max: {max_pages} pages)")
    
    # --- Step 1: Scrape Page 1 (Sequential) to detect Next link pattern ---
    logger.info(f"Scraping Page 1 (Initial): {base_url}")
    page1_result = await scrape_website(base_url)
    page1_result["page_number"] = 1
    scraped_pages.append(page1_result)
    
    if not page1_result["success"] or max_pages == 1:
        return scraped_pages

    # --- Step 2: Detect the Next Page URL from Page 1 ---
    next_url = ""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            page = await context.new_page()
            page.set_default_navigation_timeout(30000)
            
            await page.goto(base_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(1000)
            
            next_url = await find_next_page_link(page, base_url)
            await browser.close()
    except Exception as e:
        logger.error(f"Error while looking for next page link on Page 1: {e}")
        
    if not next_url:
        logger.info("Could not auto-detect a valid next page URL. Returning Page 1 results only.")
        return scraped_pages
        
    logger.info(f"Detected next page URL from Page 1: {next_url}")
    
    # --- Step 3: Generate subsequent page URLs dynamically ---
    subsequent_urls = generate_pagination_urls(base_url, next_url, max_pages)
    logger.info(f"Generated {len(subsequent_urls)} subsequent page URLs: {subsequent_urls}")
    
    if not subsequent_urls:
        return scraped_pages

    # --- Step 4: Launch concurrent, parallel async scrape tasks using asyncio.gather ---
    tasks = []
    for idx, url in enumerate(subsequent_urls, 2):
        # Stagger browser launches slightly (e.g. 0.25 seconds) to avoid high CPU spikes
        stagger_delay = (idx - 2) * 0.25
        tasks.append(scrape_single_page_task(url, idx, stagger_delay))
        
    logger.info(f"Launching {len(tasks)} parallel page scraper tasks...")
    concurrent_results = await asyncio.gather(*tasks)
    
    # Add concurrent results to the list
    scraped_pages.extend(concurrent_results)
    
    # Sort pages by page_number to maintain logical order
    scraped_pages.sort(key=lambda x: x["page_number"])
    
    logger.info(f"Scrape completed. Total pages processed concurrently: {len(scraped_pages)}")
    return scraped_pages
