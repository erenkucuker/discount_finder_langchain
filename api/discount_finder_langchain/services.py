from discount_finder_langchain.schemas import (
    UrlAnalyzeRequest,
    HtmlAnalyzeRequest,
    AnalyzeResponse,
    FormAnalyzeResponse,
    FormFields,
    FormField,
    FormButton
)

from discount_finder_langchain.agent import create_new_discount_finder_agent
from typing import Tuple
from discount_finder_langchain.utils import parse_agent_response, vprint
import json
import traceback


async def analyze_service(request: UrlAnalyzeRequest) -> Tuple[AnalyzeResponse, str | None]:
    """Returns (response, error)"""
    try:
        agent = create_new_discount_finder_agent()
        vprint(f"🔍 Analyzing URL: {request.clean_url}")
        resp = agent.invoke(
            [
                {"objective": "find coupons from provided website's homepage or try to find them from well-known coupon websites"},
                {"input": f"url: {request.clean_url}"},
                {"output_format":
                    "Return ONLY a JSON string in this exact format: { \"coupons\": [{ \"code\": \"EXAMPLE\", \"source\": \"Source\" }] }"}
            ]
        )

        vprint(f"🤖 Raw agent response: {resp}")

        # Try to extract the JSON string from the response
        output = resp
        if isinstance(output, dict):
            if "output" in output:
                output = output["output"]
            if isinstance(output, dict) and "action_input" in output:
                output = output["action_input"]

        # Convert dict to string if necessary
        if isinstance(output, dict):

            output = json.dumps(output)

        # Parse the JSON string
        try:
            data = json.loads(output)
            coupons = data.get("coupons", [])
            vprint(f"🤖 Parsed coupons: {coupons}")
            return AnalyzeResponse(coupons=coupons), None
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse JSON response: {str(e)}"
            vprint(error_msg)
            return AnalyzeResponse(coupons=[]), error_msg

    except Exception as e:

        error_msg = f"Error analyzing URL: {str(e)}\n{traceback.format_exc()}"
        vprint(error_msg)
        return AnalyzeResponse(coupons=[]), error_msg


async def analyze_form_service(request: HtmlAnalyzeRequest) -> Tuple[FormAnalyzeResponse, str | None]:
    """Returns(response, error)"""
    try:
        agent = create_new_discount_finder_agent()
        resp = agent.invoke(
            [
                {"objective": f"finding coupon form field and button from provided html page after cleaning style script svg iframe like html tags and other non-relevant elements"},
                {"input": f"html: {request.html_page}"},
                {"output_format":
                    "Return ONLY a JSON string in this exact format: { \"form_fields\": { \"coupon_input\": { \"css_path\": \"EXAMPLE\" }, \"apply_button\": { \"css_path\": \"EXAMPLE\" } } }"}
            ]
        )

        data, error = parse_agent_response(resp)
        if error:
            return FormAnalyzeResponse(form_fields=None), error

        form_fields = FormFields(
            coupon_input=FormField(css_path=data.get("form_fields", {}).get("coupon_input", {}).get(
                "css_path")) if data.get("form_fields", {}).get("coupon_input") else None,
            apply_button=FormButton(css_path=data.get("form_fields", {}).get("apply_button", {}).get(
                "css_path")) if data.get("form_fields", {}).get("apply_button") else None
        )

        return FormAnalyzeResponse(form_fields=form_fields), None

    except Exception as e:
        return FormAnalyzeResponse(form_fields=None), str(e)
