let toastContainer = null;
let currentPrice = null;
let appliedCoupons = new Set();

// Create toast container
function createToastContainer() {
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.className = 'toast-container';
    document.body.appendChild(toastContainer);
  }
  return toastContainer;
}

// Create toast notification
function createToast({ title, message, type = 'info', actions = [] }) {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const content = document.createElement('div');
  content.className = 'toast-content';

  const titleEl = document.createElement('div');
  titleEl.className = 'toast-title';
  titleEl.textContent = title;
  content.appendChild(titleEl);

  const messageEl = document.createElement('div');
  messageEl.className = 'toast-message';
  messageEl.textContent = message;
  content.appendChild(messageEl);

  if (actions.length > 0) {
    const actionsContainer = document.createElement('div');
    actionsContainer.className = 'toast-actions';

    actions.forEach(action => {
      const button = document.createElement('button');
      button.className = `toast-button ${action.primary ? 'primary' : 'secondary'}`;
      button.textContent = action.text;
      button.onclick = () => {
        action.onClick();
        removeToast(toast);
      };
      actionsContainer.appendChild(button);
    });

    content.appendChild(actionsContainer);
  }

  const closeButton = document.createElement('button');
  closeButton.className = 'toast-close';
  closeButton.innerHTML = '×';
  closeButton.onclick = () => removeToast(toast);

  toast.appendChild(content);
  toast.appendChild(closeButton);

  createToastContainer().appendChild(toast);

  // Auto remove after 10 seconds if no actions
  if (actions.length === 0) {
    setTimeout(() => removeToast(toast), 10000);
  }

  return toast;
}

// Remove toast notification
function removeToast(toast) {
  toast.style.animation = 'slideOut 0.3s ease-out forwards';
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 300);
}

// Get current price from page
function getCurrentPrice() {
  // Common price selectors with total keyword
  const priceSelectors = [
    '[data-testid*="total"]',
    '[class*="total"]',
    '[id*="total"]',
    '[data-testid*="price"]',
    '[class*="price"]',
    '[id*="price"]',
    'span:contains("Total")',
    'div:contains("Total")',
    'p:contains("Total")',
    'label:contains("Total")',
    '.cart-total',
    '.order-total',
    '.subtotal',
    '.grand-total',
    '#orderTotal',
    '#cartTotal'
  ];

  for (const selector of priceSelectors) {
    const elements = document.querySelectorAll(selector);
    for (const element of elements) {
      // Get text content and any nested text
      const text = element.textContent.trim();

      // Look for price patterns: $X, $X.XX, $X,XXX.XX
      const priceMatches = text.match(/\$\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?/g);
      if (priceMatches) {
        // Get the last match as it's more likely to be the total
        const priceStr = priceMatches[priceMatches.length - 1];
        // Remove $ and commas, then convert to float
        return parseFloat(priceStr.replace(/[$,]/g, ''));
      }

      // Alternative pattern: X.XX $, X,XXX.XX $
      const altPriceMatches = text.match(/\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*\$/g);
      if (altPriceMatches) {
        const priceStr = altPriceMatches[altPriceMatches.length - 1];
        return parseFloat(priceStr.replace(/[$,]/g, ''));
      }
    }
  }

  // If no price found with selectors, try searching all text for price patterns
  const allText = document.body.textContent;
  const totalPattern = /total\s*(?::|is|:is)?\s*\$?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?/i;
  const match = allText.match(totalPattern);
  if (match) {
    const priceMatch = match[0].match(/\d{1,3}(?:,\d{3})*(?:\.\d{2})?/);
    if (priceMatch) {
      return parseFloat(priceMatch[0].replace(/,/g, ''));
    }
  }

  return null;
}

// Apply coupon code
async function applyCoupon(code, inputSelector, buttonSelector) {


  console.log('Applying coupon:', code, inputSelector, buttonSelector);
  try {
    // Find input field and button
    const input = document.querySelector(inputSelector);
    const button = document.querySelector(buttonSelector);

    if (!input || !button) {
      throw new Error('Could not find coupon input or button');
    }

    // Store current price
    const beforePrice = getCurrentPrice();
    if (!beforePrice) {
      throw new Error('Could not determine current price');
    }

    // Focus the input
    input.focus();

    // Clear existing value
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'a', ctrlKey: true }));
    input.dispatchEvent(new KeyboardEvent('keyup', { key: 'a', ctrlKey: true }));
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Backspace' }));
    input.dispatchEvent(new KeyboardEvent('keyup', { key: 'Backspace' }));

    // Type the code character by character
    for (const char of code) {
      input.dispatchEvent(new KeyboardEvent('keydown', { key: char }));
      input.value = input.value + char; // Need to update value as keyboard events don't
      input.dispatchEvent(new KeyboardEvent('keypress', { key: char }));
      input.dispatchEvent(new KeyboardEvent('keyup', { key: char }));
      input.dispatchEvent(new Event('input', { bubbles: true }));
      await new Promise(resolve => setTimeout(resolve, 50)); // Small delay between keystrokes
    }

    // Trigger change event after typing
    input.dispatchEvent(new Event('change', { bubbles: true }));

    // Press Enter key
    input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter' }));
    input.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter' }));

    // If Enter doesn't work, click the button
    setTimeout(() => {
      button.click();
    }, 500);

    // Wait for price update
    await new Promise(resolve => setTimeout(resolve, 2000));


    return false;
  } catch (error) {
    console.error('Error applying coupon:', error);
    return false;
  }
}

// Try all coupons
async function tryAllCoupons(coupons, formFields) {
  let appliedAny = false;

  for (const coupon of coupons) {
    const success = await applyCoupon(
      coupon.code,
      formFields.coupon_input.css_path,
      formFields.apply_button.css_path
    );

    if (success) {
      appliedAny = true;
      break;
    }
    console.log('ccc')
  }

  if (!appliedAny) {
    createToast({
      title: 'No Valid Coupons',
      message: 'Sorry, none of the coupons worked.',
      type: 'error'
    });
  }
}

// Debouncing mechanism
const pendingFormAnalysis = new Map();

// Create a safe hash from string that handles Unicode characters
function createSafeHash(str) {
  try {
    // Convert string to UTF-8 bytes
    const encoder = new TextEncoder();
    const data = encoder.encode(str);

    // Create a simple hash
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      hash = ((hash << 5) - hash) + data[i];
      hash = hash & hash; // Convert to 32-bit integer
    }
    return hash.toString(36); // Convert to base36 for shorter string
  } catch (e) {
    console.error('Error creating hash:', e);
    return Date.now().toString(36); // Fallback to timestamp if error
  }
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

// Clean HTML content
function cleanHtml(html) {
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = html;

  // Remove script and style tags
  const scripts = tempDiv.getElementsByTagName('script');
  const styles = tempDiv.getElementsByTagName('style');
  const iframes = tempDiv.getElementsByTagName('iframe');
  const svgs = tempDiv.getElementsByTagName('svg');

  while (scripts.length > 0) {
    scripts[0].parentNode.removeChild(scripts[0]);
  }
  while (styles.length > 0) {
    styles[0].parentNode.removeChild(styles[0]);
  }
  while (iframes.length > 0) {
    iframes[0].parentNode.removeChild(iframes[0]);
  }
  while (svgs.length > 0) {
    svgs[0].parentNode.removeChild(svgs[0]);
  }

  return tempDiv.innerHTML;
}

// Debounced version of form analysis
const debouncedAnalyzeForm = debounce(async (html, coupons) => {
  // Create a hash of the HTML content
  const htmlHash = createSafeHash(html.slice(0, 1000)); // Use first 1000 chars for hash

  // Check if there's already a pending analysis for this HTML
  if (pendingFormAnalysis.has(htmlHash)) {
    return;
  }

  try {
    pendingFormAnalysis.set(htmlHash, true);
    const formFields = await browser.runtime.sendMessage({
      type: 'ANALYZE_FORM',
      html: cleanHtml(html) // Clean HTML before sending
    });
    pendingFormAnalysis.delete(htmlHash);

    if (formFields.form_fields) {
      await tryAllCoupons(coupons, formFields.form_fields);
    } else {
      createToast({
        title: 'Error',
        message: 'Could not find coupon form fields.',
        type: 'error'
      });
    }
  } catch (error) {
    pendingFormAnalysis.delete(htmlHash);
    console.error('Error in form analysis:', error);
    createToast({
      title: 'Error',
      message: 'An error occurred while analyzing the form.',
      type: 'error'
    });
  }
}, 1000);

// Handle coupon notification
function handleCouponNotification(coupons) {
  createToast({
    title: 'Coupons Found!',
    message: `Found ${coupons.length} potential coupon${coupons.length === 1 ? '' : 's'}. Would you like to try them?`,
    type: 'info',
    actions: [
      {
        text: 'Yes, try coupons',
        primary: true,
        onClick: async () => {
          const html = document.documentElement.outerHTML;
          debouncedAnalyzeForm(html, coupons);
        }
      },
      {
        text: 'No, thanks',
        primary: false,
        onClick: () => { }
      }
    ]
  });
}

// Listen for messages from background script
browser.runtime.onMessage.addListener((message) => {
  if (message.type === 'SHOW_COUPON_NOTIFICATION') {
    handleCouponNotification(message.coupons);
  }
});
