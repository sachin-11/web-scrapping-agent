import os
import logging
import hashlib
import time
import json
import shutil
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict

# Import scraping and processing services
from services.scraper import scrape_multiple_pages, scrape_website
from services.llm_service import extract_structured_data
from services.image_downloader import download_images
from services.excel_service import create_excel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

router = APIRouter()

# Define request schemas
class ScrapeRequest(BaseModel):
    url: str
    instruction: str
    download_images: Optional[bool] = False
    max_pages: Optional[int] = 1

class ScrapeResponse(BaseModel):
    success: bool
    excel_url: str
    total_records: int
    preview_data: List[dict]
    error: Optional[str] = None

@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_endpoint(request: ScrapeRequest):
    """
    Orchestrator endpoint with a 1-hour TTL Cache Layer to avoid redundant crawling and OpenAI costs.
    Crawls, extracts, processes, compiles Excel, and responds with preview records.
    """
    logger.info(f"Received scrape request for URL: {request.url}")
    
    # Generate unique MD5 hash for the request details
    cache_param_str = f"{request.url}_{request.instruction}_{request.max_pages}_{request.download_images}"
    hash_key = hashlib.md5(cache_param_str.encode('utf-8')).hexdigest()
    cache_id = f"cache_{hash_key}"
    
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_cache_path = os.path.join(backend_dir, "outputs", f"{cache_id}.json")
    excel_cache_path = os.path.join(backend_dir, "outputs", f"{cache_id}.xlsx")
    
    TTL_SECONDS = 3600 # 1 hour TTL
    
    # 1. TTL Cache Lookup
    if os.path.exists(json_cache_path) and os.path.exists(excel_cache_path):
        mtime = os.path.getmtime(json_cache_path)
        if time.time() - mtime < TTL_SECONDS:
            logger.info(f"Cache HIT for key: {hash_key}. Loading results instantaneously from disk...")
            try:
                with open(json_cache_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                
                # Copy back to default result.xlsx for standard legacy links
                shutil.copy2(excel_cache_path, os.path.join(backend_dir, "outputs", "result.xlsx"))
                
                return ScrapeResponse(
                    success=True,
                    excel_url=cached_data["excel_url"],
                    total_records=cached_data["total_records"],
                    preview_data=cached_data["preview_data"]
                )
            except Exception as ce:
                logger.warning(f"Cache read failure: {ce}. Falling back to default crawl flow.")

    try:
        # 2. Scraping using Playwright
        pages = await scrape_multiple_pages(request.url, max_pages=request.max_pages)
        
        # Check if scraping succeeded
        successful_pages = [p for p in pages if p["success"]]
        if not successful_pages:
            errors = "; ".join([p["error"] for p in pages if p["error"]]) or "Unknown crawling error"
            raise HTTPException(status_code=400, detail=f"Failed to crawl target pages: {errors}")
            
        # 3. Extract structured data from pages via LLM
        all_records = []
        for page in successful_pages:
            logger.info(f"Extracting structured data from Page {page['page_number']}")
            extracted_obj = extract_structured_data(page["raw_text"], request.instruction)
            
            # Smart list-flattening logic based on common extraction layouts
            records_from_page = []
            if isinstance(extracted_obj, list):
                records_from_page = extracted_obj
            elif isinstance(extracted_obj, dict):
                # If LLM wrapped list in a key (e.g. {"products": [...]})
                list_keys = [k for k, v in extracted_obj.items() if isinstance(v, list)]
                if list_keys:
                    # Select the first list key found (e.g., "products", "items", "results")
                    records_from_page = extracted_obj[list_keys[0]]
                else:
                    records_from_page = [extracted_obj]
            
            all_records.extend(records_from_page)
            
        if not all_records:
            raise HTTPException(status_code=422, detail="LLM data extraction returned empty records. Try updating your instruction.")

        # 4. Optional Image Downloading & Processing
        image_paths_map = {}
        if request.download_images:
            logger.info("Initializing image downloading for extracted records...")
            output_folder = os.path.join(backend_dir, "outputs", "images")
            
            for idx, record in enumerate(all_records):
                # Search inside fields for image keys (e.g. image, img, image_url, src, photo)
                img_url = ""
                for key, val in record.items():
                    key_lower = str(key).lower()
                    if any(term in key_lower for term in ["image", "img", "src", "photo", "pic"]) and isinstance(val, str) and val.startswith("http"):
                        img_url = val
                        break
                
                # Fallback to general page source images if no specific column matching image is found
                if not img_url and pages:
                    # Pick a general page source image for variety or placeholder
                    available_page_imgs = [img for p in pages for img in p.get("image_urls", [])]
                    if idx < len(available_page_imgs):
                        img_url = available_page_imgs[idx]
                
                if img_url:
                    product_title = record.get("name") or record.get("title") or record.get("product_name") or f"product_{idx}"
                    # Download, convert, and resize
                    saved = download_images([img_url], str(product_title), output_folder)
                    if saved:
                        image_paths_map[idx] = saved[0]
                        # Update record with relative image path for sheet clarity
                        record["local_image_path"] = os.path.relpath(saved[0], backend_dir).replace("\\", "/")

        # 5. Generate Styled Excel Spreadsheet
        logger.info("Generating formatted Excel spreadsheet...")
        create_excel(all_records, image_paths_map, excel_cache_path)
        
        # Duplicate to default result.xlsx path
        shutil.copy2(excel_cache_path, os.path.join(backend_dir, "outputs", "result.xlsx"))
        
        # 6. Save successful responses to Cache
        preview_data = all_records[:5]
        excel_url = f"/api/download-excel?id={cache_id}"
        
        response_data = {
            "excel_url": excel_url,
            "total_records": len(all_records),
            "preview_data": preview_data
        }
        
        try:
            with open(json_cache_path, "w", encoding="utf-8") as f:
                json.dump(response_data, f, ensure_ascii=False, indent=2)
            logger.info(f"Cached successful scrape results under ID: {cache_id}")
        except Exception as ce:
            logger.warning(f"Failed to save results to cache: {ce}")
        
        return ScrapeResponse(
            success=True,
            excel_url=excel_url,
            total_records=len(all_records),
            preview_data=preview_data
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error occurred in scrape orchestrator endpoint: {e}")
        return ScrapeResponse(
            success=False,
            excel_url="",
            total_records=0,
            preview_data=[],
            error=str(e)
        )

@router.get("/download-excel")
def download_excel_endpoint(id: Optional[str] = None):
    """
    Returns the generated Excel file as a download response. Supports dynamic caching IDs.
    """
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Prevent path traversal vulnerabilities by enforcing alphanumeric key matching
    if id and re.match(r"^[a-zA-Z0-9_-]+$", id):
        excel_path = os.path.join(backend_dir, "outputs", f"{id}.xlsx")
    else:
        excel_path = os.path.join(backend_dir, "outputs", "result.xlsx")
    
    if not os.path.exists(excel_path):
        raise HTTPException(status_code=404, detail="Excel spreadsheet has not been generated yet. Run a scrape job first.")
        
    return FileResponse(
        path=excel_path,
        filename="scraped_data_result.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@router.get("/status")
def status_endpoint():
    """
    Standard health check endpoint.
    """
    return {
        "status": "ok",
        "health": "healthy",
        "version": "1.0.0"
    }
