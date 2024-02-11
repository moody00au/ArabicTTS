import streamlit as st
import openai
from google.cloud import texttospeech
from google.oauth2 import service_account
import json

# Retrieve your OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Parse the Google Cloud credentials from Streamlit secrets directly
google_credentials = service_account.Credentials.from_service_account_info(
    st.secrets["GOOGLE_CLOUD_CREDENTIALS"]
)
google_tts_client = texttospeech.TextToSpeechClient(credentials=google_credentials)

def add_diacritics(text):
    try:
        response = openai.Completion.create(
            model="gpt-4",
            prompt=f"Add diacritics to this Arabic text: '{text}'.",
            temperature=0.7,
            max_tokens=3000
        )
        # Adjusted to match the new response structure
        return response.choices[0].text.strip()
    except Exception as e:
        return f"Failed to add diacritics: {str(e)}"

def synthesize_speech(text_with_harakat):
    synthesis_input = texttospeech.SynthesisInput(text=text_with_harakat)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ar-XA",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = google_tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content


def read_text_file(file):
    """Read text from the uploaded file."""
    text = file.read()
    # Assuming the uploaded file is UTF-8 encoded text
    return text.decode("utf-8")

# Streamlit UI
st.title("Arabic Text Diacritization and TTS Application")

# Option for direct text input or file upload
user_input = st.text_area("Enter Arabic text here:", "هنا يمكنك كتابة النص العربي")
uploaded_file = st.file_uploader("Or upload a text file:", type=["txt"])

if uploaded_file is not None:
    file_text = read_text_file(uploaded_file)
    user_input = file_text  # Use the text from the uploaded file

if st.button("Convert to Speech"):
    if user_input:
        with st.spinner('Adding diacritics...'):
            diacritized_text = add_diacritics(user_input)
            if not diacritized_text.startswith("Failed"):
                st.text_area("Diacritized Text", diacritized_text, height=150)
            else:
                st.error(diacritized_text)
        
        with st.spinner('Generating Speech...'):
            try:
                audio_data = synthesize_speech(diacritized_text)
                st.audio(audio_data, format='audio/mp3')
            except Exception as e:
                st.error(f"Failed to generate speech: {str(e)}")
    else:
        st.error("Please input text or upload a file.")
