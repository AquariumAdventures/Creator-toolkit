import streamlit as st
import openai
from openai import OpenAI


def run():
    st.title("🎯 YouTube Title Optimiser")
    st.markdown("""
    Step 3 of the Creator Toolkit

    Use this tool to craft a compelling, keyword-rich YouTube video title designed to boost CTR and SEO based on your chosen niche and keyword.
    """)

    with st.form("title_form"):
        topic = st.text_input("🧠 What is your video about? (Topic/Niche)", placeholder="e.g. planted aquariums, discus care")
        keyword = st.text_input("🔑 What keyword or phrase are you targeting?", placeholder="e.g. best fish for beginners")
        tone = st.selectbox("🎙️ Choose your tone", ["Neutral", "Excited", "Educational", "Funny", "Controversial"])
        goal = st.selectbox("🎯 Primary goal", ["Max CTR (Clickbait-ish)", "Balanced (CTR + SEO)", "SEO-Optimised"])
        temp_label = st.radio("🧪 Creativity level", ["Safe", "Balanced", "Wild"], horizontal=True)
        temperature = {"Safe": 0.3, "Balanced": 0.7, "Wild": 1.0}[temp_label]
        submitted = st.form_submit_button("Generate Title Suggestions")

    if submitted and keyword:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])

        prompt = f"""
        You are a YouTube strategist and headline copywriter.

        Based on the following:
        - Topic: {topic}
        - Keyword: {keyword}
        - Tone: {tone}
        - Goal: {goal}

        Generate 3 to 5 optimised YouTube video titles. Each title must:
        - Include the keyword or a close variation
        - Be no longer than 70 characters
        - Be designed to increase CTR and/or rank for search

        After each title, include a brief insight (1–2 sentences) on why it works.

        Format:
        Title: <title>
        Insight: <why this works>
        """

        with st.spinner("Generating titles..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a YouTube strategist that specialises in writing video titles."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=800
                )

                output = response.choices[0].message.content.strip()
                entries = output.split("Title:")
                for entry in entries:
                    if not entry.strip():
                        continue
                    lines = entry.strip().split("\n")
                    title = lines[0].strip()
                    insight = next((line.replace("Insight:", "").strip() for line in lines if "Insight:" in line), "")

                    st.markdown(f"### 🎬 {title}")

                    # Evaluate balance score (basic rule: keyword in title + length < 70)
                    score = 0
                    if keyword.lower() in title.lower():
                        score += 5
                    score += max(0, 5 - int((len(title) - 50) / 5)) if len(title) <= 70 else 0
                    score = min(score, 10)

                    color = "green" if score >= 7 else "orange" if score >= 4 else "red"

                    st.markdown(f"""
                        <div style='display: inline-block; background: {color}; color: white; padding: 4px 10px; border-radius: 999px; font-weight: bold; font-size: 12px;'>
                        Score: {score}/10
                        </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"<span style='color: #999;'>{insight}</span>", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Failed to generate title suggestions: {e}")
