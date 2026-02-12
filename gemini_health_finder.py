import google.generativeai as genai
import os
from datetime import datetime
import json
import feedparser

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
    
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:10]:
                articles.append({
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'summary': entry.get('summary', ''),
                    'source': feed.feed.get('title', 'Unknown')
                })
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
            continue
    
    return articles

def score_articles_with_gemini(articles):
    """Use Gemini to score and select top 3 viral articles"""
    print("Available models:")
    mod = ''
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            mod = m.name
    
    model = genai.GenerativeModel(mod)
    
    articles_text = "\n\n".join([
        f"Article {i+1}:\nTitle: {a['title']}\nSource: {a['source']}\nSummary: {a['summary'][:200]}"
        for i, a in enumerate(articles[:30])
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
    
    try:
        clean_response = response.text.strip()
        if clean_response.startswith('```json'):
            clean_response = clean_response.replace('```json', '').replace('```', '').strip()
        elif clean_response.startswith('```'):
            clean_response = clean_response.replace('```', '').strip()
        
        selections = json.loads(clean_response)
        
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
        recent_articles = fetch_recent_health_articles()
        
        if not recent_articles:
            print("No articles found")
            with open('daily_articles.txt', 'w') as f:
                f.write("No articles found from RSS feeds")
        else:
            print(f"Found {len(recent_articles)} articles. Analyzing with Gemini...\n")
            
            top_articles = score_articles_with_gemini(recent_articles)
            
            formatted_output = format_output(top_articles)
            print(formatted_output)
            
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

