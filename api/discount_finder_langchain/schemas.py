from pydantic import BaseModel, Field
from typing import List, Optional
from urllib.parse import urlparse, unquote


class UrlAnalyzeRequest(BaseModel):
    url: str = Field(
        description="The URL to analyze for coupon codes and discounts")

    @property
    def clean_url(self) -> str:
        cleaned = self.url.strip().strip('"\'')
        cleaned = unquote(cleaned)
        parsed = urlparse(cleaned)
        if not parsed.scheme:
            cleaned = 'https://' + cleaned
        return cleaned


class HtmlAnalyzeRequest(BaseModel):
    html_page: str = Field(
        description="Raw HTML content to analyze for coupon form fields")


class CouponCode(BaseModel):
    """Represents a single coupon code with its details"""
    code: str = Field(description="The actual coupon code string")
    source: str = Field(
        description="Where the coupon code was found or sourced from")


class CouponCodeList(BaseModel):
    """Represents a list of coupon codes"""
    coupons: List[CouponCode] = Field(
        description="List of coupon codes with their details")


class FormField(BaseModel):
    """Represents a form field element found in HTML"""
    css_path: str = Field(
        description="CSS selector path to locate the form field")


class FormButton(BaseModel):
    """Represents a button element found in HTML"""
    css_path: str = Field(description="CSS selector path to locate the button")


class FormFields(BaseModel):
    """Represents the coupon form fields found in HTML"""
    coupon_input: Optional[FormField] = Field(
        default=None, description="Input field for entering coupon codes")
    apply_button: Optional[FormButton] = Field(
        default=None, description="Button to submit/apply the coupon code")


class FormAnalyzeResponse(BaseModel):
    """Response model for form analysis endpoint"""
    form_fields: Optional[FormFields] = Field(
        default=None, description="Details of found coupon form fields")


class AnalyzeResponse(BaseModel):
    """Response model for URL analysis endpoint"""
    coupons: Optional[List[CouponCode]] = Field(
        default=[], description="List of found coupon codes and their details")


class ExtractCouponsFromTextInputTool(BaseModel):
    extracted_texts: List[object] = Field(
        description="list of extracted objects including texts to analyze for coupon codes")


class ScrapeSomeImagesFromWebsiteInputTool(BaseModel):
    url: str = Field(description="The URL to scrape for coupon codes")


class ExtractTextFromImagesInputTool(BaseModel):
    images: List[str] = Field(
        description="The list of images to analyze for coupon codes")


class ExtractFormFieldsInputTool(BaseModel):
    html: str = Field(
        description="The HTML content to analyze for coupon codes")


class SearchCouponsFromWebInputTool(BaseModel):
    merchant_name: str = Field(
        description="The merchant name to search for coupon codes if url was https://www.amazon.com/ then merchant_name is amazon dont use space or special characters for merchant_name")


class CleanHtmlInputTool(BaseModel):
    """Input schema for HTML cleaning tool"""
    html: str = Field(description="The HTML content to clean")
    tags_to_remove: List[str] = Field(
        description="List of HTML tags to remove (e.g., ['style', 'script', 'svg'])")
