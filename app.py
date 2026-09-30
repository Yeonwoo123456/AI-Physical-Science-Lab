import streamlit as st
from ui import render_app

st.set_page_config(
    page_title="AI Physical Science Lab",
    page_icon="🔬",
    layout="wide"
)

render_app()
