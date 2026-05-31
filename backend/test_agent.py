import os
import asyncio
import logging
from unittest.mock import patch, MagicMock

# Import services
from services.scraper import scrape_multiple_pages, scrape_website
from services.llm_service import extract_structured_data, generate_excel_schema, clean_and_truncate_text
from services.image_downloader import download_images
from services.excel_service import create_excel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

async def run_pipeline_test(use_mock: bool = False):
    print("\n" + "="*50)
    print("TESTING STEP 1: PIPELINE RUN")
    print("="*50)
    
    url = "https://books.toscrape.com"
    instruction = "Extract book title, price, rating, and availability"
    max_pages = 2
    
    # 1. Scrape Website
    print(f"\n[Scraper] Crawling up to {max_pages} pages from {url}...")
    pages = await scrape_multiple_pages(url, max_pages=max_pages)
    
    print(f"\n[Scraper Result] Total crawled pages: {len(pages)}")
    for page in pages:
        print(f"- Page {page['page_number']} success status: {page['success']}")
        print(f"  Raw text length: {len(page['raw_text'])} characters")
        print(f"  Links found: {len(page['all_links'])}")
        print(f"  Images found: {len(page['image_urls'])}")
    
    # 2. Extract structured data via LLM
    print(f"\n[LLM] Extracting structured columns using instruction: '{instruction}'...")
    
    dummy_extracted = {
        "books": [
            {"title": "A Light in the Attic", "price": "£51.77", "rating": "Three Stars", "availability": "In stock", "image_url": "https://books.toscrape.com/media/cache/2c/da/2cdad67c44b002e7ead01d1493851362.jpg"},
            {"title": "Tipping the Velvet", "price": "£53.74", "rating": "One Star", "availability": "In stock", "image_url": "https://books.toscrape.com/media/cache/26/0c/260c6ae16bce311857bb0d2826839283.jpg"},
            {"title": "Soumission", "price": "£50.10", "rating": "One Star", "availability": "In stock", "image_url": "https://books.toscrape.com/media/cache/3e/ef/3eef99c9d9adef34639f510662022830.jpg"}
        ]
    }
    
    extracted_records = []
    
    # If no valid API Key is provided, use mock to ensure test runs successfully
    api_key = os.getenv("OPENAI_API_KEY", "")
    is_mocking = use_mock or not api_key or api_key.startswith("your-openai")
    
    if is_mocking:
        print("[Notice] No active OpenAI API Key found. Running with mock structured outputs.")
        for page in pages:
            if page["success"]:
                extracted_records.extend(dummy_extracted["books"])
    else:
        for page in pages:
            if page["success"]:
                obj = extract_structured_data(page["raw_text"], instruction)
                # Parse list out of dictionary wrapper
                if isinstance(obj, list):
                    extracted_records.extend(obj)
                elif isinstance(obj, dict):
                    list_keys = [k for k, v in obj.items() if isinstance(v, list)]
                    if list_keys:
                        extracted_records.extend(obj[list_keys[0]])
                    else:
                        extracted_records.append(obj)

    print(f"\n[LLM Result] Total extracted book records: {len(extracted_records)}")
    if extracted_records:
        print("Sample extracted book JSON:")
        print(extracted_records[0])

    # 3. Download & Resize Images
    print("\n[Image Downloader] Downloading and resizing book image thumbnails...")
    image_paths_map = {}
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    output_folder = os.path.join(backend_dir, "outputs", "images")
    
    for idx, book in enumerate(extracted_records[:3]): # Download first 3 for test speed
        img_url = book.get("image_url")
        if img_url:
            saved = download_images([img_url], book.get("title", "book"), output_folder)
            if saved:
                image_paths_map[idx] = saved[0]
                print(f"- Image {idx+1} saved to: {saved[0]}")

    # 4. Generate Excel
    print("\n[Excel Writer] Compiling styled Excel spreadsheet...")
    excel_path = os.path.join(backend_dir, "outputs", "result.xlsx")
    create_excel(extracted_records[:3], image_paths_map, excel_path)
    print(f"[Excel Writer Result] Formatted spreadsheet saved at: {excel_path}")
    print(f"Spreadsheet File Exists: {os.path.exists(excel_path)}")

    return len(pages), len(extracted_records), len(image_paths_map)

async def test_error_handling():
    print("\n" + "="*50)
    print("TESTING STEP 2: ERROR BOUNDARY HANDLERS")
    print("="*50)

    # 1. Invalid URL Test
    print("\n[Error 1] Testing Scraper with Invalid URL structure...")
    res1 = await scrape_website("invalid_scheme_url.com")
    print("Success status:", res1["success"])
    print("Captured Error Details:", res1["error"])

    # 2. Empty/Nonexistent Domain Test
    print("\n[Error 2] Testing Scraper with Unresolvable Domain...")
    res2 = await scrape_website("https://nonexistent-domain-xyz-12345.com")
    print("Success status:", res2["success"])
    print("Captured Error Details:", res2["error"])

    # 3. LLM Timeout Test
    print("\n[Error 3] Mocking LLM connection timeout error boundary...")
    # Mocking OpenAI completion creation raising exception
    with patch("services.llm_service.client.chat.completions.create", side_effect=Exception("Connection timed out (504 Gateway)")):
        res3 = extract_structured_data("Raw text sample", "extract something")
        print("Captured JSON on exception:", res3)
        assert res3 == {}
        print("LLM exception boundary validation successful!")

def print_cost_estimation(pages_count: int, records_count: int, images_count: int):
    print("\n" + "="*50)
    print("ESTIMATED API PIPELINE RUN COST (USD)")
    print("="*50)
    
    # 1. GPT-4o-Mini Text pricing: $0.150 / 1M Input, $0.600 / 1M Output
    # Let's estimate roughly 2500 input tokens per page, 1000 output tokens for extracted lists
    input_tokens_text = pages_count * 2500
    output_tokens_text = records_count * 80
    
    cost_input_text = (input_tokens_text / 1_000_000) * 0.150
    cost_output_text = (output_tokens_text / 1_000_000) * 0.600
    total_text_cost = cost_input_text + cost_output_text
    
    # 2. GPT-4o Vision: Let's assume user requested Vision analysis for downloaded photos
    # Each Vision image at 500x500 is approx 85 tokens input
    # Model: gpt-4o ($5.00 / 1M input)
    vision_input_tokens = images_count * 85
    cost_vision = (vision_input_tokens / 1_000_000) * 5.00
    
    total_cost = total_text_cost + cost_vision
    
    print(f"Total Pages Crawled: {pages_count}")
    print(f"Total Text Extracted: {records_count} rows")
    print(f"Total Images Downloaded: {images_count} items")
    print("-"*40)
    print(f"Text Input Tokens (est.):  {input_tokens_text} -> ${cost_input_text:.6f}")
    print(f"Text Output Tokens (est.): {output_tokens_text} -> ${cost_output_text:.6f}")
    print(f"Vision Input Tokens (est.): {vision_input_tokens} -> ${cost_vision:.6f}")
    print("-"*40)
    print(f"Total Approximate Pipeline USD Cost: ${total_cost:.6f}")
    print("="*50 + "\n")

async def main():
    print("Starting Web Scraper Agent complete pipeline integration tests...")
    
    # Run the main pipeline
    pages_crawled, records, images = await run_pipeline_test()
    
    # Run the error cases
    await test_error_handling()
    
    # Calculate costs
    print_cost_estimation(pages_crawled, records, images)

if __name__ == "__main__":
    asyncio.run(main())
