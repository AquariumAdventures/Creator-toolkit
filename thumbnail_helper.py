import streamlit as st


def run():
    st.title("🎨 Thumbnail Helper")
    st.markdown("""
    Step 5 of the Creator Toolkit

    Design high-impact thumbnails that drive views and clicks.
    """)

    with st.expander("📚 Why Thumbnails Matter"):
        st.markdown("""
        Your video thumbnail is your **first impression** — it determines whether someone clicks or scrolls past. Your comtent can be a cinematic masterpiece but if people don't
        notice or aren't interested in your thumbnail, they might scroll on by.
        
        Here are some proven types of thumbnails:

        - **The Burning question** ❓
          - Pose the question that intrigues! Hook the viewer by speaking to their curiosity or concerns about your topic.
        - **Shocking facts** ⚡
          - Data can grab attention too - sharing a snippit of a shocking fact makes them need to know more context.
        - **The Reaction Face** 😲
          - Close-up of an expressive face. Works well for emotional or personal content.
        - **Before & After Split** 📸
          - Great for tutorials, makeovers, and results-driven videos.
        - **The Highlighted Object** 🎯
          - One clear focal item (a product, fish tank, gear, etc). Minimal clutter.
        - **Bold Text Overlay** 🆘
          - A few punchy words that add drama, emotion, or a cliffhanger.
        - **Comparisons** 🆚
          - The 'versus' format draws people in to hear your take on what the differences or similarities of things are.
        - **Quotes or soundbites** 🗨️
          - An interesting snippet acts as a preview and cultivates interest.

        *These are just some suggestions, not an exhaustive list - make use of A/B testing features to try out different approaches*
        """)

    st.markdown("## 🛠️ Let's Design Your Perfect Thumbnail")
    with st.form("thumb_form"):
        title = st.text_input("🎬 Video Title", placeholder="e.g. Best Plants for Discus Aquariums")
        keyword = st.text_input("🔑 Keyword or Phrase", placeholder="e.g. discus aquarium plants")
        vibe = st.selectbox("🎯 Tone or Emotion", ["Excited", "Serious", "Curious", "Funny", "Shocking"])
        goal = st.selectbox("📈 Strategy", ["Stand out from competition", "Make people curious", "Reinforce the title", "Brand consistency"])
        submitted = st.form_submit_button("Suggest Thumbnail Concepts")

    if submitted and title and keyword:
        import openai
        from openai import OpenAI
        client = OpenAI(api_key=st.secrets["api"]["openai_key"])

        with st.spinner("Generating thumbnail ideas with GPT..."):
            try:
                thumb_prompt = f"""
                You are a YouTube strategist and visual designer. Suggest 3 compelling, creative YouTube thumbnail ideas for the following:

                - Title: {title}
                - Keyword: {keyword}
                - Tone/Emotion: {vibe}
                - Strategy Goal: {goal}

                Each suggestion should include:
                - Description: A vivid visual scene (composition, subject, colors, layout)
                - Insight: Why this visual style would be effective
                - Prompt: A DALL·E-compatible AI image prompt to generate the thumbnail image

                Format:
                Concept 1:
                Description: <...>
                Text: <...>
                Insight: <...>
                """

                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a creative YouTube thumbnail designer."},
                        {"role": "user", "content": thumb_prompt}
                    ],
                    temperature=0.8,
                    max_tokens=800
                )

                result = response.choices[0].message.content.strip()
                st.markdown("## 💡 AI-Generated Thumbnail Concepts")
                for i, concept in enumerate(result.split("Concept ")):
                    if not concept.strip():
                        continue
                    concept_lines = concept.strip().splitlines()
                    label = f"Concept {i}"
                    st.markdown(f"### {label}")
                    st.markdown("\n".join(concept_lines))
                    prompt_line = next((line for line in concept_lines if line.lower().startswith("prompt:")), None)
                    if prompt_line:
                        prompt_text = prompt_line.replace("Prompt:", "").strip()
                        if st.button(f"Generate this ({label})", key=f"gen_{i}"):
                            with st.spinner("Generating thumbnail image..."):
                                try:
                                    image_response = client.images.generate(
                                        model="dall-e-3",
                                        prompt=prompt_text,
                                        size="1792x1024",
                                        quality="standard",
                                        n=1
                                    )
                                    image_url = image_response.data[0].url
                                    st.image(image_url, caption=f"Generated for {label}", use_container_width=True)
                                    with st.expander("💾 Download this image"):
                                        st.markdown(f"[Right click here to download]({image_url})")
                                        st.info("If the link doesn't work directly, right click the image above and select 'Save image as...'")
                                except Exception as e:
                                    st.error(f"❌ Failed to generate image: {e}")

            except Exception as e:
                st.error(f"❌ Failed to generate thumbnail ideas: {e}")

    st.markdown("---")
    st.markdown("## 🎨 Want to Create or Improve a Thumbnail?")
    choice = st.radio("Choose an option:", ["Generate from scratch", "Upload an image to enhance"])

    if choice == "Generate from scratch":
        prompt = st.text_area("Describe the thumbnail you want", placeholder="e.g. Bright green tank with fish looking at camera, dramatic lighting")
        if st.button("Generate Thumbnail Image") and prompt:
            with st.spinner("Generating image..."):
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=st.secrets["api"]["openai_key"])
                    response = client.images.generate(
                        model="dall-e-3",
                        prompt=prompt,
                        size="1792x1024",
                        quality="standard",
                        n=1
                    )
                    image_url = response.data[0].url
                    st.image(image_url, caption="AI-Generated Thumbnail", use_container_width=True)
                    with st.expander("💾 Download this image"):
                        st.markdown(f"[Right click here to download]({image_url})")
                        st.info("If the link doesn't work directly, right click the image above and select 'Save image as...'")
                except Exception as e:
                    st.error(f"❌ Failed to generate image: {e}")

    elif choice == "Upload an image to enhance":
        uploaded = st.file_uploader("Upload your current thumbnail image", type=["png", "jpg", "jpeg"])
        enhance_text = st.text_input("What would you like to add or improve?", placeholder="e.g. Add bold text, improve contrast")
        if st.button("Enhance Thumbnail"):
            if uploaded:
                st.image(uploaded, caption="Your Uploaded Image", use_container_width=True)
                st.info(f"🛠️ Enhancement suggestion: {enhance_text}")
                st.warning("🚧 Image editing features coming soon.")
            else:
                st.error("Please upload an image to enhance.")
