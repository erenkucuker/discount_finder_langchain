from langchain.prompts import PromptTemplate, ChatPromptTemplate
from discount_finder_langchain.schemas import CouponCode, AnalyzeResponse, CouponCodeList
from langchain_core.output_parsers import PydanticOutputParser


# PARSERS
PARSER_COUPON_CODE = PydanticOutputParser(pydantic_object=CouponCode)
PARSER_COUPON_CODE_LIST = PydanticOutputParser(pydantic_object=CouponCodeList)
PARSER_ANALYZE_URL = PydanticOutputParser(pydantic_object=AnalyzeResponse)


# PROMPTS


SYSTEM_PROMPT = (
    "Let's first understand the problem and devise a plan to solve the problem."
    " Please output the plan starting with the header 'Plan:' "
    "and then followed by a numbered list of steps. "
    "Please make the plan the minimum number of steps required "
    "to accurately complete the task. If the task is a question, "
    "the final step should almost always be 'Given the above steps taken, "
    "please respond to the users original question'. "
    "If you tried all but achieved results, finish your task with saying '<END_OF_PLAN>'."
    "At the end of your plan, say '<END_OF_PLAN>'"
)

MAIN_PROMPT = """You are a shopping assistant agent with various tools.
Your main goal is to help the user find the best deals and coupons for their shopping needs.

IMPORTANT:
- Ensure you are providing all the output from previous steps to the next step.
"""


EXTRACT_COUPONS_FROM_TEXT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are an expert at finding coupon codes in text.
You will be given text to analyze for potential coupon codes.
A valid coupon code is typically:
- Alphanumeric(e.g., SAVE10, DISCOUNT2023)
- Between 4-15 characters
- Often includes numbers
- Usually all uppercase
- May include hyphens or underscores
- Often contains words like SAVE, OFF, DISCOUNT

Your task is to extract any valid coupon codes from the text.
If no valid coupon codes are found, return an empty list.

Input text:
---
{text}
---

Return a list of coupon codes in this format:
{format_instructions}

Important:
- Only return coupon codes that match the format described above
- If no valid coupon codes are found, return an empty list
- Do not make up or guess coupon codes
- Do not include promotional text or descriptions that look like codes
- Ensure the source field indicates where the code was found
"""),
    ("human", "{text}")
]).partial(format_instructions=PARSER_COUPON_CODE_LIST.get_format_instructions())

EXTRACT_FORM_FIELDS_PROMPT = PromptTemplate.from_template(
    '''You are an expert at analyzing HTML to find coupon-related form elements.

Analyze this HTML and find:
1. The input field used for entering coupon/promo/discount codes
2. The button that applies/submits the coupon code

Return ONLY a JSON

HTML to analyze:
{html}

Important:
- Return ONLY the JSON object, no other text
- Use null for missing elements or attributes
- Ensure all JSON keys and values are properly quoted
- Make sure the JSON is properly formatted and valid
- Do not include any explanatory text before or after the JSON'''
)
