import os
from datetime import datetime, timedelta
import json
import feedparser
import re
from urllib.parse import urlparse

def get_comprehensive_health_feeds():
    """Comprehensive list of reliable health news RSS feeds organized by category"""
    
    feeds = {
        # Tier 1: Major Medical News (Highest Credibility)
        'tier1_medical': [
            {
                'url': 'https://www.medicalnewstoday.com/rss/news.xml',
                'name': 'Medical News Today',
                'credibility_score': 10,
                'category': 'General Medical'
            },
            {
                'url': 'https://www.sciencedaily.com/rss/health_medicine.xml',
                'name': 'Science Daily - Health',
                'credibility_score': 10,
                'category': 'Research'
            },
            {
                'url': 'https://consumer.healthday.com/rss/healthday.rss',
                'name': 'HealthDay',
                'credibility_score': 9,
                'category': 'Consumer Health'
            },
            {
                'url': 'https://www.sciencenews.org/feeds/headlines.rss',
                'name': 'Science News',
                'credibility_score': 10,
                'category': 'Research'
            },
        ],
        
        # Tier 2: Established Health Publishers
        'tier2_established': [
            {
                'url': 'https://www.healthline.com/rssfeed',
                'name': 'Healthline',
                'credibility_score': 8,
                'category': 'General Health'
            },
            {
                'url': 'https://feeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC',
                'name': 'WebMD',
                'credibility_score': 8,
                'category': 'Medical Info'
            },
            {
                'url': 'https://www.everydayhealth.com/rss/health-news.aspx',
                'name': 'Everyday Health',
                'credibility_score': 7,
                'category': 'Wellness'
            },
            {
                'url': 'https://www.prevention.com/rss/all.xml/',
                'name': 'Prevention',
                'credibility_score': 7,
                'category': 'Prevention'
            },
        ],
        
        # Tier 3: Mainstream News Health Sections
        'tier3_mainstream': [
            {
                'url': 'https://rss.nytimes.com/services/xml/rss/nyt/Health.xml',
                'name': 'New York Times Health',
                'credibility_score': 9,
                'category': 'News'
            },
            {
                'url': 'https://www.theguardian.com/society/health/rss',
                'name': 'The Guardian Health',
                'credibility_score': 8,
                'category': 'News'
            },
            {
                'url': 'https://www.npr.org/rss/rss.php?id=1128',
                'name': 'NPR Health',
                'credibility_score': 9,
                'category': 'News'
            },
            {
                'url': 'https://feeds.bbci.co.uk/news/health/rss.xml',
                'name': 'BBC Health',
                'credibility_score': 9,
                'category': 'News'
            },
            {
                'url': 'https://www.cbsnews.com/latest/rss/health',
                'name': 'CBS News Health',
                'credibility_score': 8,
                'category': 'News'
            },
            {
                'url': 'https://feeds.reuters.com/reuters/healthNews',
                'name': 'Reuters Health',
                'credibility_score': 9,
                'category': 'News'
            },
        ],
        
        # Tier 4: Specialized Health Topics
        'tier4_specialized': [
            {
                'url': 'https://www.heart.org/en/news/rss-feeds',
                'name': 'American Heart Association',
                'credibility_score': 10,
                'category': 'Cardiology'
            },
            {
                'url': 'https://www.cancer.org/latest-news.rss',
                'name': 'American Cancer Society',
                'credibility_score': 10,
                'category': 'Oncology'
            },
            {
                'url': 'https://www.diabetes.org/newsroom/rss',
                'name': 'American Diabetes Association',
                'credibility_score': 10,
                'category': 'Diabetes'
            },
            {
                'url': 'https://www.mayoclinic.org/rss/all-health-and-wellness-blog',
                'name': 'Mayo Clinic',
                'credibility_score': 10,
                'category': 'Medical Excellence'
            },
            {
                'url': 'https://www.nih.gov/news-events/news-releases/rss',
                'name': 'NIH News',
                'credibility_score': 10,
                'category': 'Research'
            },
            {
                'url': 'https://www.cdc.gov/rss/cdcnewsroom.xml',
                'name': 'CDC Newsroom',
                'credibility_score': 10,
                'category': 'Public Health'
            },
        ],
        
        # Tier 5: Nutrition & Lifestyle
        'tier5_nutrition': [
            {
                'url': 'https://www.nutritionaction.com/rss/',
                'name': 'Nutrition Action',
                'credibility_score': 8,
                'category': 'Nutrition'
            },
            {
                'url': 'https://www.eatright.org/rss',
                'name': 'Academy of Nutrition and Dietetics',
                'credibility_score': 9,
                'category': 'Nutrition'
            },
        ],
        
        # Tier 6: Mental Health
        'tier6_mental': [
            {
                'url': 'https://www.psychiatry.org/news-room/rss-feeds',
                'name': 'American Psychiatric Association',
                'credibility_score': 10,
                'category': 'Mental Health'
            },
            {
                'url': 'https://www.psychologytoday.com/us/blog/feed',
                'name': 'Psychology Today',
                'credibility_score': 7,
                'category': 'Mental Health'
            },
        ],
    }
    
    # Flatten all feeds into a single list
    all_feeds = []
    for tier, feed_list in feeds.items():
        all_feeds.extend(feed_list)
    
    return all_feeds

def fetch_from_all_sources():
    """Fetch articles from all reliable health sources"""
    
    all_feeds = get_comprehensive_health_feeds()
    articles = []
    
    print(f"📡 Fetching from {len(all_feeds)} reliable health sources...\n")
    
    successful_feeds = 0
    failed_feeds = []
    
    for feed_info in all_feeds:
        try:
            print(f"  Fetching from {feed_info['name']}... ", end='')
            feed = feedparser.parse(feed_info['url'])
            
            if feed.entries:
                count = 0
                for entry in feed.entries[:10]:  # Get top 10 from each source
                    article = {
                        'title': entry.get('title', ''),
                        'url': entry.get('link', ''),
                        'summary': entry.get('summary', entry.get('description', '')),
                        'published_parsed': entry.get('published_parsed'),
                        'source': feed_info['name'],
                        'source_credibility': feed_info['credibility_score'],
                        'category': feed_info['category']
                    }
                    
                    # Only add if we have minimum required fields
                    if article['title'] and article['url']:
                        articles.append(article)
                        count += 1
                
                print(f"✅ Got {count} articles")
                successful_feeds += 1
            else:
                print(f"⚠️ No entries found")
                failed_feeds.append(feed_info['name'])
                
        except Exception as e:
            print(f"❌ Failed: {str(e)[:50]}")
            failed_feeds.append(feed_info['name'])
            continue
    
    print(f"\n✅ Successfully fetched from {successful_feeds}/{len(all_feeds)} sources")
    print(f"📊 Total articles collected: {len(articles)}")
    
    if failed_feeds:
        print(f"\n⚠️ Failed sources ({len(failed_feeds)}):")
        for name in failed_feeds[:5]:  # Show first 5 failures
            print(f"   - {name}")
    
    return articles

def calculate_enhanced_viral_score(article):
    """
    Enhanced viral score calculation that includes:
    - Keyword matching
    - Recency
    - Title characteristics
    - Source credibility
    - Category relevance
    """
    score = 0
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    text = f"{title} {summary}"
    
    # Core viral keywords with weights
    viral_keywords = {
        # High impact discoveries
        'breakthrough': 6,
        'discover': 5,
        'discovered': 5,
        'new study': 5,
        'scientists find': 5,
        'research shows': 5,
        'first time': 4,
        'game changer': 5,
        'revolutionary': 5,
        
        # Shocking/Surprising
        'shocking': 4,
        'surprising': 4,
        'unexpected': 4,
        'hidden': 3,
        'secret': 3,
        'myth': 3,
        'debunked': 4,
        'truth about': 3,
        
        # Major health conditions (high engagement)
        'cancer': 4,
        'alzheimer': 4,
        'heart disease': 4,
        'diabetes': 3,
        'covid': 3,
        'stroke': 3,
        'dementia': 3,
        
        # Popular wellness topics
        'weight loss': 4,
        'lose weight': 4,
        'burn fat': 3,
        'anti-aging': 4,
        'longevity': 4,
        'live longer': 4,
        'sleep better': 3,
        'sleep': 2,
        'mental health': 3,
        'depression': 3,
        'anxiety': 3,
        'stress': 2,
        
        # Nutrition trending
        'diet': 2,
        'nutrition': 2,
        'gut health': 3,
        'microbiome': 3,
        'superfood': 3,
        'vitamin': 2,
        'supplement': 2,
        
        # Exercise & fitness
        'exercise': 2,
        'workout': 2,
        'fitness': 2,
        'muscle': 2,
        
        # Preventive & actionable
        'prevent': 3,
        'cure': 5,
        'treatment': 3,
        'risk': 2,
        'reduce risk': 3,
        'warning': 3,
        'signs of': 3,
        'symptoms': 2,
        
        # Medical authority
        'fda': 4,
        'approved': 3,
        'clinical trial': 4,
        'study': 2,
        'research': 2,
        'expert': 2,
        'doctor': 2,
        
        # Specific trending topics
        'immune system': 3,
        'inflammation': 3,
        'blood pressure': 2,
        'cholesterol': 2,
        'hormone': 2,
        'metabolism': 2,
        'brain health': 3,
    }
    
    # Score based on keywords
    for keyword, weight in viral_keywords.items():
        if keyword in text:
            score += weight
    
    # Recency boost (articles published recently are more viral)
    pub_date = article.get('published_parsed')
    if pub_date:
        try:
            pub_datetime = datetime(*pub_date[:6])
            hours_old = (datetime.now() - pub_datetime).total_seconds() / 3600
            
            if hours_old < 12:
                score += 15  # Very recent
            elif hours_old < 24:
                score += 12
            elif hours_old < 48:
                score += 8
            elif hours_old < 72:
                score += 4
            elif hours_old < 168:  # Less than a week
                score += 2
        except:
            pass
    
    # Title engagement factors
    if '?' in title:
        score += 3  # Questions drive curiosity
    
    if any(word in title for word in ['you', 'your']):
        score += 4  # Personal relevance
    
    # Numbers in title (listicles, stats)
    numbers = re.findall(r'\b\d+\b', title)
    if numbers:
        score += 3
    
    # Title length (optimal is 10-15 words)
    word_count = len(title.split())
    if 10 <= word_count <= 15:
        score += 2
    elif word_count > 15:
        score += 1
    
    # Emotional/clickbait indicators (use carefully)
    surprise_words = ['surprising', 'unexpected', 'shocking', 'contrary', 'debunked', 'myth', 'secret', 'hidden', 'truth']
    surprise_count = sum(1 for word in surprise_words if word in text)
    score += min(surprise_count * 3, 9)  # Max 9 points from this
    
    # Action words (practical value)
    action_words = ['how to', 'ways to', 'tips', 'avoid', 'prevent', 'boost', 'improve', 'increase', 'reduce', 'lower']
    if any(word in text for word in action_words):
        score += 4
    
    # Source credibility boost
    # Higher credibility sources get a boost because they're more shareable
    credibility = article.get('source_credibility', 5)
    if credibility >= 9:
        score += 8  # Very trusted sources
    elif credibility >= 7:
        score += 5
    elif credibility >= 5:
        score += 2
    
    # Category-specific boosts
    category = article.get('category', '').lower()
    high_engagement_categories = ['research', 'oncology', 'cardiology', 'mental health', 'nutrition']
    if any(cat in category for cat in high_engagement_categories):
        score += 3
    
    # Penalty for very old articles
    if pub_date:
        try:
            pub_datetime = datetime(*pub_date[:6])
            days_old = (datetime.now() - pub_datetime).days
            if days_old > 7:
                score -= min((days_old - 7) * 2, 20)  # Penalty for old news
        except:
            pass
    
    return max(min(score, 100), 0)  # Keep between 0-100

def generate_why_viral(article):
    """Generate explanation for why article is viral"""
    title = article.get('title', '').lower()
    summary = article.get('summary', '').lower()
    text = f"{title} {summary}"
    
    reasons = []
    
    # Discovery/breakthrough
    if any(word in text for word in ['breakthrough', 'discover', 'first time', 'revolutionary']):
        reasons.append("Major scientific breakthrough")
    
    # Major health conditions
    if any(word in title for word in ['cancer', 'alzheimer', 'heart disease', 'diabetes']):
        reasons.append("Critical health condition with high public interest")
    
    # Popular topics
    if any(word in title for word in ['weight loss', 'diet', 'exercise', 'sleep']):
        reasons.append("High engagement topic with practical value")
    
    # Curiosity drivers
    if '?' in title:
        reasons.append("Question format drives curiosity")
    
    # Personal relevance
    if any(word in title for word in ['you', 'your']):
        reasons.append("Personal relevance to readers")
    
    # Research backing
    if any(word in text for word in ['new study', 'scientists', 'research shows', 'clinical trial']):
        reasons.append("Backed by research credibility")
    
    # Surprising/controversial
    if any(word in text for word in ['surprising', 'shocking', 'unexpected', 'debunked', 'myth']):
        reasons.append("Surprising findings challenge common beliefs")
    
    # Actionable content
    if any(word in text for word in ['how to', 'prevent', 'avoid', 'tips', 'ways to']):
        reasons.append("Provides actionable health advice")
    
    # Source credibility
    if article.get('source_credibility', 0) >= 9:
        reasons.append(f"Published by highly trusted source ({article['source']})")
    
    # Recency
    pub_date = article.get('published_parsed')
    if pub_date:
        try:
            pub_datetime = datetime(*pub_date[:6])
            hours_old = (datetime.now() - pub_datetime).total_seconds() / 3600
            if hours_old < 24:
                reasons.append("Breaking news (published within 24 hours)")
        except:
            pass
    
    if not reasons:
        reasons.append("Relevant health topic with shareability potential")
    
    return "; ".join(reasons[:4])  # Max 4 reasons

def deduplicate_articles(articles):
    """Remove duplicate articles based on title similarity"""
    
    unique_articles = []
    seen_titles = set()
    
    for article in articles:
        # Normalize title for comparison
        normalized_title = article['title'].lower().strip()
        normalized_title = re.sub(r'[^\w\s]', '', normalized_title)  # Remove punctuation
        
        # Check for similarity with existing titles
        is_duplicate = False
        for seen in seen_titles:
            # Calculate simple similarity (if 80% of words match, it's a duplicate)
            seen_words = set(seen.split())
            new_words = set(normalized_title.split())
            
            if len(seen_words) > 0:
                overlap = len(seen_words.intersection(new_words))
                similarity = overlap / len(seen_words)
                
                if similarity > 0.8:
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            unique_articles.append(article)
            seen_titles.add(normalized_title)
    
    return unique_articles

def extract_key_insight(article):
    """Extract the main health insight from the article"""
    title = article['title']
    summary = article.get('summary', '')[:300]
    
    numbers = re.findall(r'\d+%|\d+ percent', title + ' ' + summary)
    
    insight = title
    if numbers:
        insight = f"{title} - {numbers[0]}"
    
    return insight

def generate_instagram_caption(article, article_number):
    """Generate Instagram-optimized caption (2200 char limit)"""
    
    title = article['title']
    insight = extract_key_insight(article)
    
    hooks = [
        f"🚨 New research just dropped:",
        f"⚠️ Health experts are talking about this:",
        f"💡 This could change everything we know about health:",
        f"🔬 Science alert:",
        f"📊 The latest study reveals:",
    ]
    
    hook = hooks[article_number % len(hooks)]
    
    caption = f"""{hook}

{title}

Here's what you need to know:

{article.get('summary', '')[:400]}...

💭 My take as a health expert:
This is significant because it {article['why_viral'].lower()}. Always consult with your healthcare provider before making any changes to your health routine.

🔗 Read the full study: Link in bio or comments

---
📌 Save this post for later
💬 Tag someone who needs to see this
🔄 Share to spread awareness

#HealthNews #WellnessTips #HealthyLiving #ScienceBacked #HealthExpert #Wellness #NutritionFacts #HealthAwareness #MedicalNews #EvidenceBased

Source: {article['source']} | Credibility: {article['source_credibility']}/10"""
    
    return caption

def generate_facebook_caption(article):
    """Generate Facebook-optimized caption"""
    
    title = article['title']
    
    caption = f"""📢 Important Health Update!

{title}

I came across this research today and had to share it with you all. Here's why this matters:

{article.get('summary', '')[:500]}...

🔍 What does this mean for you?

As a health professional, I always recommend:
✅ Staying informed with evidence-based research
✅ Discussing any health changes with your doctor
✅ Being cautious about health trends without scientific backing

💡 Key Takeaway: {article['why_viral']}

Want to learn more? Check out the full article here: {article['url']}

What are your thoughts on this? Drop a comment below! 👇

📌 Share this with someone who cares about their health!

---
Source: {article['source']} (Credibility: {article['source_credibility']}/10)
Viral Score: {article['viral_score']}/100
Category: {article['category']}

#HealthNews #Wellness #HealthyLiving #MedicalResearch #HealthEducation #StayInformed"""
    
    return caption

def generate_tiktok_caption(article):
    """Generate TikTok-optimized caption"""
    
    title = article['title']
    
    caption = f"""🚨 You need to know this!

{title}

The research shows: {article.get('summary', '')[:200]}...

💥 Why this matters:
{article['why_viral']}

⚠️ Always check with your doctor before trying anything new!

Full details 👉 {article['url']}

---
Drop a 💖 if you learned something new!
Save this for later 📌
Share with your health-conscious friends 🔄

#HealthTok #WellnessTips #HealthFacts #ScienceTok #LearnOnTikTok #HealthNews #Wellness #FYP #ForYou #HealthExpert #MedicalNews #StayHealthy

Source: {article['source']}"""
    
    return caption

def generate_twitter_caption(article):
    """Generate Twitter/X-optimized caption (280 chars)"""
    
    title = article['title'][:200]
    
    caption = f"""🔬 {title}

Key: {article['why_viral'][:80]}

Source: {article['source']}
{article['url']}

#HealthNews #Wellness"""
    
    if len(caption) > 280:
        caption = f"""🔬 {title[:150]}...

{article['why_viral'][:60]}

{article['url']}

#HealthNews"""
    
    return caption

def generate_linkedin_caption(article):
    """Generate LinkedIn-optimized caption"""
    
    title = article['title']
    
    caption = f"""Recent Health Research Insights 📊

{title}

As healthcare professionals, staying current with evidence-based research is crucial. Here's what the latest study reveals:

{article.get('summary', '')[:600]}...

Key Implications:
- {article['why_viral']}
- This research adds to our understanding of health optimization
- Clinical applications should be discussed with qualified practitioners

Professional Perspective:
This study is particularly noteworthy because it addresses a significant gap in our current understanding. While the findings are promising, it's important to:

1. Review the full methodology and sample size
2. Consider the peer review status
3. Understand limitations and future research needs
4. Apply findings within appropriate clinical context

Full research article: {article['url']}

What are your thoughts on these findings? How might this impact clinical practice in your field?

---
Source: {article['source']} (Credibility Score: {article['source_credibility']}/10)
Research Viral Score: {article['viral_score']}/100
Category: {article['category']}

#HealthcareInnovation #MedicalResearch #EvidenceBasedMedicine #HealthcareLeadership #ClinicalResearch #PublicHealth #HealthTech #MedicalScience #HealthcareProfessionals"""
    
    return caption

def generate_image_suggestions(article):
    """Generate image suggestions based on article content"""
    
    title_lower = article['title'].lower()
    summary_lower = article.get('summary', '').lower()
    
    suggestions = {
        'style': '',
        'ai_prompt': '',
        'stock_photo_keywords': [],
        'color_palette': [],
        'visual_elements': [],
        'do_not_include': []
    }
    
    if any(word in title_lower for word in ['cancer', 'disease', 'medical', 'treatment', 'diagnosis']):
        suggestions['style'] = 'Medical/Clinical'
        suggestions['ai_prompt'] = f"Professional medical illustration showing {article['title']}, clean clinical aesthetic, soft lighting, high detail, scientific accuracy, calming blue and white tones, modern healthcare setting"
        suggestions['stock_photo_keywords'] = ['doctor consultation', 'medical research', 'hospital technology', 'healthcare professional']
        suggestions['color_palette'] = ['#4A90E2', '#FFFFFF', '#E8F4F8', '#2C5F8D']
        suggestions['visual_elements'] = ['Medical equipment', 'Healthcare professionals', 'Clean modern environment', 'Soft focus background']
        suggestions['do_not_include'] = ['Blood', 'Graphic medical procedures', 'Distressed patients']
    
    elif any(word in title_lower for word in ['brain', 'mental health', 'depression', 'anxiety', 'cognitive', 'memory']):
        suggestions['style'] = 'Mental Wellness'
        suggestions['ai_prompt'] = f"Peaceful mental wellness concept for {article['title']}, serene atmosphere, person meditating or in calm state, warm natural lighting, gentle pastel colors, hopeful and uplifting mood, abstract brain visualization in background"
        suggestions['stock_photo_keywords'] = ['meditation', 'peaceful woman', 'mental clarity', 'brain health', 'mindfulness']
        suggestions['color_palette'] = ['#A8D5E2', '#F9E4D4', '#B8E6D5', '#FFE5D9']
        suggestions['visual_elements'] = ['Calm faces', 'Natural settings', 'Soft bokeh', 'Abstract neural networks', 'Peaceful postures']
        suggestions['do_not_include'] = ['Stressed expressions', 'Dark moody lighting', 'Clinical environments']
    
    elif any(word in title_lower for word in ['diet', 'nutrition', 'food', 'eating', 'meal', 'vitamin']):
        suggestions['style'] = 'Fresh & Appetizing'
        suggestions['ai_prompt'] = f"Vibrant healthy food photography for {article['title']}, fresh colorful ingredients, bright natural lighting, overhead flat lay composition, abundance of nutritious foods, appetizing presentation, Instagram-worthy food styling"
        suggestions['stock_photo_keywords'] = ['healthy food', 'fresh vegetables', 'balanced meal', 'nutrition', 'colorful produce']
        suggestions['color_palette'] = ['#4CAF50', '#FF9800', '#FFC107', '#8BC34A']
        suggestions['visual_elements'] = ['Fresh produce', 'Vibrant colors', 'Wooden backgrounds', 'Natural textures', 'Top-down view']
        suggestions['do_not_include'] = ['Processed foods', 'Fast food', 'Artificial looking items']
    
    elif any(word in title_lower for word in ['exercise', 'fitness', 'workout', 'training', 'physical activity', 'gym']):
        suggestions['style'] = 'Dynamic & Energetic'
        suggestions['ai_prompt'] = f"Dynamic fitness scene for {article['title']}, athletic person in motion, energetic atmosphere, dramatic lighting, powerful and motivating, vibrant colors, professional sports photography style, sharp focus on subject"
        suggestions['stock_photo_keywords'] = ['fitness workout', 'athletic training', 'exercise', 'gym motivation', 'active lifestyle']
        suggestions['color_palette'] = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#292F36']
        suggestions['visual_elements'] = ['Motion blur', 'Athletic bodies', 'Gym equipment', 'Determined expressions', 'Action shots']
        suggestions['do_not_include'] = ['Extreme body types', 'Overly sexualized poses', 'Dangerous exercises']
    
    elif any(word in title_lower for word in ['sleep', 'insomnia', 'rest', 'tired', 'fatigue']):
        suggestions['style'] = 'Peaceful & Restful'
        suggestions['ai_prompt'] = f"Serene sleep environment for {article['title']}, peaceful bedroom scene, soft morning light, comfortable bedding, calming blue and white tones, tranquil atmosphere, invitation to rest, cozy and safe feeling"
        suggestions['stock_photo_keywords'] = ['peaceful sleep', 'comfortable bed', 'bedroom tranquility', 'rest and recovery']
        suggestions['color_palette'] = ['#6C96C8', '#FFFFFF', '#E6F2FF', '#8AADD6']
        suggestions['visual_elements'] = ['Soft fabrics', 'Gentle lighting', 'Comfortable bedding', 'Peaceful expressions', 'Morning glow']
        suggestions['do_not_include'] = ['Alarm clocks', 'Screens/devices', 'Cluttered rooms']
    
    elif any(word in title_lower for word in ['heart', 'cardiovascular', 'blood pressure', 'cholesterol']):
        suggestions['style'] = 'Health & Vitality'
        suggestions['ai_prompt'] = f"Heart health and vitality concept for {article['title']}, glowing anatomical heart illustration, vibrant red and pink tones, life force energy, hopeful and strong, medical accuracy with artistic beauty, inspiring wellness message"
        suggestions['stock_photo_keywords'] = ['heart health', 'cardiovascular wellness', 'healthy heart', 'medical heart illustration']
        suggestions['color_palette'] = ['#E74C3C', '#FF6B9D', '#C0392B', '#FFC3A0']
        suggestions['visual_elements'] = ['Heart imagery', 'Vital signs graphics', 'Active lifestyle', 'Strength symbols']
        suggestions['do_not_include'] = ['Graphic medical imagery', 'Surgical scenes', 'Disease visualization']
    
    elif any(word in title_lower for word in ['aging', 'longevity', 'anti-aging', 'elderly', 'senior']):
        suggestions['style'] = 'Timeless & Graceful'
        suggestions['ai_prompt'] = f"Graceful aging concept for {article['title']}, vibrant senior with youthful energy, warm golden hour lighting, active and joyful, celebrating life at every age, natural beauty, wisdom and vitality combined, inspiring and aspirational"
        suggestions['stock_photo_keywords'] = ['active seniors', 'healthy aging', 'graceful elderly', 'longevity lifestyle']
        suggestions['color_palette'] = ['#D4A574', '#F5E6D3', '#8B7355', '#FFF8E7']
        suggestions['visual_elements'] = ['Active older adults', 'Natural wrinkles (positive)', 'Joyful expressions', 'Golden lighting']
        suggestions['do_not_include'] = ['Frailty', 'Medical dependency', 'Stereotypical aging imagery']
    
    elif any(word in title_lower for word in ['immune', 'immunity', 'infection', 'bacteria', 'virus']):
        suggestions['style'] = 'Scientific & Protective'
        suggestions['ai_prompt'] = f"Immune system protection concept for {article['title']}, abstract visualization of strong immunity, protective shield imagery, cellular level detail, vibrant healthy colors, scientific accuracy, hopeful and empowering, micro-photography aesthetic"
        suggestions['stock_photo_keywords'] = ['immune system', 'antibodies', 'health protection', 'cellular defense']
        suggestions['color_palette'] = ['#00BCD4', '#4CAF50', '#FFFFFF', '#E1F5FE']
        suggestions['visual_elements'] = ['Shield symbols', 'Cellular imagery', 'Protective barriers', 'Strength indicators']
        suggestions['do_not_include'] = ['Sick people', 'Germs in scary context', 'Medical procedures']
    
    else:
        suggestions['style'] = 'General Wellness'
        suggestions['ai_prompt'] = f"Inspiring wellness concept for {article['title']}, healthy lifestyle imagery, bright and uplifting, diverse people feeling great, natural environment, optimistic and encouraging, professional health photography, aspirational but achievable"
        suggestions['stock_photo_keywords'] = ['wellness', 'healthy lifestyle', 'well-being', 'health awareness']
        suggestions['color_palette'] = ['#4CAF50', '#2196F3', '#FFC107', '#FFFFFF']
        suggestions['visual_elements'] = ['Smiling people', 'Natural light', 'Active poses', 'Clean backgrounds']
        suggestions['do_not_include'] = ['Medical procedures', 'Illness imagery', 'Pharmaceutical focus']
    
    suggestions['instagram_specs'] = {
        'aspect_ratio': '1:1 (Square) or 4:5 (Portrait)',
        'recommended_size': '1080x1080px or 1080x1350px',
        'text_safe_zone': 'Keep important elements in center 80%',
        'tips': 'Use high contrast, bold visuals that stop the scroll'
    }
    
    suggestions['facebook_specs'] = {
        'aspect_ratio': '1.91:1 (Landscape) or 1:1 (Square)',
        'recommended_size': '1200x630px or 1080x1080px',
        'text_overlay': 'Text can be up to 20% of image',
        'tips': 'Clear, attention-grabbing images work best'
    }
    
    suggestions['tiktok_specs'] = {
        'aspect_ratio': '9:16 (Vertical)',
        'recommended_size': '1080x1920px',
        'video_friendly': 'Consider creating 15-60 second videos',
        'tips': 'High energy, eye-catching visuals. Consider text overlays'
    }
    
    suggestions['linkedin_specs'] = {
        'aspect_ratio': '1.91:1 (Landscape)',
        'recommended_size': '1200x627px',
        'professional_tone': 'Clean, professional imagery preferred',
        'tips': 'Infographics and data visualizations perform well'
    }
    
    suggestions['free_sources'] = [
        'Unsplash.com - Search: ' + ', '.join(suggestions['stock_photo_keywords'][:3]),
        'Pexels.com - Search: ' + ', '.join(suggestions['stock_photo_keywords'][:3]),
        'Pixabay.com - Search: ' + ', '.join(suggestions['stock_photo_keywords'][:3]),
    ]
    
    suggestions['ai_tools'] = [
        'Leonardo.ai - Free tier: 150 images/day',
        'Bing Image Creator - Unlimited free (Microsoft account required)',
        'Craiyon.com - Unlimited free (lower quality)',
        'NightCafe - Free credits daily',
    ]
    
    return suggestions

def create_social_media_posts(articles):
    """Create all social media posts for the top 3 articles"""
    
    posts = {
        'instagram': [],
        'facebook': [],
        'tiktok': [],
        'twitter': [],
        'linkedin': []
    }
    
    for i, article in enumerate(articles[:3]):
        image_suggestions = generate_image_suggestions(article)
        
        posts['instagram'].append({
            'article_number': i + 1,
            'title': article['title'],
            'caption': generate_instagram_caption(article, i),
            'url': article['url'],
            'viral_score': article['viral_score'],
            'source_credibility': article['source_credibility'],
            'category': article['category'],
            'image_suggestions': image_suggestions
        })
        
        posts['facebook'].append({
            'article_number': i + 1,
            'title': article['title'],
            'caption': generate_facebook_caption(article),
            'url': article['url'],
            'viral_score': article['viral_score'],
            'source_credibility': article['source_credibility'],
            'category': article['category'],
            'image_suggestions': image_suggestions
        })
        
        posts['tiktok'].append({
            'article_number': i + 1,
            'title': article['title'],
            'caption': generate_tiktok_caption(article),
            'url': article['url'],
            'viral_score': article['viral_score'],
            'source_credibility': article['source_credibility'],
            'category': article['category'],
            'image_suggestions': image_suggestions
        })
        
        posts['twitter'].append({
            'article_number': i + 1,
            'title': article['title'],
            'caption': generate_twitter_caption(article),
            'viral_score': article['viral_score'],
            'source_credibility': article['source_credibility'],
            'category': article['category'],
            'image_suggestions': image_suggestions
        })
        
        posts['linkedin'].append({
            'article_number': i + 1,
            'title': article['title'],
            'caption': generate_linkedin_caption(article),
            'url': article['url'],
            'viral_score': article['viral_score'],
            'source_credibility': article['source_credibility'],
            'category': article['category'],
            'image_suggestions': image_suggestions
        })
    
    return posts

def format_output(articles):
    """Format the articles for posting"""
    output = f"🔥 Top 3 Viral Health Articles - {datetime.now().strftime('%B %d, %Y')}\n\n"
    
    for i, article in enumerate(articles, 1):
        output += f"{i}. **{article['title']}**\n"
        output += f"   📊 Viral Score: {article['viral_score']}/100\n"
        output += f"   ⭐ Source Credibility: {article['source_credibility']}/10\n"
        output += f"   📁 Category: {article['category']}\n"
        output += f"   💡 Why it's viral: {article['why_viral']}\n"
        output += f"   🔗 {article['url']}\n"
        output += f"   📰 Source: {article['source']}\n\n"
    
    return output

def save_individual_platform_posts(posts):
    """Save each platform's posts to separate text files with image guidance"""
    
    for platform, platform_posts in posts.items():
        filename = f"posts_{platform}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"{'='*60}\n")
            f.write(f"{platform.upper()} POSTS - {datetime.now().strftime('%B %d, %Y')}\n")
            f.write(f"{'='*60}\n\n")
            
            for post in platform_posts:
                img = post['image_suggestions']
                
                f.write(f"{'='*60}\n")
                f.write(f"POST #{post['article_number']}\n")
                f.write(f"Title: {post['title']}\n")
                f.write(f"Viral Score: {post['viral_score']}/100\n")
                f.write(f"Source Credibility: {post['source_credibility']}/10\n")
                f.write(f"Category: {post['category']}\n")
                f.write(f"{'='*60}\n\n")
                
                f.write(f"📸 IMAGE GUIDANCE\n")
                f.write(f"{'-'*60}\n")
                f.write(f"Style: {img['style']}\n\n")
                
                f.write(f"🎨 AI Image Prompt (copy this into AI tool):\n")
                f.write(f"{img['ai_prompt']}\n\n")
                
                f.write(f"🔍 Stock Photo Keywords:\n")
                for keyword in img['stock_photo_keywords']:
                    f.write(f"  • {keyword}\n")
                f.write(f"\n")
                
                f.write(f"🎨 Color Palette:\n")
                for color in img['color_palette']:
                    f.write(f"  • {color}\n")
                f.write(f"\n")
                
                f.write(f"✨ Visual Elements to Include:\n")
                for element in img['visual_elements']:
                    f.write(f"  • {element}\n")
                f.write(f"\n")
                
                f.write(f"❌ Do NOT Include:\n")
                for avoid in img['do_not_include']:
                    f.write(f"  • {avoid}\n")
                f.write(f"\n")
                
                if platform == 'instagram':
                    specs = img['instagram_specs']
                elif platform == 'facebook':
                    specs = img['facebook_specs']
                elif platform == 'tiktok':
                    specs = img['tiktok_specs']
                elif platform == 'linkedin':
                    specs = img['linkedin_specs']
                else:
                    specs = img['instagram_specs']
                
                f.write(f"📐 {platform.upper()} Image Specs:\n")
                for key, value in specs.items():
                    f.write(f"  • {key.replace('_', ' ').title()}: {value}\n")
                f.write(f"\n")
                
                f.write(f"🆓 Free Image Sources:\n")
                for source in img['free_sources']:
                    f.write(f"  • {source}\n")
                f.write(f"\n")
                
                f.write(f"🤖 AI Image Tools (Free):\n")
                for tool in img['ai_tools']:
                    f.write(f"  • {tool}\n")
                f.write(f"\n")
                
                f.write(f"{'-'*60}\n\n")
                
                f.write(f"📝 CAPTION\n")
                f.write(f"{'-'*60}\n")
                f.write(f"{post['caption']}\n\n")
                f.write(f"{'='*60}\n\n\n")
        
        print(f"✅ Saved {platform} posts to {filename}")

def create_image_guide_summary(posts):
    """Create a summary guide for all images"""
    
    with open('image_creation_guide.txt', 'w', encoding='utf-8') as f:
        f.write(f"{'='*70}\n")
        f.write(f"IMAGE CREATION GUIDE - {datetime.now().strftime('%B %d, %Y')}\n")
        f.write(f"{'='*70}\n\n")
        
        f.write(f"This guide will help you create or find the perfect images for your posts.\n\n")
        
        f.write(f"{'='*70}\n")
        f.write(f"QUICK START OPTIONS\n")
        f.write(f"{'='*70}\n\n")
        
        f.write(f"Option 1: AI Image Generation (Recommended)\n")
        f.write(f"{'-'*70}\n")
        f.write(f"1. Go to Leonardo.ai or Bing Image Creator (both free)\n")
        f.write(f"2. Copy the 'AI Image Prompt' from the post file\n")
        f.write(f"3. Paste into the AI tool and generate\n")
        f.write(f"4. Download and use!\n\n")
        
        f.write(f"Option 2: Stock Photos (Fastest)\n")
        f.write(f"{'-'*70}\n")
        f.write(f"1. Go to Unsplash.com or Pexels.com\n")
        f.write(f"2. Search using the keywords provided\n")
        f.write(f"3. Download high-res version (free)\n")
        f.write(f"4. Optional: Add text overlay with Canva\n\n")
        
        f.write(f"Option 3: Create in Canva\n")
        f.write(f"{'-'*70}\n")
        f.write(f"1. Use Canva.com (free account)\n")
        f.write(f"2. Select the correct size for your platform\n")
        f.write(f"3. Use the color palette and elements suggested\n")
        f.write(f"4. Add stock photos from Canva's library\n\n")
        
        f.write(f"\n{'='*70}\n")
        f.write(f"IMAGES NEEDED FOR TODAY'S POSTS\n")
        f.write(f"{'='*70}\n\n")
        
        for i, post in enumerate(posts['instagram'][:3], 1):
            img = post['image_suggestions']
            
            f.write(f"\n{'-'*70}\n")
            f.write(f"IMAGE #{i}: {post['title'][:50]}...\n")
            f.write(f"{'-'*70}\n\n")
            
            f.write(f"📸 QUICK COPY AI PROMPT:\n")
            f.write(f"{img['ai_prompt']}\n\n")
            
            f.write(f"🔍 OR SEARCH STOCK PHOTOS FOR:\n")
            f.write(f"{', '.join(img['stock_photo_keywords'])}\n\n")
            
            f.write(f"🎨 USE THESE COLORS:\n")
            f.write(f"{', '.join(img['color_palette'])}\n\n")
            
            f.write(f"Platform-Specific Sizes:\n")
            f.write(f"  Instagram: 1080x1080px (square) or 1080x1350px (portrait)\n")
            f.write(f"  Facebook: 1200x630px (landscape) or 1080x1080px (square)\n")
            f.write(f"  TikTok: 1080x1920px (vertical video)\n")
            f.write(f"  LinkedIn: 1200x627px (landscape)\n")
            f.write(f"  Twitter: 1200x675px (landscape)\n\n")
        
        f.write(f"\n{'='*70}\n")
        f.write(f"FREE TOOLS REFERENCE\n")
        f.write(f"{'='*70}\n\n")
        
        f.write(f"AI Image Generation:\n")
        f.write(f"  • Leonardo.ai - https://leonardo.ai (150 free images/day)\n")
        f.write(f"  • Bing Image Creator - https://bing.com/create (unlimited)\n")
        f.write(f"  • Craiyon - https://craiyon.com (unlimited, lower quality)\n\n")
        
        f.write(f"Stock Photos:\n")
        f.write(f"  • Unsplash - https://unsplash.com\n")
        f.write(f"  • Pexels - https://pexels.com\n")
        f.write(f"  • Pixabay - https://pixabay.com\n\n")
        
        f.write(f"Design & Editing:\n")
        f.write(f"  • Canva - https://canva.com (free account)\n")
        f.write(f"  • Remove.bg - https://remove.bg (background removal)\n")
        f.write(f"  • Photopea - https://photopea.com (free Photoshop alternative)\n\n")
        
    print(f"✅ Created image_creation_guide.txt")

def create_source_analysis_report(all_articles, top_articles):
    """Create a report showing source diversity and credibility"""
    
    with open('source_analysis.txt', 'w', encoding='utf-8') as f:
        f.write(f"{'='*70}\n")
        f.write(f"SOURCE ANALYSIS REPORT - {datetime.now().strftime('%B %d, %Y')}\n")
        f.write(f"{'='*70}\n\n")
        
        # Count articles by source
        source_counts = {}
        for article in all_articles:
            source = article['source']
            if source not in source_counts:
                source_counts[source] = {
                    'count': 0,
                    'credibility': article['source_credibility'],
                    'category': article['category']
                }
            source_counts[source]['count'] += 1
        
        f.write(f"ARTICLES COLLECTED BY SOURCE\n")
        f.write(f"{'-'*70}\n")
        for source, data in sorted(source_counts.items(), key=lambda x: x[1]['count'], reverse=True):
            f.write(f"{source}: {data['count']} articles (Credibility: {data['credibility']}/10, Category: {data['category']})\n")
        
        f.write(f"\n\nTOP 3 SELECTED ARTICLES\n")
        f.write(f"{'-'*70}\n")
        for i, article in enumerate(top_articles, 1):
            f.write(f"{i}. {article['title']}\n")
            f.write(f"   Source: {article['source']} (Credibility: {article['source_credibility']}/10)\n")
            f.write(f"   Viral Score: {article['viral_score']}/100\n")
            f.write(f"   Category: {article['category']}\n\n")
        
        # Average credibility
        avg_credibility = sum(a['source_credibility'] for a in all_articles) / len(all_articles)
        f.write(f"\nAVERAGE SOURCE CREDIBILITY: {avg_credibility:.1f}/10\n")
        
        # Category distribution
        categories = {}
        for article in all_articles:
            cat = article['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        f.write(f"\nCATEGORY DISTRIBUTION\n")
        f.write(f"{'-'*70}\n")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{cat}: {count} articles\n")
    
    print(f"✅ Created source_analysis.txt")

if __name__ == "__main__":
    print("🔍 Starting health article aggregation from 30+ reliable sources...\n")
    
    try:
        # Fetch from all sources
        all_articles = fetch_from_all_sources()
        
        if not all_articles:
            print("❌ No articles found")
            with open('daily_articles.txt', 'w') as f:
                f.write("No articles found from RSS feeds")
        else:
            print(f"\n📝 Processing {len(all_articles)} articles...\n")
            
            # Deduplicate
            print(f"🔄 Removing duplicates...")
            unique_articles = deduplicate_articles(all_articles)
            print(f"✅ {len(unique_articles)} unique articles after deduplication\n")
            
            # Score all articles
            print(f"📊 Calculating viral scores...")
            for article in unique_articles:
                article['viral_score'] = calculate_enhanced_viral_score(article)
                article['why_viral'] = generate_why_viral(article)
            print(f"✅ All articles scored\n")
            
            # Sort and get top 3
            top_articles = sorted(unique_articles, key=lambda x: x['viral_score'], reverse=True)[:3]
            
            print(f"🏆 Top 3 articles selected:\n")
            for i, article in enumerate(top_articles, 1):
                print(f"   {i}. {article['title'][:60]}...")
                print(f"      Score: {article['viral_score']}/100 | Source: {article['source']} ({article['source_credibility']}/10)")
            
            # Generate social media posts
            print(f"\n📱 Generating social media posts...\n")
            social_posts = create_social_media_posts(top_articles)
            
            # Format summary
            formatted_output = format_output(top_articles)
            print(f"\n{formatted_output}")
            
            # Save all outputs
            with open('daily_articles.txt', 'w', encoding='utf-8') as f:
                f.write(formatted_output)
            
            with open('daily_articles.json', 'w', encoding='utf-8') as f:
                json.dump(top_articles, f, indent=2, ensure_ascii=False)
            
            with open('social_media_posts.json', 'w', encoding='utf-8') as f:
                json.dump(social_posts, f, indent=2, ensure_ascii=False)
            
            # Save platform-specific files
            save_individual_platform_posts(social_posts)
            
            # Create guides
            create_image_guide_summary(social_posts)
            create_source_analysis_report(unique_articles, top_articles)
            
            print("\n✅ All files saved successfully!")
            print("\n📁 Generated files:")
            print("   - daily_articles.txt (summary)")
            print("   - daily_articles.json (article data)")
            print("   - social_media_posts.json (all captions)")
            print("   - posts_instagram.txt")
            print("   - posts_facebook.txt")
            print("   - posts_tiktok.txt")
            print("   - posts_twitter.txt")
            print("   - posts_linkedin.txt")
            print("   - image_creation_guide.txt")
            print("   - source_analysis.txt (NEW - shows source diversity)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        with open('daily_articles.txt', 'w') as f:
            f.write(f"Error occurred: {e}\n\n{traceback.format_exc()}")
