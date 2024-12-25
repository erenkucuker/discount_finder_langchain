from fastapi import APIRouter
from discount_finder_langchain.schemas import (
    UrlAnalyzeRequest,
    HtmlAnalyzeRequest,
    AnalyzeResponse,
    FormAnalyzeResponse
)
from discount_finder_langchain.services import analyze_service, analyze_form_service
router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(request: UrlAnalyzeRequest) -> AnalyzeResponse:

    response, _ = await analyze_service(request)
    return response


@router.post("/analyze_form", response_model=FormAnalyzeResponse)
async def analyze_form_endpoint(request: HtmlAnalyzeRequest) -> FormAnalyzeResponse:
    response, _ = await analyze_form_service(request)
    return response
