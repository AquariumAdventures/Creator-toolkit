import streamlit as st
import openai
from openai import OpenAI


def run():
    st.title("📝 YouTube Description Writer")
    st.markdown("""
    Step 4 of the Creator Toolkit

    Create a compelling and keyword-rich YouTube video description tailored to your video title, audience and tone.
    """)

    with st.form("desc_form"):
        title = st.text_input("🎬 Video title", placeholder="e.g. Top 10 Plants for Your Discus Aquarium")
        keyword = st.text_input("🔑 Targeted keyword or phrase", placeholder="e.g. discus aquarium plants")
        topic = st.text_input("🧠 Video topic / niche", placeholder="e.g. planted aquariums, discus care")
        tone = st.selectbox("🎙️ Description tone", ["Neutral", "Friendly", "Expert", "Salesy", "Funny"])
        goal = st.selectbox("🎯 Primary goal", ["Educate", "Engage", "Convert (CTA-driven)", "Balanced"])
        temp_label = st.radio("🧪 Creativity level", ["Safe", "Balanced", "Wild"], horizontal=True)
        temperature = {"Safe": 0.3, "Balanced": 0.7, "Wild": 1.0}[temp_label]
        submitted = st.form_submit_button("Generate Description")

    if submitted and title and keyword:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])

        prompt = f"""
        You are a YouTube strategist and copywriter. Write an effective, engaging YouTube video description based on the following:

        - Title: {title}
        - Topic: {topic}
        - Keyword: {keyword}
        - Tone: {tone}
        - Goal: {goal}

        The description should:
        - Be 1–3 paragraphs
        - Naturally use the keyword or phrase
        - Include calls to action if appropriate (subscribe, comment, visit links)
        - Help with viewer retention and SEO

        At the end, include a short explanation of how the description supports the goal.
        """

        with st.spinner("Generating description..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a YouTube strategist who writes high-performing video descriptions."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=temperature,
                    max_tokens=800
                )

                output = response.choices[0].message.content.strip()
                st.session_state.generated_description = output
                st.markdown("## ✍️ Generated Description")
                st.markdown(output)

                st.markdown("---")
                

            except Exception as e:
                st.error(f"❌ Failed to generate description: {e}")

    # Revision logic outside form block
    if "generated_description" in st.session_state and "api" in st.secrets and "openai_key" in st.secrets["api"]:
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])
        st.markdown("---")
        st.subheader("🔁 Want to revise this?")
        user_feedback = st.text_area("Tell us what you'd like to change or improve", placeholder="Make it more concise... remove the second paragraph...")
        if st.button("Revise Description") and user_feedback:
            revision_prompt = f"""
            Please revise the following YouTube video description:

            {st.session_state.generated_description}

            Based on this user feedback:
            {user_feedback}

            Provide the improved description only.
            """
            with st.spinner("Revising..."):
                try:
                    revision = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are a helpful YouTube strategist."},
                            {"role": "user", "content": revision_prompt}
                        ],
                        temperature=temperature,
                        max_tokens=600
                    )
                    revised_output = revision.choices[0].message.content.strip()
                    st.markdown("## ✨ Revised Description")
                    st.markdown(revised_output)
                except Exception as e:
                    st.error(f"❌ Failed to revise description: {e}")
