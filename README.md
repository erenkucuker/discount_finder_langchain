# 🛍️ AI Shopping Assistant & Coupon Finder Agent

> ⚠️ *Important Notice*: This project is not intended for production use.




## 📋 Overview
It uses Plan & Execute Agent Architecture. Specifically chosen for handling complex task like finding coupons without losing the context.

![llm-compiler](https://blog.langchain.dev/content/images/size/w1600/2024/02/llm-compiler-1.png)


## 📝 Criticism & Limitations
- For production use case there would be many programmatic tools before using LLM solutions to decrease the cost of usage.
- Instead of using and agent a chain would work better.


## 🛠️ Tech Stack

### 🔧 Backend

The backend uses:
- ⚡ FastAPI
- 🔗 LangChain
- 🤖 OpenAI's GPT models
- 👁️ EasyOCR
- 🌐 BeautifulSoup4

### 🎯 Extension

The Chrome extension uses:
- 💻 JavaScript (no framework)
- 🔄 Webextension-Polyfill for All Browsers

## 📖 Usage

### 🎯 Basic Usage

1. **🔄 Automatic Detection**
   - Visit any e-commerce website
   - The extension automatically detects shopping-related pages
   - Works on popular platforms like Amazon, eBay, Walmart, and many others

2. **🔍 Finding Coupons**
   - When you're on a cart or checkout page, the extension will:
     - Automatically search for available coupons
     - Show a notification if coupons are found
     - Display the number of available coupons

3. **💳 Applying Coupons**
   - Click "Yes, try coupons" in the notification
   - The extension will:
     - Automatically locate the coupon input field
     - Test each coupon code sequentially
     - Stop when it finds a working coupon
     - Show results via toast notifications

## 🚀 Installation

### 🔧 Backend API Setup

1. Clone the repository:
```bash
git clone https://github.com/erenkucuker/discount_finder_langchain.git
cd discount_finder_langchain/api
```

2. Install dependencies:
```bash
poetry install
```

3. Create a `.env` file in the `api` directory:
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

4. Start the API server:
```bash
cd api
poetry run dev
```

### 🌐 Chrome Extension Setup

1. Load the extension in Chrome:
   - Open Chrome and go to `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `extension` directory



## 📁 Project Structure

```
discount_finder_langchain/
├── api/                          # Backend API directory
│   ├── discount_finder_langchain/
│   │   ├── agent.py             # AI agent implementation
│   │   ├── config.py            # Configuration settings
│   │   ├── prompts.py           # LLM prompts
│   │   ├── routes.py            # API endpoints
│   │   ├── schemas.py           # Data models
│   │   ├── services.py          # Business logic
│   │   └── tools.py             # Agent tools
│   ├── pyproject.toml           # Python dependencies
├── extension/                    # Browser extension
│   ├── manifest.json            # Extension config
│   ├── popup.html               # Extension popup
│   ├── popup.js                 # Popup logic
│   ├── content.js               # Page interaction
│   └── background.js            # Background processes
└── README.md                    # Documentation
```


## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
