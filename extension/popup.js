// Get current tab URL
async function getCurrentTab() {
  const tabs = await browser.tabs.query({ active: true, currentWindow: true });
  return tabs[0];
}

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

// Update UI with coupons
function updateCouponList(coupons) {
  const couponList = document.querySelector('.coupon-list');

  if (!coupons || coupons.length === 0) {
    couponList.innerHTML = '<div class="no-coupons">No coupons found for this website.</div>';
    return;
  }

  couponList.innerHTML = coupons.map(coupon => `
    <div class="coupon-item">
      <div class="coupon-code">${coupon.code}</div>
      <div class="coupon-source">Source: ${coupon.source}</div>
    </div>
  `).join('');
}

// Initialize popup
async function initPopup() {
  try {
    const currentTab = await getCurrentTab();
    const domain = extractDomain(currentTab.url);

    if (!domain) {
      document.querySelector('.domain-info').textContent = 'Invalid URL';
      updateCouponList(null);
      return;
    }

    document.querySelector('.domain-info').textContent = `Coupons for ${domain}`;

    // Get domain-specific coupons
    const response = await browser.runtime.sendMessage({
      type: 'GET_DOMAIN_COUPONS',
      url: currentTab.url
    });

    updateCouponList(response.coupons);

    // Setup clear cache button
    document.querySelector('.clear-cache').addEventListener('click', async () => {
      await browser.runtime.sendMessage({
        type: 'CLEAR_CACHE',
        url: currentTab.url
      });

      // Show success message
      document.querySelector('.domain-info').textContent = `Cache cleared for ${domain}`;
      updateCouponList(null);
    });

  } catch (error) {
    console.error('Error initializing popup:', error);
    document.querySelector('.domain-info').textContent = 'Error loading coupons';
    updateCouponList(null);
  }
}

// Initialize when popup opens
document.addEventListener('DOMContentLoaded', initPopup);
