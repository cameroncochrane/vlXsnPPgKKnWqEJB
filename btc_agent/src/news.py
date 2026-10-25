# Here the logic regarding fetching bitcoin/financial/world news will be placed:

# Base imports:
import logging
import os
import requests
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def fetch_news_articles(
    api_token=None,
    query='(bitcoin OR btc) OR ("cryptocurrency" AND (regulation OR "federal reserve" OR fed OR inflation OR sec))',
    params=None,
):
    """Fetch recent bitcoin and macro-market news articles from NewsAPI."""
    # 1. Define your API Key and endpoint
    # SENSITIVE: API key read from the environment; curly/straight quotes and whitespace are stripped (pasted keys often include them)
    api_key = (api_token or os.environ.get("NEWS_API_KEY", "")).strip().strip("\"'“”‘’").strip()
    if not api_key:
        logger.error("NEWS_API_KEY is not set, so news can't be fetched.")
        raise SystemExit("NEWS_API_KEY is not set. Run: export NEWS_API_KEY=your_key (no quotes needed).")

    url = "https://newsapi.org/v2/everything"

    # 2. Craft an advanced query to catch both Bitcoin and macro market triggers
    # We use boolean logic to look for Bitcoin specifically, or crypto coupled with macro economic terms
    # 3. Define time window (NewsAPI free tier allows querying the last 30 days)
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    # 4. Set up default parameters; caller-provided parameters override them
    request_params = {
        "q": query,
        "from": thirty_days_ago,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": 20,
    }
    if params is not None:
        request_params.update(params)
    request_params.pop("apiKey", None)
    # SENSITIVE: the key goes in the X-Api-Key header, not the URL, so it never appears in request error messages or logs
    headers = {"X-Api-Key": api_key}

    # 5. Execute request and process data
    try:
        response = requests.get(url, params=request_params, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "ok":
            articles = data.get("articles", [])
            logger.info("Fetched %d news articles.", len(articles))
            return articles

        logger.error("NewsAPI returned an error: %s", data.get("message", "Unknown error"))
        return []
    except requests.exceptions.RequestException:
        logger.exception("Request to NewsAPI failed (network error or rejected request).")
        return []
