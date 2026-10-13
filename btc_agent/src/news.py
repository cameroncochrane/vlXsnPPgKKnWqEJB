# Here the logic regarding fetching bitcoin/financial/world news will be placed:

# Base imports:
import os
import requests
from datetime import datetime, timedelta

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
        "apiKey": api_key,
    }
    if params is not None:
        request_params.update(params)
    request_params["apiKey"] = api_key

    # 5. Execute request and process data
    try:
        response = requests.get(url, params=request_params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "ok":
            articles = data.get("articles", [])
            print(f"Successfully fetched {len(articles)} articles for your trading agent:\n")
            for idx, article in enumerate(articles, 1):
                source = article.get("source", {}).get("name", "Unknown source")
                title = article.get("title", "No title")
                published = article.get("publishedAt", "Unknown date")
                url = article.get("url", "")

                print(f"[{idx}] {title}")
                print(f"Source: {source} | Published: {published}")
                print(f"Link: {url}\n")
            return articles

        print(f"API Error: {data.get('message', 'Unknown error occurrence')}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        return []
