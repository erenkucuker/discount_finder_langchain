import json
import requests
import re
import easyocr
from bs4 import BeautifulSoup
from langchain_core.output_parsers.json import SimpleJsonOutputParser
from discount_finder_langchain.prompts import (
    EXTRACT_COUPONS_FROM_TEXT_PROMPT,
    EXTRACT_FORM_FIELDS_PROMPT
)
from discount_finder_langchain.config import config
from langchain.tools import StructuredTool
from discount_finder_langchain.prompts import PARSER_COUPON_CODE_LIST
from discount_finder_langchain.schemas import (
    ExtractCouponsFromTextInputTool,
    ScrapeSomeImagesFromWebsiteInputTool,
    ExtractTextFromImagesInputTool,
    ExtractFormFieldsInputTool,
    SearchCouponsFromWebInputTool,
    CleanHtmlInputTool
)
from discount_finder_langchain.constant import (
    CODE_PATTERNS,
    COUPON_SELECTORS,
    COUPON_ATTRIBUTES,
    COUPON_SITES,
    SCRAPE_TIMEOUT,
    COUPON_SEARCH_TIMEOUT
)
from typing import List, Optional
from discount_finder_langchain.schemas import CouponCode, CouponCodeList
from discount_finder_langchain.utils import (
    fetch_url_content,
    process_image_for_ocr,
    filter_image_by_size,
    extract_base_url,
    process_ocr_detection,
    validate_coupon_code,
)
from discount_finder_langchain.utils import vprint
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
reader = easyocr.Reader(['en'])


def scrape_some_images_from_website_tool_func(url: str) -> Optional[List[str]]:
    vprint("🌐 Scraping website...")
    images = []
    try:
        vprint("📥 Fetching webpage content...")
        html_content = fetch_url_content(url)
        if not html_content:
            return []

        vprint("🧹 Cleaning HTML content...")
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all image tags

        img_tags = soup.find_all('img', limit=250)
        vprint(f"Found {len(img_tags)} total image tags")

        # Extract base URL
        base_url = extract_base_url(url)
        if not base_url:
            vprint("⚠️ Could not determine base URL, using original URL")
            return []

        for img in img_tags:
            try:
                src = filter_image_by_size(img, base_url)
                if src and src not in images:
                    images.append(src)
            except Exception as img_error:
                vprint(
                    f"⚠️ Error processing individual image: {str(img_error)}")
                continue

        vprint("✅ Website scraping completed successfully")
        return images

    except Exception as e:
        vprint(f"❌ Error scraping website: {str(e)}")
        return images


def extract_text_from_images_tool_func(images: List[str]) -> Optional[List[object]]:
    vprint("🔍 Starting image analysis...")
    try:
        all_extracted_texts = []
        vprint(f"📸 Processing {len(images)} images...")
        for idx, img_url in enumerate(images, 1):
            try:
                vprint(
                    f"🖼️ Analyzing image {idx}/{len(images)}: {img_url[:50]}...")
                resp = requests.get(img_url, timeout=SCRAPE_TIMEOUT)
                resp.raise_for_status()

                enhanced = process_image_for_ocr(resp.content)
                if enhanced is None:
                    continue

                vprint("📝 Performing OCR...")
                detections = reader.readtext(enhanced)
                for detection in detections:
                    result = process_ocr_detection(detection)
                    if result:
                        all_extracted_texts.append(result)

                if all_extracted_texts:
                    vprint(f"✅ Found {len(all_extracted_texts)} text segments")
                else:
                    vprint("⚠️ No text found in image")
            except Exception as e:
                vprint(f"❌ Error processing image {img_url}: {e}")
                continue

        vprint(
            f"✨ Image analysis completed. Found {len(all_extracted_texts)} text segments in total")
        return all_extracted_texts
    except Exception as e:
        vprint(f"❌ Error in image analysis: {str(e)}")
        return []


def extract_coupons_from_text_tool_func(extracted_texts: List[object]) -> Optional[List[CouponCode]]:
    vprint("🔍 Starting coupon extraction from text...")
    vprint(f"📝 Analyzing text of length: {len(extracted_texts)}")
    try:
        llm = ChatOpenAI(
            temperature=0,
            openai_api_key=OPENAI_API_KEY,
            model="gpt-4o-mini",
            model_kwargs={"response_format": {"type": "json_object"}}
        )
        chain = EXTRACT_COUPONS_FROM_TEXT_PROMPT | llm | PARSER_COUPON_CODE_LIST
        result = chain.invoke({"text": extracted_texts})

        if not isinstance(result, CouponCodeList):
            vprint("⚠️ Unexpected response format")
            return []

        valid_coupons = []
        for coupon in result.coupons:
            try:
                if validate_coupon_code(coupon.code):
                    valid_coupons.append(coupon)
            except Exception as e:
                vprint(f"⚠️ Error validating coupon: {str(e)}")
                continue

        if valid_coupons:
            vprint(f"✅ Found {len(valid_coupons)} valid coupons")
            return valid_coupons
        else:
            vprint("⚠️ No valid coupon codes found")
            return []

    except Exception as e:
        vprint(f"❌ Error extracting coupons: {str(e)}")
        return []


def extract_form_fields_tool_func(html: str) -> Optional[str]:
    vprint("🔍 Starting form field extraction...")
    llm = ChatOpenAI(
        temperature=0,
        openai_api_key=OPENAI_API_KEY,
        model="gpt-4o-mini",
        model_kwargs={"response_format": {"type": "json_object"}}
    )
    chain = EXTRACT_FORM_FIELDS_PROMPT | llm | SimpleJsonOutputParser()
    try:
        vprint("🤖 Analyzing HTML with LLM...")
        result = chain.invoke({"html": html})
        vprint("✅ Form field extraction completed")

        form_fields = {
            "form_fields": {
                "coupon_input": {"css_path": result.get("coupon_input", {}).get("css_path")} if result.get("coupon_input") else None,
                "apply_button": {"css_path": result.get("apply_button", {}).get("css_path")} if result.get("apply_button") else None
            }
        }
        return json.dumps(form_fields, indent=2)
    except Exception as e:
        vprint(f"❌ Error in form field extraction: {str(e)}")
        return json.dumps({"form_fields": None})


def search_coupons_from_web_func(merchant_name: str) -> Optional[List[CouponCode]]:
    vprint(f"🔍 Searching coupons for merchant: {merchant_name}")
    coupons = []
    vprint("🌐 Starting requests to coupon sites...")

    sites = [site.format(merchant_name=merchant_name) for site in COUPON_SITES]

    for site in sites:
        try:
            vprint(f"📥 Fetching: {site}")
            html_content = fetch_url_content(site, COUPON_SEARCH_TIMEOUT)
            if not html_content:
                continue

            vprint(f"📝 Analyzing content from: {site}")
            soup = BeautifulSoup(html_content, 'html.parser')

            for selector in COUPON_SELECTORS:
                elements = soup.select(selector)
                vprint(
                    f"🔍 Found {len(elements)} potential coupon elements with selector: {selector}")
                for element in elements:
                    code = None
                    description = None

                    # Check coupon attributes first
                    for attr in COUPON_ATTRIBUTES:
                        if code_value := element.get(attr):
                            if validate_coupon_code(code_value):
                                code = code_value.upper()
                                vprint(
                                    f"💡 Found code in attribute {attr}: {code}")
                                break

                    if not code:
                        text_content = element.get_text(strip=True)
                        for pattern in CODE_PATTERNS:
                            if match := re.search(pattern, text_content, re.I):
                                potential_code = match.group(1).upper()
                                if validate_coupon_code(potential_code):
                                    code = potential_code
                                    vprint(f"💡 Found code in text: {code}")
                                    break

                    if code and description:
                        vprint(f"✅ Adding valid coupon: {code}")
                        coupons.append({
                            'code': code,
                            'source': site,
                        })

        except Exception as e:
            vprint(f"❌ Error processing site {site}: {str(e)}")
            continue

    seen = set()
    unique_coupons = []
    for coupon in coupons:
        if coupon['code'] not in seen:
            seen.add(coupon['code'])
            unique_coupons.append(coupon)

    vprint(f"✨ Found {len(unique_coupons)} unique coupons")
    return json.dumps(unique_coupons)


def clean_html_tool_func(html: str, tags_to_remove: List[str]) -> str:
    """Clean HTML by removing specified tags"""
    vprint("🧹 Starting HTML cleaning...")
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Remove specified tags
        for tag in tags_to_remove:
            vprint(f"Removing {tag} tags...")
            for element in soup.find_all(tag):
                element.decompose()

        vprint("✅ HTML cleaning completed")
        return str(soup)
    except Exception as e:
        vprint(f"❌ Error cleaning HTML: {str(e)}")
        return html


scrape_some_images_from_website_tool = StructuredTool(
    name="scrape_some_images_from_website",
    func=scrape_some_images_from_website_tool_func,
    description="Scrape a website and return a list of image URLs found on the page. Returns a list(array) of image URLs.",
    args_schema=ScrapeSomeImagesFromWebsiteInputTool
)

extract_text_from_images_tool = StructuredTool(
    name="extract_text_from_images",
    func=extract_text_from_images_tool_func,
    description="Extract text from images using OCR.",
    args_schema=ExtractTextFromImagesInputTool
)

extract_coupons_from_text_tool = StructuredTool(
    name="extract_coupons_from_text",
    func=extract_coupons_from_text_tool_func,
    description="Given a list of  objects includingextracted texts, attempt to extract coupon codes (like SAVE10). Returns a list(array) of coupon codes.",
    args_schema=ExtractCouponsFromTextInputTool
)

extract_form_fields_tool = StructuredTool(
    name="extract_form_fields",
    func=extract_form_fields_tool_func,
    description="Use LLM to analyze HTML and find coupon input field and apply button. Returns JSON with detailed information about the found elements.",
    args_schema=ExtractFormFieldsInputTool
)

search_coupons_from_web_tool = StructuredTool(
    name="search_coupons_from_web",
    func=search_coupons_from_web_func,
    description="Search coupons from well known coupon website sources. Returns a JSON string containing an array of coupon objects.",
    args_schema=SearchCouponsFromWebInputTool
)

clean_html_tool = StructuredTool(
    name="clean_html",
    func=clean_html_tool_func,
    description="Clean HTML by removing specified tags (e.g., style, script, svg). Returns the cleaned HTML string.",
    args_schema=CleanHtmlInputTool
)

all_tools = [
    scrape_some_images_from_website_tool,
    extract_text_from_images_tool,
    extract_coupons_from_text_tool,
    extract_form_fields_tool,
    search_coupons_from_web_tool,
    clean_html_tool
]
