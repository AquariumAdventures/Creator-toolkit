import streamlit as st
import time
import math

# Import tool modules
import topic_researcher
import keyword_generator
import title_optimiser
import description_writer
import thumbnail_helper

# Set page layout early
st.set_page_config(page_title="Creator Toolkit", layout="wide")

# Fix: One-time rerun after short delay to allow layout to stabilize
if 'first_run_done' not in st.session_state:
    st.session_state.first_run_done = True
    time.sleep(0.1)
    st.rerun()

# Version indicator
st.info("🟢 Creator Toolkit Live — v1 | 21st July 2025")

# Sidebar navigation
st.sidebar.title("📺 Creator Toolkit")

# Optional: manual reload button
if st.sidebar.button("🔁 Reload App"):
    st.rerun()

# Menu setup
pages = {
    "🏠 Home": "home",
    "🔍 Topic Researcher": "topic",
    "🔑 Keyword / Phrase Generator": "keywords",
    "✍️ Title Optimiser": "title",
    "📝 Description Writer": "description",
    "🎨 Thumbnail Helper": "thumb",
}

default_page = list(pages.keys())[0]

# Store nav state
if 'page' not in st.session_state:
    st.session_state.page = default_page

nav = st.sidebar.radio("Choose a tool:", list(pages.keys()), index=list(pages.keys()).index(st.session_state.page))

# If nav changed, update and rerun
if nav != st.session_state.page:
    st.session_state.page = nav
    st.rerun()

# Routing logic
if st.session_state.page == "🏠 Home":
    st.title("🎯 Creator Toolkit")
    st.markdown("""
    Welcome to the **Creator Toolkit** — a 5 step suite of tools to help video creators:

    - Research what's working in their niche
    - Dial in on the best keywords and phrases
    - Generate scroll-stopping **titles**
    - Write compelling **descriptions**
    - Design effective **thumbnails**

    Choose a module from the left sidebar to get started.
    """)

elif st.session_state.page == "🔍 Topic Researcher":
    topic_researcher.run()

elif st.session_state.page == "✍️ Title Optimiser":
    title_optimiser.run()

elif st.session_state.page == "📝 Description Writer":
    description_writer.run()

elif st.session_state.page == "🎨 Thumbnail Helper":
    thumbnail_helper.run()

elif st.session_state.page == "🔑 Keyword / Phrase Generator":
    keyword_generator.run()
