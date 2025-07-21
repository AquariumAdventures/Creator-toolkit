import streamlit as st
import math
import warnings
from pytrends.request import TrendReq

# Import tool modules
import topic_researcher
#import title_optimiser
#import description_writer
#import thumbnail_helper

def get_trend_score(keyword: str) -> int:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=FutureWarning)
            pytrends = TrendReq(hl='en-US', tz=360)
            pytrends.build_payload([keyword], cat=0, timeframe='today 12-m', geo='', gprop='youtube')
            data = pytrends.interest_over_time()

        if not data.empty:
            avg_score = int(data[keyword].mean())
            return round(min(avg_score / 10, 10))
        else:
            return None
    except Exception:
        return None

def get_score_label(score):
    if score >= 8:
        return "Excellent Potential"
    elif score >= 6:
        return "Strong Opportunity"
    elif score >= 4:
        return "Balanced Potential"
    elif score >= 2:
        return "Low Potential"
    else:
        return "High Risk"

# Sidebar Navigation
def run():
    st.title("🔑 Keyword / Phrase Generator")
    st.markdown("""
    Step 2 of the Creator Toolkit
    
    Enter a few words or a phrase related to your video topic. We'll analyze and rank them (and suggest alternatives) using a combination of
    live trend analysis and AI powered insights
    """)

    with st.expander("ℹ️ How does this work"):
        st.markdown("""
        We perform analysis of your suggested search keywords or keyphrases against the following criteria:

        - **Popularity** – Level of interest or search volume
        - **Competition** – How saturated is that term
        - **SEO potential** – What chance does it have to rank

        We use live data from tools like Google Trends, YouTube Search data and other publicly available search metrics along with OpenAI's language model and general popularity/intent signals
        to calculate a score for the keyword or phrase based on its potential to perform well. The ideal (but practically unobtainable) goal is 10/10 for popularity with 1/10 for competition with
        a high SEO potential – These sort of results are extremely rare so bear in mind that in reality scores above 6 are good, above 7 amazing – but rare! This is a game of fine margins. 
        Our tool will consider these different criteria options along with other ranking and niche inputs, live at the current time you perform the search (not referencing a stored out-of-date 
        database) to determine a likelihood of performing well.

        Keywords are just one part of your strategy and while important can only perform relative to existing channel size, relevance and popularity. Keep grinding!

        Also consider that sometimes it is worth targeting lower value keywords, especially in well-defined niches or very targeted subject matter
        or using longer keyphrases in oversaturated markets.
        """)

    user_input = st.text_area("🔍 Topic words or phrases:", placeholder="e.g. aquascaping, nano planted tank, fish tank setup")

    if st.button("Analyze Keywords"):
        if not user_input.strip():
            st.warning("Please enter at least one keyword or phrase.")
        else:
            import openai
            from openai import OpenAI
            client = OpenAI(api_key=st.secrets["api"]["openai_key"])

            with st.spinner("Analyzing with GPT..."):
                prompt = f"""
                You are a video content strategist. Analyze the following keywords or phrases:

                {user_input}

                For each one:
                - Score its popularity from 1–10
                - Score its likely competition from 1–10 (higher = more competitive)
                - Suggest if it's good for ranking or too saturated
                - Recommend three alternative keywords or phrases that are more specific or have better SEO opportunity

                Most importantly, include a unique and helpful insight for each keyword AND each alternative:
                - Explain why this keyword might perform well or not
                - Suggest content types, audience appeal, or strategic SEO intent
                - Tailor the insight to the specific keyword — do not reuse language or generic phrases like "offers better SEO opportunity"

                Return a markdown table using six columns:
                | Keyword | Popularity | Competition | Rankability | Alternatives | Insight |
                """

                import re
                try:
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an SEO and YouTube keyword expert."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.0,
                        max_tokens=1000
                    )

                    content = response.choices[0].message.content.strip()
                    lines = content.splitlines()
                    rows = [line for line in lines if line.strip().startswith("|") and not line.strip().startswith("|---")]

                    if not rows:
                        st.error("❌ GPT did not return a proper table format.")
                        st.code(content)
                        return

                    from collections import defaultdict
                    shown_keywords = set()
                    raw_keywords = [kw.strip().lower() for kw in user_input.replace(',', '\n').splitlines() if kw.strip()]

                    keyword_blocks = []
                    keyword_lookup = {}
                    main_keywords = set()

                    for row in rows[1:]:
                        cols = [c.strip() for c in row.strip('|').split('|')]
                        if len(cols) < 6:
                            continue

                        keyword, popularity, competition, rankability, alternatives, notes = cols
                        alt_list = [a.strip() for a in alternatives.split(',') if a.strip()]
                        try:
                            popularity = get_trend_score(keyword) or int(popularity)
                            competition = int(competition)
                        except:
                            continue

                        score = round(10 - math.sqrt((10 - popularity)**2 + competition**2) / 2, 1)

                        block = {
                            "keyword": keyword,
                            "popularity": popularity,
                            "competition": competition,
                            "score": score,
                            "rankability": ('Excellent' if score >= 8 else 'Good' if score >= 6 else 'Medium' if score >= 4 else 'Low'),
                            "alternatives": alt_list,
                            "notes": notes
                        }
                        keyword_blocks.append(block)
                        keyword_lookup[keyword.lower()] = block
                        if keyword.lower() in raw_keywords:
                            main_keywords.add(keyword.lower())

                        for alt in alt_list:
                            alt_key = alt.lower()
                            if alt_key not in keyword_lookup:
                                keyword_lookup[alt_key] = {
                                    "keyword": alt,
                                    "popularity": None,
                                    "competition": None,
                                    "score": None,
                                    "rankability": None,
                                    "notes": notes
                                }

                    # Display results
                    for block in keyword_blocks:
                        is_main = block["keyword"].lower() in main_keywords
                        if is_main:
                            st.subheader(f'📌 {block["keyword"]}')
                        else:
                            st.markdown(f'**{block["keyword"]}**')

                        cols = st.columns([1, 4])
                        with cols[0]:
                            color = "green" if block["score"] and block["score"] >= 6 else "orange" if block["score"] else "gray"
                            st.markdown(f"""
                                <div style="text-align: center;">
                                    <div style="border: 4px solid {color}; border-radius: 50%; width: 60px; height: 60px; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: bold;">
                                        {block["score"] if block["score"] is not None else "?"}
                                    </div>
                                    <div style="font-size: 12px; margin-top: 4px; color: #999;">{get_score_label(block["score"]) if block["score"] else "N/A"}</div>
                                </div>
                            """, unsafe_allow_html=True)

                        with cols[1]:
                            st.markdown(f"""
                            **Popularity:** {block["popularity"]}/10  |  **Competition:** {block["competition"]}/10  
                            **Result:** {block["rankability"] if block["rankability"] else "Unknown"}
                            """)
                            if block["notes"]:
                                st.markdown(block["notes"])
                            if block["alternatives"]:
                                st.markdown(f"_Suggested Alternatives:_ {', '.join(block['alternatives'])}")

                except Exception as e:
                    st.error(f"❌ Failed to generate insights: {e}")
