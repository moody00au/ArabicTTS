import streamlit as st
import openai
from google.cloud import texttospeech
from google.oauth2 import service_account
import json

# Retrieve your OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Google Cloud Text-to-Speech client setup with Streamlit secrets
google_credentials = service_account.Credentials.from_service_account_info(
    st.secrets["GOOGLE_CLOUD_CREDENTIALS"]
)
google_tts_client = texttospeech.TextToSpeechClient(credentials=google_credentials)
