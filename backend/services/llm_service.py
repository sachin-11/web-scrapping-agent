import os
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
from services.image_downloader import get_image_as_base64

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize OpenAI client
# It will automatically pick up OPENAI_API_KEY from environment or .env
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def clean_and_truncate_text(text: str, max_chars: int = 12000) -> str:
    """
    Cleans up extra whitespaces and truncates the text to fit within roughly 3000 tokens.
    """
    if not text:
        return ""
    # Remove excessive blank lines and whitespaces
    cleaned = " ".join(text.split())
    # Truncate
    if len(cleaned) > max_chars:
        logger.info(f"Truncating text from {len(cleaned)} to {max_chars} characters.")
        cleaned = cleaned[:max_chars]
    return cleaned

def extract_structured_data(raw_text: str, user_instruction: str) -> dict:
    """
    Extracts structured JSON from raw page text matching user specifications.
    Uses gpt-4o-mini for optimized and low-cost data extraction.
    """
    cleaned_text = clean_and_truncate_text(raw_text)
    
    system_prompt = "You are a data extraction expert. Extract data as clean JSON only. No markdown, no explanation."
    user_prompt = f"""
User Instruction: {user_instruction}

Raw Page Text Content:
{cleaned_text}
"""
    try:
        logger.info("Requesting structured data extraction from GPT-4o-mini...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        raw_response = response.choices[0].message.content
        logger.info("Extraction completed successfully.")
        
        # Parse JSON
        parsed_data = json.loads(raw_response)
        return parsed_data
        
    except Exception as e:
        logger.error(f"Error during structured data extraction: {e}")
        return {}

def analyze_image(image_path: str, context: str) -> dict:
    """
    Sends the local image file to GPT-4o Vision API to analyze color, condition, style, and visible text.
    """
    try:
        logger.info(f"Preparing image for GPT-4o Vision analysis: {image_path}")
        # Get image in base64 data URL format
        base64_image_url = get_image_as_base64(image_path)
        
        system_prompt = "You are an expert visual analyzer. Analyze the provided image and extract its properties as a clean JSON object."
        user_prompt = f"""
Additional Context/Instruction: {context}

Please analyze this image and output a clean JSON object with the following fields:
- product_color (string description)
- condition (string description)
- style (string description)
- visible_text (list of any text seen inside the image)
- description (brief summary of what the image contains)

Ensure that you return only valid JSON without markdown formatting.
"""
        logger.info("Sending image query to GPT-4o...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": base64_image_url
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        raw_response = response.choices[0].message.content
        logger.info("Image analysis completed successfully.")
        
        parsed_analysis = json.loads(raw_response)
        return parsed_analysis
        
    except Exception as e:
        logger.error(f"Error analyzing image with GPT-4o Vision: {e}")
        return {
            "product_color": "Unknown",
            "condition": "Unknown",
            "style": "Unknown",
            "visible_text": [],
            "description": f"Analysis failed: {str(e)}"
        }

def generate_excel_schema(sample_data: dict) -> list:
    """
    Uses gpt-4o-mini to analyze sample extracted data and recommend an ordered list of flat column headers
    ideal for saving to a spreadsheet.
    """
    system_prompt = "You are a spreadsheet design expert. Given a JSON object, output a clean JSON list containing the flat column names in logical order."
    user_prompt = f"""
Here is a sample of extracted JSON data structure:
{json.dumps(sample_data, indent=2)}

Please define a flat list of column headers (strings) that should represent this data in an Excel sheet.
For example, if the data is a list of items or nested, think of how to flatten it logically.
Return a JSON object containing a single key "columns" which maps to a list of strings.
Example output format:
{{
  "columns": ["id", "title", "price", "description"]
}}
"""
    try:
        logger.info("Requesting logical column schema from GPT-4o-mini...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1
        )
        
        raw_response = response.choices[0].message.content
        parsed_res = json.loads(raw_response)
        columns = parsed_res.get("columns", [])
        
        logger.info(f"Generated logical Excel columns: {columns}")
        return columns
        
    except Exception as e:
        logger.error(f"Error generating Excel schema: {e}")
        # Return fallback keys if prompt failed
        return list(sample_data.keys()) if isinstance(sample_data, dict) else ["data"]
