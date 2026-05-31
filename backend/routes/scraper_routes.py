import os
import logging
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
    Orchestrator endpoint to crawl page, extract structured data via LLM,
    optionally download & resize images, generate Excel sheet, and return previews.
    """
    logger.info(f"Received scrape request for URL: {request.url}")
    
    try:
        # 1. Scraping using Playwright
        pages = await scrape_multiple_pages(request.url, max_pages=request.max_pages)
        
        # Check if scraping succeeded
        successful_pages = [p for p in pages if p["success"]]
        if not successful_pages:
            errors = "; ".join([p["error"] for p in pages if p["error"]]) or "Unknown crawling error"
            raise HTTPException(status_code=400, detail=f"Failed to crawl target pages: {errors}")
            
        # 2. Extract structured data from pages via LLM
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

        # 3. Optional Image Downloading & Processing
        image_paths_map = {}
        if request.download_images:
            logger.info("Initializing image downloading for extracted records...")
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

        # 4. Generate Styled Excel Spreadsheet
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        excel_output_path = os.path.join(backend_dir, "outputs", "result.xlsx")
        
        logger.info("Generating formatted Excel spreadsheet...")
        create_excel(all_records, image_paths_map, excel_output_path)
        
        # 5. Build Response
        # Return first 5 rows as a preview
        preview_data = all_records[:5]
        
        return ScrapeResponse(
            success=True,
            excel_url="/api/download-excel",
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
def download_excel_endpoint():
    """
    Returns the generated Excel file as a download response.
    """
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
