import streamlit as st

from ui import render_app

st.set_page_config(
    page_title="AI Physical Science Lab",
    layout="wide"
)

render_app()
