import asyncio
import random
import logging
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Shared executor — limits concurrent browser instances
_executor = ThreadPoolExecutor(max_workers=2)


def _sync_scrape_page(url: str) -> dict:
    """
    Synchronous Playwright scrape. Runs in a thread pool to avoid the Windows
    asyncio SelectorEventLoop subprocess limitation.
    """
    result = {
        "url": url,
        "success": False,
        "page_title": "",
        "raw_text": "",
        "all_links": [],
        "image_urls": [],
        "meta_description": "",
        "error": None,
    }

    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        result["error"] = "Invalid URL structure. Ensure scheme (http/https) is included."
        return result

    try:
        with sync_playwright() as p:
            logger.info(f"Launching chromium to scrape: {url}")
            browser = p.chromium.launch(headless=True)

            context = browser.new_context(
                user_agent=USER_AGENT,
                viewport={"width": 1280, "height": 720},
                extra_http_headers={
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                },
            )

            page = context.new_page()
            page.set_default_navigation_timeout(30000)
            page.set_default_timeout(10000)

            response = page.goto(url, wait_until="domcontentloaded")

            if not response:
                raise Exception("Failed to load page response.")

            if response.status >= 400:
                result["error"] = f"HTTP Error Status: {response.status}"
                browser.close()
                return result

            page.wait_for_timeout(1000)

            result["page_title"] = page.title()

            body = page.locator("body")
            if body.count() > 0:
                result["raw_text"] = body.inner_text()
            else:
                result["raw_text"] = page.locator("html").inner_text()

            meta_desc = page.locator('meta[name="description"]')
            if meta_desc.count() > 0:
                result["meta_description"] = meta_desc.first.get_attribute("content") or ""
            else:
                og_desc = page.locator('meta[property="og:description"]')
                if og_desc.count() > 0:
                    result["meta_description"] = og_desc.first.get_attribute("content") or ""

            link_locs = page.locator("a")
            links = []
            for i in range(link_locs.count()):
                href = link_locs.nth(i).get_attribute("href")
                if href:
                    links.append(urljoin(url, href))
            result["all_links"] = list(set(links))

            img_locs = page.locator("img")
            images = []
            for i in range(img_locs.count()):
                src = img_locs.nth(i).get_attribute("src")
                if src:
                    images.append(urljoin(url, src))
            result["image_urls"] = list(set(images))

            result["success"] = True
            browser.close()
            logger.info(f"Successfully scraped: {url}")

    except PlaywrightTimeoutError:
        logger.error(f"Timeout scraping {url}")
        result["error"] = "Timeout error: The page took too long to load."
    except Exception as e:
        msg = str(e) or type(e).__name__
        logger.error(f"Error scraping {url}: {msg}")
        result["error"] = msg

    return result


def _sync_find_next_page(url: str) -> str:
    """Opens the page synchronously and returns the next-page URL, or empty string."""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()
            page.set_default_navigation_timeout(30000)
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            next_url = _find_next_page_link_sync(page, url)
            browser.close()
            return next_url
    except Exception as e:
        logger.error(f"Error finding next page on {url}: {e}")
        return ""


def _find_next_page_link_sync(page, current_url: str) -> str:
    try:
        rel_next = page.locator('a[rel="next"]')
        if rel_next.count() > 0:
            href = rel_next.first.get_attribute("href")
            if href:
                return urljoin(current_url, href)
    except Exception:
        pass

    selectors = [
        "a:has-text('Next')", "a:has-text('next')", "a:has-text('Next Page')",
        "a:has-text('Older')", "a:has-text('>')", "a:has-text('»')", "a:has-text('→')",
    ]
    for selector in selectors:
        try:
            loc = page.locator(selector)
            for i in range(loc.count()):
                item = loc.nth(i)
                if item.is_visible():
                    href = item.get_attribute("href")
                    if href:
                        resolved = urljoin(current_url, href)
                        if resolved != current_url:
                            return resolved
        except Exception:
            continue

    try:
        cls_loc = page.locator('a[class*="next" i], a[class*="pagination-next" i]')
        for i in range(cls_loc.count()):
            item = cls_loc.nth(i)
            if item.is_visible():
                href = item.get_attribute("href")
                if href:
                    resolved = urljoin(current_url, href)
                    if resolved != current_url:
                        return resolved
    except Exception:
        pass

    return ""


async def scrape_website(url: str) -> dict:
    """Async wrapper — runs sync Playwright in a thread pool."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, _sync_scrape_page, url)


async def scrape_multiple_pages(base_url: str, max_pages: int = 5) -> list:
    """Crawls and scrapes multiple pages following auto-detected next-page links."""
    scraped_pages = []
    visited_urls = set()
    current_url = base_url

    logger.info(f"Starting pagination scrape from: {base_url} (Max: {max_pages} pages)")

    for page_num in range(1, max_pages + 1):
        if not current_url or current_url in visited_urls:
            logger.info("No further pages found or cycle detected. Stopping.")
            break

        visited_urls.add(current_url)
        logger.info(f"Scraping Page {page_num}: {current_url}")

        page_result = await scrape_website(current_url)
        page_result["page_number"] = page_num
        scraped_pages.append(page_result)

        if not page_result["success"] or page_num == max_pages:
            break

        # Random delay between pages
        delay = random.uniform(1.0, 3.0)
        logger.info(f"Sleeping {delay:.2f}s before next page...")
        await asyncio.sleep(delay)

        loop = asyncio.get_event_loop()
        next_url = await loop.run_in_executor(_executor, _sync_find_next_page, current_url)

        if next_url:
            logger.info(f"Detected next page: {next_url}")
            current_url = next_url
        else:
            logger.info("No next page detected.")
            break

    return scraped_pages
