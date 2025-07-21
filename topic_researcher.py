import streamlit as st
import math
from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt
from iso639 import languages
import isodate
from openai import OpenAI

def run():
    youtube = build('youtube', 'v3', developerKey=st.secrets["api"]["youtube_key"])
    client = OpenAI(api_key=st.secrets["api"]["openai_key"])

    def search_videos(keyword, published_after, max_results=100):
        all_items = []
        next_page_token = None
        while len(all_items) < max_results:
            response = youtube.search().list(
                q=keyword,
                type='video',
                part='id,snippet',
                maxResults=min(50, max_results - len(all_items)),
                publishedAfter=published_after,
                pageToken=next_page_token
            ).execute()
            all_items.extend(response['items'])
            next_page_token = response.get('nextPageToken')
            if not next_page_token:
                break
        return all_items

    def get_video_details(video_ids):
        details = []
        for i in range(0, len(video_ids), 50):
            batch = video_ids[i:i+50]
            response = youtube.videos().list(
                part='snippet,statistics,contentDetails',
                id=','.join(batch)
            ).execute()
            details.extend(response['items'])
        return details

    def get_channel_info(channel_id):
        response = youtube.channels().list(
            part='snippet,statistics',
            id=channel_id
        ).execute()
        channel = response['items'][0]
        subs = int(channel['statistics'].get('subscriberCount', 0))
        description = channel['snippet'].get('description', '').lower()
        avatar_url = channel['snippet']['thumbnails']['default']['url']
        return subs, description, avatar_url

    def classify_description(desc):
        blob = TextBlob(desc)
        sentiment_score = blob.sentiment.polarity
        if sentiment_score > 0.3:
            sentiment_text = "Positive tone"
        elif sentiment_score < -0.3:
            sentiment_text = "Negative tone"
        else:
            sentiment_text = "Neutral tone"
        if "tutorial" in desc.lower() or "how to" in desc.lower():
            style = "educational"
        elif "funny" in desc.lower() or "joke" in desc.lower():
            style = "funny"
        elif "shocking" in desc.lower() or "unbelievable" in desc.lower():
            style = "shocking"
        else:
            style = "entertaining"
        return desc[:200], style, sentiment_score, sentiment_text

    def parse_duration(iso_duration):
        try:
            duration = isodate.parse_duration(iso_duration)
            return duration.total_seconds() / 60
        except:
            return None

    def render_viral_badge(score):
        percentage = min(score, 1.5)
        if score < 0.2:
            colour = "red"
        elif score < 0.5:
            colour = "orange"
        elif score < 1:
            colour = "blue"
        else:
            colour = "limegreen"
        dasharray = 113
        dashoffset = dasharray * (1 - min(percentage, 1))
        svg = f"""
        <div style='display: block; text-align: left; margin-top: 0; margin-left: 0; display: flex; flex-direction: column; align-items: center;'>
            <div style='font-size: 12px; font-weight: bold; margin-bottom: 4px;'>Viral Score</div>
            <svg width=\"70\" height=\"70\" viewBox=\"0 0 40 40\">
                <circle cx=\"20\" cy=\"20\" r=\"18\" stroke=\"#ccc\" stroke-width=\"4\" fill=\"none\"/>
                <circle
                    cx=\"20\" cy=\"20\" r=\"18\"
                    stroke=\"{colour}\" stroke-width=\"4\"
                    stroke-dasharray=\"{dasharray}\" stroke-dashoffset=\"{dashoffset}\"
                    fill=\"none\" stroke-linecap=\"round\"
                    transform=\"rotate(-90 20 20)\"
                />
                <text x=\"50%\" y=\"52%\" text-anchor=\"middle\" dominant-baseline=\"middle\" font-size=\"12\" font-weight=\"bold\" fill=\"#f2f2f2\">{score:.1f}</text>
            </svg>
        </div>
        """
        return svg

    def generate_video_insight(row):
        prompt = f"""
You're a YouTube growth strategist. Analyze this video to identify repeatable, audience-agnostic techniques that may have contributed to its strong performance.

Please avoid restating obvious metrics like high views, likes, or comments unless they're part of a clear strategy (e.g. controversy, challenge, timing). Be specific and actionable.

Explain **how a creator could test, adapt, or apply** these tactics to their own videos — including practical steps, phrasing, visuals, or formats.

Also explain **when NOT to use** any tactic mentioned (e.g. "only works if..." or "avoid this unless...").

**Video Context**:
- Title: {row['Title']}
- Description: {row['Summary']}
- Style: {row['Style']}
- Sentiment: {row['Sentiment Text']} ({row['Sentiment Score']})
- Thumbnail URL: {row['Thumbnail']}
- Subscribers: {row['Subscribers']}
- Views: {row['Views']}
- Likes: {row['Likes']}
- Comments: {row['Comments']}
- Duration: {row['Duration (min)']} min
- Keyword Match: {row['Matched Keyword']}"""

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a YouTube marketing expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Insight generation failed: {str(e)}"

    st.title("📊 Topic Researcher")
    st.markdown("""
    Step 1 of the Creator Toolkit

    Research what is working in your target niche!
    """)
    with st.expander("ℹ️ What is the Viral Score?"):
        st.markdown("""
        **Viral Score** = A weighted algorithm loosely based on Views ÷ Subscribers
        - A score > 1 means the video has performed well relative to the amount of subscribers.
        - Often indicates viral reach beyond the channel’s audience, or substanial enough of an amout of views to be considered viral by any other means.
        """)

    search_expander = st.expander("🔧 Search Criteria & Filters", expanded=True)
    with search_expander:
        niches = st.text_input("Enter niche topics:", "fishkeeping|aquascaping|planted tank")
        months_back = st.slider("Look back how many months?", 1, 12, 6)
        max_results = st.slider("Number of results per niche (max 200):", 5, 200, 50)

        subscriber_steps = [0, 10, 50, 100, 500, 1000, 3000, 7000, 10000, 20000, 50000, 100000, 250000, 500000, 1000000]
        subs_min, subs_max = st.select_slider("Subscriber range", options=subscriber_steps, value=(0, 1000000))

        view_steps = [0, 100, 500, 1000, 5000, 10000, 25000, 50000, 100000, 250000, 500000, 1000000]
        views_min, views_max = st.select_slider("View range", options=view_steps, value=(0, 500000))

        likes_filter = st.checkbox("Filter by likes?")
        if likes_filter:
            likes_min, likes_max = st.slider("Like count range", 0, 1000000, (500, 10000))
        else:
            likes_min, likes_max = 0, 999999

        comments_filter = st.checkbox("Filter by comments?")
        if comments_filter:
            comments_min, comments_max = st.slider("Comment count range", 0, 10000, (10, 500))
        else:
            comments_min, comments_max = 0, 999999

        duration_filter = st.checkbox("Filter by video duration (minutes)?")
        shorts_toggle = st.radio("Video type:", ["All", "Shorts only", "Exclude Shorts"], horizontal=True)
        if duration_filter:
            dur_min, dur_max = st.slider("Duration range (minutes)", 0, 240, (1, 20))
        else:
            dur_min, dur_max = 0, 240

        sort_by = st.selectbox("Sort results by:", ["Viral Score", "Views", "Likes", "Comments", "Subscribers"], index=0)
        sort_order = st.radio("Sort order:", ["Descending", "Ascending"], horizontal=True)

        language_options = {
            "English": "en", "Spanish": "es", "German": "de", "French": "fr", "Portuguese": "pt",
            "Russian": "ru", "Japanese": "ja", "Hindi": "hi", "Arabic": "ar", "Korean": "ko"
        }
        language_label = st.selectbox("Select video language:", options=list(language_options.keys()), index=0)
        language_filter = language_options[language_label]

        match_mode = st.radio("Niche match mode:", ["Loose (any keyword)", "Strict (all keywords)"], horizontal=True)

        creator_filter = st.text_input("From specific creators? (optional, comma-separated names)", "")
        search_clicked = st.button("🔍 Find Videos")

    if search_clicked:
        st.info("🔄 Searching YouTube and analyzing results...")
        published_after = (datetime.now(timezone.utc) - timedelta(days=30 * months_back)).isoformat("T")
        topic = niches.strip()
        search_results = search_videos(topic, published_after, max_results)
        video_ids = [item['id']['videoId'] for item in search_results]
        videos = get_video_details(video_ids)

        all_results = []
        for video in videos:
            snippet = video['snippet']
            # creator_names = [name.strip().lower() for name in creator_filter.split(',') if name.strip()]
            # if creator_names and snippet['channelTitle'].lower() not in creator_names:
            #     continue
            if snippet.get('defaultAudioLanguage', 'en')[:2] != language_filter.lower():
                continue

            stats = video['statistics']
            content = video.get('contentDetails', {})
            views = int(stats.get('viewCount', 0))
            likes = int(stats.get('likeCount', 0))
            comments = int(stats.get('commentCount', 0))
            duration = parse_duration(content.get('duration', 'PT0M'))

            if shorts_toggle == "Shorts only" and (duration is None or duration > 2.0):
                continue
            if shorts_toggle == "Exclude Shorts" and (duration is not None and duration <= 2.0):
                continue

            channel_id = snippet['channelId']
            subs, channel_description, avatar_url = get_channel_info(channel_id)
            desc = snippet.get('description', '')
            combined_text = f"{snippet['title']} {desc} {channel_description}".lower()
            keywords = [k.strip().lower() for k in topic.split('|')]

            if match_mode == "Strict (all keywords)" and not all(keyword in combined_text for keyword in keywords):
                continue

            summary, style, sentiment, sentiment_text = classify_description(desc)
            is_viral = views > subs
            adjusted_subs = subs
            # Adjust subscriber count based on thresholds
            if subs < 500:
                adjusted_subs = subs * 6.0
            elif subs < 1000:
                adjusted_subs = subs * 4.0
            elif subs < 2500:
                adjusted_subs = subs * 3.0
            elif subs < 5000:
                adjusted_subs = subs * 2.0
            elif subs < 10000:
                adjusted_subs = subs * 1.7
            elif subs < 20000:
                adjusted_subs = subs * 1.5
            elif subs < 50000:
                adjusted_subs = subs * 0.90
            elif subs < 100000:
                adjusted_subs = subs * 0.80
            elif subs < 500000:
                adjusted_subs = subs * 0.75
            elif subs < 1000000:
                adjusted_subs = subs * 0.40
            else:
                adjusted_subs = subs * 0.35

            viral_score = round(views / adjusted_subs, 2) if adjusted_subs > 0 else 0

            if subs < subs_min or subs > subs_max:
                continue
            if views < views_min or views > views_max:
                continue
            if likes < likes_min or likes > likes_max:
                continue
            if comments < comments_min or comments > comments_max:
                continue
            if duration is not None and (duration < dur_min or duration > dur_max):
                continue

            all_results.append({
                'Topic': topic,
                'Title': snippet['title'],
                'Channel': snippet['channelTitle'],
                'Subscribers': subs,
                'Views': views,
                'Likes': likes,
                'Comments': comments,
                'Duration (min)': round(duration or 0, 2),
                'Published': snippet['publishedAt'],
                'Link': f"https://www.youtube.com/watch?v={video['id']}",
                'Summary': summary,
                'Style': style,
                'Sentiment Score': sentiment,
                'Sentiment Text': sentiment_text,
                'Thumbnail': snippet['thumbnails']['medium']['url'],
                'Viral': is_viral,
                'Viral Score': viral_score,
                'Matched Keyword': ", ".join([k for k in keywords if k in combined_text]) or topic,
                'Avatar': avatar_url
            })

        df = pd.DataFrame(all_results)
        st.session_state['results_df'] = df

    if 'results_df' in st.session_state:
        df = st.session_state['results_df']
        if df.empty:
            st.warning("No results matched your criteria.")
        else:
            st.success(f"✅ Found {len(df)} videos matching your criteria.")

            for i, row in df.iterrows():
                with st.container():
                    st.markdown(f"### 🔥 [{row['Title']}]({row['Link']})")
                    cols = st.columns([1], gap="small")
                    with cols[0]:
                        st.markdown("""
    <div style='display: flex; align-items: flex-start; gap: 16px;'>
        <img src='""" + row['Thumbnail'] + """' width='200'/>
        <div style='text-align: center;'>
            <img src='""" + row['Avatar'] + """' width='100'/><br>
            <div style='font-size: 16px; font-weight: 600; text-align: center;'>""" + row['Channel'] + """</div>
        </div>
        <div>""" + render_viral_badge(row['Viral Score']) + """</div>
    </div>
    """, unsafe_allow_html=True)
                    
                    
                    # Already shown above; remove duplicate badge
                    # st.markdown(badge_svg, unsafe_allow_html=True)
                    st.markdown(f"**Subscribers**: {row['Subscribers']} | **Views**: {row['Views']} | **Likes**: {row['Likes']} | **Comments**: {row['Comments']}  ")
                    st.markdown(f"**Duration**: {row['Duration (min)']} min | **Published**: {row['Published']}")
                    st.markdown(f"**Style**: {row['Style']} | **Sentiment**: {row['Sentiment Text']} ({row['Sentiment Score']:.2f})")
                    st.markdown(f"**Summary**: {row['Summary']}")
                    st.markdown(f"**Matched Keyword**: _{row['Matched Keyword']}_")

                    if st.button(f"🧠 Why did this go viral?", key=f"insight_{i}"):
                        st.markdown("---")
                        st.image(row['Thumbnail'], width=320)
                        st.markdown(f"### [{row['Title']}]({row['Link']})")
                        insights = generate_video_insight(row)
                        st.info(insights)
                        st.markdown("---")


