from langchain_experimental.plan_and_execute.executors.base import ChainExecutor
from langchain.agents.agent import AgentExecutor
from langchain.agents.structured_chat.base import StructuredChatAgent
from discount_finder_langchain.prompts import MAIN_PROMPT
import requests
import cv2
import numpy as np
from typing import List, Dict, Optional, Any
import json
import re
from urllib.parse import urlparse
from discount_finder_langchain.constant import (
    USER_AGENT_HEADERS,
    MIN_IMAGE_WIDTH,
    MIN_IMAGE_HEIGHT,
    SCRAPE_TIMEOUT,
    OCR_CONFIDENCE_THRESHOLD,
    VALID_COUPON_CODE_PATTERN,
    MAX_DESCRIPTION_LENGTH
)
from discount_finder_langchain.config import config


def vprint(message: str) -> None:
    """Print message only if verbose mode is enabled"""
    if config.verbose:
        print(message)


def create_agent_executor(llm, tools, verbose=True, include_task_in_prompt=True):
    input_variables = ["previous_steps", "current_step", "agent_scratchpad"]
    HUMAN_MESSAGE_TEMPLATE = """Previous steps: {previous_steps}

    Current objective: {current_step}

    {agent_scratchpad}"""

    TASK_PREFIX = """{objective}

    """

    template = HUMAN_MESSAGE_TEMPLATE

    if include_task_in_prompt:
        input_variables.append("objective")
        template = TASK_PREFIX + template

    agent = StructuredChatAgent.from_llm_and_tools(
        llm,
        tools,
        human_message_template=template,
        prefix=MAIN_PROMPT,
        input_variables=input_variables,

    )
    agent_executor = AgentExecutor.from_agent_and_tools(
        agent=agent, tools=tools, verbose=verbose,
    )
    return ChainExecutor(chain=agent_executor)


def fetch_url_content(url: str, timeout: int = SCRAPE_TIMEOUT) -> Optional[str]:
    """Fetch content from a URL with error handling."""
    try:
        response = requests.get(
            url, headers=USER_AGENT_HEADERS, timeout=timeout)
        response.raise_for_status()
        return response.text
    except Exception as e:
        vprint(f"❌ Error fetching URL {url}: {str(e)}")
        return None


def process_image_for_ocr(image_content: bytes) -> Optional[np.ndarray]:
    """Process image bytes into a format suitable for OCR."""
    try:
        nparr = np.frombuffer(image_content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        enhanced = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        return enhanced
    except Exception as e:
        vprint(f"❌ Error processing image: {str(e)}")
        return None


def filter_image_by_size(img_tag: Any, base_url: str) -> Optional[str]:
    """Filter and process image tags based on size requirements."""
    try:
        src = img_tag.get('src', '') or img_tag.get(
            'data-src', '') or img_tag.get('data-lazy-src', '')
        if not src or not src.strip() or src.startswith('data:'):
            return None

        # Handle relative URLs
        if src.startswith('//'):
            src = 'https:' + src
        elif src.startswith('/'):
            src = f'https://{base_url}{src}'
        elif not src.startswith(('http://', 'https://')):
            src = f'https://{base_url}/{src}'

        width = img_tag.get('width', '').strip(
            'px') or img_tag.get('data-width', '').strip('px')
        height = img_tag.get('height', '').strip(
            'px') or img_tag.get('data-height', '').strip('px')

        if width and height:
            try:
                if int(width) < MIN_IMAGE_WIDTH or int(height) < MIN_IMAGE_HEIGHT:
                    return None
            except ValueError:
                pass

        return src
    except Exception as e:
        vprint(f"⚠️ Error processing image tag: {str(e)}")
        return None


def extract_base_url(url: str) -> Optional[str]:
    """Extract base URL from a given URL."""
    try:
        parsed_url = urlparse(url)
        base_url = parsed_url.netloc
        return base_url if base_url else None
    except Exception as e:
        vprint(f"⚠️ Error extracting base URL: {str(e)}")
        return None


def process_ocr_detection(detection: List[Any]) -> Optional[Dict[str, Any]]:
    """Process OCR detection results."""
    try:
        text = detection[1]
        confidence = detection[2]
        if confidence > OCR_CONFIDENCE_THRESHOLD:
            return {
                "text": text,
                "confidence": confidence
            }
        return None
    except Exception as e:
        vprint(f"❌ Error processing OCR detection: {str(e)}")
        return None


def validate_coupon_code(code: str) -> bool:
    """Validate a coupon code against the defined pattern."""
    if not code:
        return False
    return bool(re.match(VALID_COUPON_CODE_PATTERN, code.strip(), re.I))


def clean_description(description: str) -> str:
    """Clean and truncate description text."""
    if not description:
        return ""
    return description.strip()[:MAX_DESCRIPTION_LENGTH]


def parse_agent_response(response: Any) -> tuple[Any, str]:
    """Parse agent response and handle different formats."""
    if isinstance(response, dict):
        output = response.get("output", "")
    else:
        output = str(response)

    try:
        if isinstance(output, str):
            data = json.loads(output)
        else:
            data = output
        return data, None
    except Exception as e:
        return None, str(e)
