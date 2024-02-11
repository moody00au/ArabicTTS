import streamlit as st
import openai
import os
from openai import OpenAI
from google.cloud import texttospeech
from google.oauth2 import service_account
import json

client = OpenAI()

# Define available voice models
voice_options = {
    "Arabic Female Standard A": ("ar-XA", "ar-XA-Standard-A", texttospeech.SsmlVoiceGender.FEMALE),
    "Arabic Male Standard B": ("ar-XA", "ar-XA-Standard-B", texttospeech.SsmlVoiceGender.MALE),
    "Arabic Male Standard C": ("ar-XA", "ar-XA-Standard-C", texttospeech.SsmlVoiceGender.MALE),
    "Arabic Female Standard D": ("ar-XA", "ar-XA-Standard-D", texttospeech.SsmlVoiceGender.FEMALE),
    "Arabic Female WaveNet A": ("ar-XA", "ar-XA-Wavenet-A", texttospeech.SsmlVoiceGender.FEMALE),
    "Arabic Male WaveNet B": ("ar-XA", "ar-XA-Wavenet-B", texttospeech.SsmlVoiceGender.MALE),
    "Arabic Male WaveNet C": ("ar-XA", "ar-XA-Wavenet-C", texttospeech.SsmlVoiceGender.MALE),
    "Arabic Female WaveNet D": ("ar-XA", "ar-XA-Wavenet-D", texttospeech.SsmlVoiceGender.FEMALE),
}


# Retrieve your OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Parse the Google Cloud credentials from Streamlit secrets directly
google_credentials = service_account.Credentials.from_service_account_info(
    st.secrets["GOOGLE_CLOUD_CREDENTIALS"]
)
google_tts_client = texttospeech.TextToSpeechClient(credentials=google_credentials)

def add_diacritics(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {
                    "role": "user",
                    "content": f"Add diacritics to this Arabic text: '{text}'."
                }
            ],
            temperature=1,
            max_tokens=3000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        diacritized_text = response.choices[0].message.content
        
        return diacritized_text
    except Exception as e:
        return f"Failed to add diacritics: {str(e)}"

def synthesize_speech(text_with_harakat, language_code, voice_name, ssml_gender):
    synthesis_input = texttospeech.SynthesisInput(text=text_with_harakat)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
        ssml_gender=ssml_gender
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
st.title("Arabic Text Harakat and Text to Speech Application")

# Voice selection
selected_voice = st.selectbox("Choose a voice model:", list(voice_options.keys()))

# Text input/upload
user_input = st.text_area("Enter Arabic text here:", "هنا يمكنك كتابة النص العربي")
uploaded_file = st.file_uploader("Or upload a text file:", type=["txt"])

if uploaded_file is not None:
    user_input = read_text_file(uploaded_file)

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
                # Get the selected voice configuration
                language_code, voice_name, ssml_gender = voice_options[selected_voice]
                audio_data = synthesize_speech(diacritized_text, language_code, voice_name, ssml_gender)
                st.audio(audio_data, format='audio/mp3')
            except Exception as e:
                st.error(f"Failed to generate speech: {str(e)}")
    else:
        st.error("Please input text or upload a file.")
