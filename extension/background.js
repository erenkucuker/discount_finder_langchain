import './libs/browser-polyfill.js';

// Debouncing mechanism
const pendingAnalysis = new Map();
const analyzedDomains = new Set();

// Cache mechanism
const CACHE_DURATION = 24 * 60 * 60 * 1000; // 1 day in milliseconds

// Extract domain from URL
function extractDomain(url) {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname;
  } catch (e) {
    console.error('Invalid URL:', url);
    return null;
  }
}

// Check if domain was recently analyzed
function isDomainAnalyzed(url) {
  const domain = extractDomain(url);
  return domain ? analyzedDomains.has(domain) : false;
}

// Mark domain as analyzed
function markDomainAnalyzed(url) {
  const domain = extractDomain(url);
  if (domain) {
    analyzedDomains.add(domain);
    // Clear the analyzed status after cache duration
    setTimeout(() => {
      analyzedDomains.delete(domain);
    }, CACHE_DURATION);
  }
}

async function getCachedResponse(url, type) {
  const domain = extractDomain(url);
  if (!domain) return null;

  const cacheKey = `${type}_${domain}`;
  const cached = await browser.storage.local.get(cacheKey);

  if (cached[cacheKey]) {
    const { data, timestamp } = cached[cacheKey];
    if (Date.now() - timestamp < CACHE_DURATION) {
      console.log(`Using cached ${type} response for domain: ${domain}`);
      return data;
    }
    // Cache expired, remove it
    await browser.storage.local.remove(cacheKey);
    analyzedDomains.delete(domain);
  }
  return null;
}

async function setCachedResponse(url, type, data) {
  const domain = extractDomain(url);
  if (!domain) return;

  const cacheKey = `${type}_${domain}`;
  await browser.storage.local.set({
    [cacheKey]: {
      data,
      timestamp: Date.now()
    }
  });
}

async function clearDomainCache(url) {
  const domain = extractDomain(url);
  if (!domain) return;

  const keys = ['page', 'form', 'coupons'].map(type => `${type}_${domain}`);
  await browser.storage.local.remove(keys);
  console.log(`Cleared cache for domain: ${domain}`);
}

// Store coupons for specific domain
async function storeDomainCoupons(url, coupons) {
  const domain = extractDomain(url);
  if (!domain) return;

  const cacheKey = `coupons_${domain}`;
  await browser.storage.local.set({
    [cacheKey]: {
      coupons,
      timestamp: Date.now(),
      url: url
    }
  });
}

// Get coupons for specific domain
async function getDomainCoupons(url) {
  const domain = extractDomain(url);
  if (!domain) return null;

  const cacheKey = `coupons_${domain}`;
  const cached = await browser.storage.local.get(cacheKey);

  if (cached[cacheKey]) {
    const { coupons, timestamp } = cached[cacheKey];
    if (Date.now() - timestamp < CACHE_DURATION) {
      return coupons;
    }
    await browser.storage.local.remove(cacheKey);
  }
  return null;
}

function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

const API_BASE_URL = 'http://localhost:8000';
const ECOMMERCE_PATTERNS = [
  'checkout',
  'cart',
  'basket',
  'shop',
  'store',
  'product',
  'item',
  'buy',
  'purchase',
  'amazon',
  'ebay',
  'walmart',
  'target',
  'bestbuy',
  'costco',
  'shopify',
];

// Check if URL matches ecommerce patterns
function isEcommerceUrl(url) {
  const urlLower = url.toLowerCase();
  return ECOMMERCE_PATTERNS.some(pattern => urlLower.includes(pattern));
}

// Check if URL is a checkout page
function isCheckoutPage(url) {
  const urlLower = url.toLowerCase();
  return urlLower.includes('checkout') || urlLower.includes('payment');
}

function isCartPage(url) {
  const urlLower = url.toLowerCase();
  return urlLower.includes('cart') || urlLower.includes('basket');
}

// Analyze URL for coupons
async function analyzePage(url) {
  try {
    const domain = extractDomain(url);
    if (!domain) return { coupons: [] };

    // Check if domain was already analyzed
    if (isDomainAnalyzed(url)) {
      console.log(`Domain ${domain} was already analyzed, skipping API call`);
      const cachedCoupons = await getDomainCoupons(url);
      return { coupons: cachedCoupons || [] };
    }

    // Check cache first
    const cachedResponse = await getCachedResponse(url, 'page');
    if (cachedResponse) {
      markDomainAnalyzed(url);
      return cachedResponse;
    }

    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ url })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    const formattedResult = {
      coupons: Array.isArray(result.coupons) ? result.coupons : []
    };

    // Cache the response and store domain coupons
    await setCachedResponse(url, 'page', formattedResult);
    if (formattedResult.coupons.length > 0) {
      await storeDomainCoupons(url, formattedResult.coupons);
    }

    markDomainAnalyzed(url);
    return formattedResult;
  } catch (error) {
    console.error('Error analyzing page:', error);
    return { coupons: [] };
  }
}

// Analyze form fields
async function analyzeForm(html, url) {
  try {
    const domain = extractDomain(url);
    if (!domain) throw new Error('Invalid URL');

    // Check cache first
    const cachedResponse = await getCachedResponse(url, 'form');
    if (cachedResponse) {
      return cachedResponse;
    }

    const response = await fetch(`${API_BASE_URL}/analyze_form`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ html_page: html })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    if (!result.form_fields?.coupon_input?.css_path || !result.form_fields?.apply_button?.css_path) {
      throw new Error('Invalid form fields response format');
    }

    // Cache the response
    await setCachedResponse(url, 'form', result);

    return result;
  } catch (error) {
    console.error('Error analyzing form:', error);
    throw error;
  }
}

// Debounced version of analyzePage
const debouncedAnalyzePage = debounce(async (url, tabId) => {
  const domain = extractDomain(url);
  if (!domain) return;

  // Check if there's already a pending analysis for this domain
  if (pendingAnalysis.has(domain)) {
    return;
  }

  try {
    pendingAnalysis.set(domain, true);
    const result = await analyzePage(url);
    pendingAnalysis.delete(domain);

    if (result.coupons && result.coupons.length > 0) {
      // Only show notification on cart or checkout pages
      if (isCheckoutPage(url) || isCartPage(url)) {
        await browser.tabs.sendMessage(tabId, {
          type: 'SHOW_COUPON_NOTIFICATION',
          coupons: result.coupons
        });
      }
    }
  } catch (error) {
    pendingAnalysis.delete(domain);
    console.error('Error in debounced analyzePage:', error);
  }
}, 1000);

// Listen for tab updates
browser.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    if (isEcommerceUrl(tab.url)) {
      // Use the debounced version
      debouncedAnalyzePage(tab.url, tabId);
    }
  }
});

// Listen for messages from content script and popup
browser.runtime.onMessage.addListener(async (message, sender) => {
  if (message.type === 'ANALYZE_FORM') {
    try {
      const result = await analyzeForm(message.html, sender.tab.url);
      return result;
    } catch (error) {
      console.error('Error analyzing form:', error);
      throw error;
    }
  } else if (message.type === 'CLEAR_CACHE') {
    const domain = extractDomain(message.url);
    if (domain) {
      analyzedDomains.delete(domain);
    }
    await clearDomainCache(message.url);
    return { success: true };
  } else if (message.type === 'GET_DOMAIN_COUPONS') {
    const coupons = await getDomainCoupons(message.url);
    return { coupons };
  }
});
