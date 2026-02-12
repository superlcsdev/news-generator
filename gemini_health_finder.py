import os
from datetime import datetime, timedelta
import json
import feedparser
import re

def fetch_recent_health_articles():
    """Scrape recent health articles from RSS feeds"""
    articles = []
    
    rss_feeds = [
        'https://www.medicalnewstoday.com/rss/news.xml',
        'https://www.sciencedaily.com/rss/health_medicine.xml',
        'https://consumer.healthday.com/rss/healthday.rss',
    ]
    
    for feed_url in rss_feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:15]:
                articles.append({
                    'title': entry.get('title', ''),
                    'url': entry.get('link', ''),
                    'summary': entry.get('summary', ''),
                    'published_parsed': entry.get('published_parsed'),
                    'source': feed.feed.get('title', 'Unknown')
                })
        except Exception as e:
            print(f"Error fetching {feed_url}: {e}")
            continue
    
    return articles

def calculate_viral_score(article):
    """Calculate viral potential score based on keywords and characteristics"""
    score = 0
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    text = f"{title} {summary}"
    
    # High-value viral keywords
    viral_keywords = {
        'breakthrough': 5,
        'discover': 4,
        'new study': 4,
        'scientists find': 4,
        'shocking': 3,
        'surprising': 3,
        'cancer': 3,
        'weight loss': 3,
        'brain': 2,
        'heart': 2,
        'covid': 2,
        'alzheimer': 3,
        'diabetes': 2,
        'mental health': 2,
        'longevity': 3,
        'anti-aging': 3,
        'obesity': 2,
        'exercise': 2,
        'diet': 2,
        'sleep': 2,
        'vitamin': 2,
        'risk': 2,
        'prevent': 2,
        'cure': 4,
        'trial': 3,
        'fda': 3,
        'warning': 2,
    }
    
    # Score based on keywords
    for keyword, weight in viral_keywords.items():
        if keyword in text:
            score += weight
    
    # Recency boost
    pub_date = article.get('published_parsed')
    if pub_date:
        try:
            pub_datetime = datetime(*pub_date[:6])
            hours_old = (datetime.now() - pub_datetime).total_seconds() / 3600
            if hours_old < 24:
                score += 10
            elif hours_old < 48:
                score += 5
            elif hours_old < 72:
                score += 2
        except:
            pass
    
    # Title characteristics
    if '?' in title:
        score += 2
    if any(word in title for word in ['you', 'your']):
        score += 3
    if re.search(r'\d+', title):
        score += 2
    if len(title.split()) > 10:
        score += 1
    
    # Emotional/clickbait indicators
    surprise_words = ['surprising', 'unexpected', 'contrary', 'debunked', 'myth', 'secret', 'hidden']
    if any(word in text for word in surprise_words):
        score += 3
    
    # Action words
    action_words = ['how to', 'ways to', 'tips', 'avoid', 'prevent', 'boost', 'improve']
    if any(word in text for word in action_words):
        score += 2
    
    return min(score, 100)

def generate_why_viral(article):
    """Generate explanation for why article is viral"""
    title = article.get('title', '').lower()
    
    reasons = []
    
    if 'breakthrough' in title or 'discover' in title:
        reasons.append("Major scientific breakthrough")
    if 'cancer' in title or 'alzheimer' in title:
        reasons.append("Critical health condition with high public interest")
    if 'weight loss' in title or 'diet' in title:
        reasons.append("High engagement topic with practical value")
    if '?' in title:
        reasons.append("Question format drives curiosity")
    if any(word in title for word in ['you', 'your']):
        reasons.append("Personal relevance to readers")
    if 'new study' in title or 'scientists' in title:
        reasons.append("Backed by research credibility")
    if article['viral_score'] >= 20:
        reasons.append("Timely and trending topic")
    
    if not reasons:
        reasons.append("Relevant health topic with shareability potential")
    
    return "; ".join(reasons[:3])

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
        articles = fetch_recent_health_articles()
        
        if not articles:
            print("❌ No articles found")
            with open('daily_articles.txt', 'w') as f:
                f.write("No articles found from RSS feeds")
        else:
            print(f"✅ Found {len(articles)} articles\n")
            
            # Score all articles
            for article in articles:
                article['viral_score'] = calculate_viral_score(article)
                article['why_viral'] = generate_why_viral(article)
            
            # Sort by viral score and get top 3
            top_articles = sorted(articles, key=lambda x: x['viral_score'], reverse=True)[:3]
            
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
