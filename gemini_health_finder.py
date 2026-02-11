import google.generativeai as genai
import os
from datetime import datetime
import json

# Configure Gemini
genai.configure(api_key=os.environ.get('GEMINI_API_KEY'))

def find_viral_health_articles():
    """Use Gemini with web search to find viral health articles"""
    
    # Use Gemini 1.5 Flash (fast, free, with grounding/search)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    prompt = f"""Today is {datetime.now().strftime('%B %d, %Y')}.

Search the web and find the 3 most viral-worthy health articles published in the last 24-48 hours.

For each article, evaluate viral potential based on:
- Social engagement signals and trending topics
- Shareability (surprising, controversial, actionable)
- Novelty factor and emotional impact
- Credibility of source

Return ONLY a JSON array with this exact format:
[
  {{
    "title": "Article title",
    "url": "Full URL",
    "viral_score": 85,
    "why_viral": "Brief explanation of viral potential",
    "source": "Publication name"
  }}
]

Focus on recent breakthroughs, surprising findings, or trending health topics. No markdown, just the JSON array."""

    # Enable grounding with Google Search
    response = model.generate_content(
        prompt,
        tools='google_search_retrieval'
    )
    
    return response.text

def format_output(json_response):
    """Format the JSON response for posting"""
    try:
        articles = json.loads(json_response)
        
        output = f"🔥 Top 3 Viral Health Articles - {datetime.now().strftime('%B %d, %Y')}\n\n"
        
        for i, article in enumerate(articles, 1):
            output += f"{i}. **{article['title']}**\n"
            output += f"   📊 Viral Score: {article['viral_score']}/100\n"
            output += f"   💡 Why it's viral: {article['why_viral']}\n"
            output += f"   🔗 {article['url']}\n"
            output += f"   📰 Source: {article['source']}\n\n"
        
        return output, articles
    
    except json.JSONDecodeError:
        return f"⚠️ Raw Response:\n{json_response}", []

if __name__ == "__main__":
    print("🔍 Using Gemini AI to find viral health articles...\n")
    
    try:
        json_response = find_viral_health_articles()
        formatted_output, articles = format_output(json_response)
        
        print(formatted_output)
        
        # Save outputs
        with open('daily_articles.txt', 'w', encoding='utf-8') as f:
            f.write(formatted_output)
        
        if articles:
            with open('daily_articles.json', 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
        
        print("✅ Articles saved successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        with open('daily_articles.txt', 'w') as f:
            f.write(f"Error occurred: {e}")
