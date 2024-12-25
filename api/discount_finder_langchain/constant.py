
# Coupon code patterns
CODE_PATTERNS = [
    r'code[:\s]+([A-Z0-9-_]+)',
    r'coupon[:\s]+([A-Z0-9-_]+)',
    r'promo[:\s]+([A-Z0-9-_]+)',
    r'\b([A-Z0-9]{4,15})\b'
]


# Coupon element selectors
COUPON_SELECTORS = [
    'div[class*="coupon"]',
    'div[class*="promo"]',
    'div[class*="offer"]',
    'div[class*="deal"]',
    'div[class*="discount"]',
    'div[class*="code"]',
    '[data-coupon]',
    '[data-promo]'
]

# Coupon data attributes
COUPON_ATTRIBUTES = ['data-coupon', 'data-code', 'data-promo']

# Coupon sites template URLs
COUPON_SITES = [
    "https://www.retailmenot.com/view/{merchant_name}",
    "https://www.promocodes.com/{merchant_name}",
    "https://www.coupons.com/brands/{merchant_name}",
    "https://www.offers.com/{merchant_name}",
]

# Request headers
USER_AGENT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Image filtering constants
MIN_IMAGE_WIDTH = 200  # pixels
MIN_IMAGE_HEIGHT = 200  # pixels


# OCR constants
OCR_LANGUAGES = ['en']
OCR_CONFIDENCE_THRESHOLD = 0.7


# Description length limit
MAX_DESCRIPTION_LENGTH = 100

# Regex patterns
VALID_COUPON_CODE_PATTERN = r'^[A-Z0-9-_]{4,15}$'

# Request timeouts
SCRAPE_TIMEOUT = 30  # seconds
HEAD_REQUEST_TIMEOUT = 5  # seconds
COUPON_SEARCH_TIMEOUT = 10  # seconds
