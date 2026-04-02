import feedparser
import json
import anthropic
import os
import time
from datetime import datetime, timezone

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SOURCES = [
    {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "name": "The Verge"},
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "name": "TechCrunch"},
    {"url": "https://venturebeat.com/category/ai/feed/", "name": "VentureBeat"},
    {"url": "https://www.wired.com/feed/tag/artificial-intelligence/rss", "name": "Wired"},
    {"url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "name": "Ars Technica"},
    {"url": "https://www.technologyreview.com/feed/", "name": "MIT Tech Review"},
    {"url": "https://huggingface.co/blog/feed.xml", "name": "Hugging Face"},
    {"url": "https://blogs.microsoft.com/ai/feed/", "name": "Microsoft AI"},
    {"url": "https://blog.google/technology/ai/rss/", "name": "Google AI"},
    {"url": "https://openai.com/blog/rss/", "name": "OpenAI"},
    {"url": "https://www.deepmind.com/blog/rss.xml", "name": "DeepMind"},
    {"url": "https://stability.ai/blog/rss.xml", "name": "Stability AI"},
    {"url": "https://www.anthropic.com/news/rss.xml", "name": "Anthropic"},
    {"url": "https://importai.substack.com/feed", "name": "Import AI"},
    {"url": "https://lastweekin.ai/feed", "name": "Last Week in AI"},
    {"url": "https://aiweekly.co/issues.rss", "name": "AI Weekly"},
    {"url": "https://www.artificialintelligence-news.com/feed/", "name": "AI News"},
    {"url": "https://syncedreview.com/feed/", "name": "Synced Review"},
    {"url": "https://bdtechtalks.com/feed/", "name": "TechTalks"},
    {"url": "https://www.unite.ai/feed/", "name": "Unite AI"},
]

def summarize_article(title, content):
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""Summarize this AI news article in exactly 2 sentences (max 50 words total).
Be factual and specific. Include key numbers or metrics if present.

Title: {title}
Content: {content[:1500]}

Also provide 3 short relevant tags.
Respond ONLY with valid JSON like this:
{{"summary": "...", "tags": ["tag1", "tag2", "tag3"]}}"""
        }]
    )
    return json.loads(msg.content[0].text)

articles = []
seen_titles = set()

for source in SOURCES:
    try:
        feed = feedparser.parse(source["url"])
        print(f"Fetching: {source['name']} — {len(feed.entries)} entries")

        for entry in feed.entries[:3]:
            title = entry.get("title", "").strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)

            content = entry.get("summary", "") or ""
            if hasattr(entry, "content"):
                content = entry.content[0].get("value", "") or content

            try:
                result = summarize_article(title, content)
                articles.append({
                    "id": len(articles) + 1,
                    "source": source["name"],
                    "title": title,
                    "summary": result["summary"],
                    "tags": result["tags"],
                    "url": entry.get("link", "#"),
                    "published": entry.get("published", ""),
                    "fetched_at": datetime.now(timezone.utc).isoformat()
                })
                print(f"  OK: {title[:60]}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  Summarize error: {e}")
                continue

    except Exception as e:
        print(f"Feed error {source['name']}: {e}")

os.makedirs("data", exist_ok=True)
with open("data/articles.json", "w", encoding="utf-8") as f:
    json.dump({
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(articles),
        "articles": articles
    }, f, ensure_ascii=False, indent=2)

print(f"\nDone! Saved {len(articles)} articles to data/articles.json")
