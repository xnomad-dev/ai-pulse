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
    {"url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "name": "Ars Technica"},
    {"url": "https://www.technologyreview.com/feed/", "name": "MIT Tech Review"},
    {"url": "https://huggingface.co/blog/feed.xml", "name": "Hugging Face"},
    {"url": "https://blogs.microsoft.com/ai/feed/", "name": "Microsoft AI"},
    {"url": "https://blog.google/technology/ai/rss/", "name": "Google AI"},
    {"url": "https://www.deepmind.com/blog/rss.xml", "name": "DeepMind"},
    {"url": "https://lastweekin.ai/feed", "name": "Last Week in AI"},
    {"url": "https://www.artificialintelligence-news.com/feed/", "name": "AI News"},
    {"url": "https://syncedreview.com/feed/", "name": "Synced Review"},
    {"url": "https://bdtechtalks.com/feed/", "name": "TechTalks"},
    {"url": "https://www.marktechpost.com/feed/", "name": "MarkTechPost"},
    {"url": "https://aimagazine.com/rss.xml", "name": "AI Magazine"},
    {"url": "https://www.infoq.com/ai-ml-data-eng/rss.xml", "name": "InfoQ AI"},
    {"url": "https://www.zdnet.com/topic/artificial-intelligence/rss.xml", "name": "ZDNet AI"},
    {"url": "https://www.forbes.com/ai/feed/", "name": "Forbes AI"},
    {"url": "https://machinelearningmastery.com/feed/", "name": "ML Mastery"},
    {"url": "https://towardsdatascience.com/feed", "name": "Towards Data Science"},
    {"url": "https://www.datasciencecentral.com/feed/", "name": "Data Science Central"},
    {"url": "https://blogs.nvidia.com/feed/", "name": "NVIDIA Blog"},
    {"url": "https://aws.amazon.com/blogs/machine-learning/feed/", "name": "AWS ML Blog"},
    {"url": "https://developer.nvidia.com/blog/feed/", "name": "NVIDIA Developer"},
    {"url": "https://cloud.google.com/blog/products/ai-machine-learning/rss.xml", "name": "Google Cloud AI"},
    {"url": "https://research.facebook.com/feed/", "name": "Meta Research"},
    {"url": "https://bair.berkeley.edu/blog/feed.xml", "name": "Berkeley AI Research"},
    {"url": "https://openai.com/blog/rss/", "name": "OpenAI"},
    {"url": "https://www.anthropic.com/news/rss.xml", "name": "Anthropic"},
    {"url": "https://mistral.ai/news/rss.xml", "name": "Mistral AI"},
    {"url": "https://stability.ai/blog/rss.xml", "name": "Stability AI"},
    {"url": "https://www.unite.ai/feed/", "name": "Unite AI"},
    {"url": "https://importai.substack.com/feed", "name": "Import AI"},
]

def summarize_article(title, content):
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""You must respond with ONLY a JSON object, no other text.

Summarize this AI news article in 2 sentences max 50 words.
Give 3 short tags.

Title: {title}
Content: {content[:1000]}

Return ONLY this JSON:
{{"summary": "your summary here", "tags": ["tag1", "tag2", "tag3"]}}"""
        }]
    )
    raw = msg.content[0].text.strip()
    print(f"  RAW: [{raw[:150]}]")
    raw = raw.replace("```json", "").replace("```", "").strip()
    start = raw.find("{")
    end = raw.rfind("}") + 1
    if start >= 0 and end > start:
        raw = raw[start:end]
    return json.loads(raw)

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
                time.sleep(0.3)
            except Exception as e:
                print(f"  ERROR: {e}")
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
