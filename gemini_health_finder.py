import google.generativeai as genai
import os
from datetime import datetime
import json
import requests
from bs4 import BeautifulSoup

# Configure Gemini
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

def fetch_recent_health_articles():
    """Scrape recent health articles from RSS feeds"""
    articles = []
    
    # Free health news sources
    rss_feeds = [
        'https://www.medicalnewstoday.com/rss/news.xml',
        'https://www.sciencedaily.com/rss/health_medicine.xml',
        'https://consumer.healthday.com/rss/healthday.rss',
    ]
    
    try:
        import feedparser
        
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:10]:  # Get top 10 from each
                    articles.append({
                        'title': entry.get('title', ''),
                        'url': entry.get('link', ''),
                        'summary': entry.get('summary', ''),
                        'source': feed.feed.get('title', 'Unknown')
                    })
            except Exception as e:
                print(f"Error fetching {feed_url}: {e}")
                continue
    except ImportError:
        print("feedparser not installed, using sample data")
        return []
    
    return articles

def score_articles_with_gemini(articles):
    """Use Gemini to score and select top 3 viral articles"""
    
    model = genai.GenerativeModel('gemini-pro')
    
    articles_text = "\n\n".join([
        f"Article {i+1}:\nTitle: {a['title']}\nSource: {a['source']}\nSummary: {a['summary'][:200]}"
        for i, a in enumerate(articles[:30])  # Limit to 30 to avoid token limits
    ])
    
    prompt = f"""Here are recent health articles from today. Analyze them and select the TOP 3 that have the highest viral potential.

{articles_text}

Evaluate based on:
- Shareability and emotional impact
- Novelty and surprise factor
- Controversy or debate potential
- Practical usefulness

Return ONLY a JSON array with the top 3, using this exact format:
[
  {{
    "article_number": 5,
    "viral_score": 92,
    "why_viral": "Brief explanation of why this will go viral"
  }}
]

Return ONLY the JSON array."""

    response = model.generate_content(prompt)
    
    # Parse the response
    try:
        clean_response = response.text.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response.replace('```json', '').replace('```', '').strip()
        elif clean_response.startswith('```'):
            clean_response = clean_response.replace('```', '').strip()
        
        selections = json.loads(clean_response)
        
        # Build final results
        results = []
        for selection in selections:
            idx = selection['article_number'] - 1
            if idx < len(articles):
                article = articles[idx].copy()
                article['viral_score'] = selection['viral_score']
                article['why_viral'] = selection['why_viral']
                results.append(article)
        
        return results
    
    except Exception as e:
        print(f"Error parsing Gemini response: {e}")
        # Fallback: return first 3 articles with default scores
        return [
            {**articles[i], 'viral_score': 75, 'why_viral': 'Trending health topic'}
            for i in range(min(3, len(articles)))
        ]

def format_output(articles):
    """Format the articles for posting"""
    output = f"🔥 Top 3 Viral Health Articles - {datetime.now().strftime('%B %d, %Y')}\n\n"
    
    for i, article in enumerate(articles, 1):
        output += f"{i}. **{article['title']}**\n"
        output += f"   📊 Viral Score: {article['viral_score']}/100\n"
        output += f"   💡 Why it's viral: {article['why_viral']}\n"
        output += f"   🔗 {article['url']}\n"
        output += f"   📰 Source: {article['source']}\n\n"
    
    return output

if __name__ == "__main__":
    print("🔍 Fetching recent health articles...\n")
    
    try:
        # Fetch recent articles
        recent_articles = fetch_recent_health_articles()
        
        if not recent_articles:
            print("No articles found, using Gemini standalone mode")
            # Fallback to original approach
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Generate 3 trending health article ideas with titles, URLs, and viral scores in JSON format")
            print(response.text)
            with open('daily_articles.txt', 'w') as f:
                f.write(response.text)
        else:
            print(f"Found {len(recent_articles)} articles. Analyzing with Gemini...\n")
            
            # Score with Gemini
            top_articles = score_articles_with_gemini(recent_articles)
            
            # Format output
            formatted_output = format_output(top_articles)
            print(formatted_output)
            
            # Save outputs
            with open('daily_articles.txt', 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            
            with open('daily_articles.json', 'w', encoding='utf-8') as f:
                json.dump(top_articles, f, indent=2, ensure_ascii=False)
            
            print("✅ Articles saved successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        with open('daily_articles.txt', 'w') as f:
            f.write(f"Error occurred: {e}\n\n{traceback.format_exc()}")
```

### Update `requirements.txt`:
```
google-generativeai>=0.3.0
feedparser>=6.0.0
beautifulsoup4>=4.12.0
requests>=2.31.0
