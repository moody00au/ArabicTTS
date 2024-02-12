import streamlit as st
import openai
from openai import OpenAI
from google.cloud import texttospeech
from google.oauth2 import service_account
import re


# Custom CSS to set the text area to RTL and potentially adjust its style
st.markdown(
    """
    <style>
    /* Targeting all textareas */
    textarea {
        direction: RTL; /* Right to Left */
        text-align: right; /* Align text to the right */
        height: 300px !important; /* Example of setting a larger fixed height */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize the OpenAI client
client = OpenAI()

# Define available voice models with user-friendly Arabic names
voice_options = {
    "Hala": ("ar-XA", "ar-XA-Standard-A", texttospeech.SsmlVoiceGender.FEMALE),
    "Sami": ("ar-XA", "ar-XA-Standard-B", texttospeech.SsmlVoiceGender.MALE),
    "Omar": ("ar-XA", "ar-XA-Standard-C", texttospeech.SsmlVoiceGender.MALE),
    "Samar": ("ar-XA", "ar-XA-Standard-D", texttospeech.SsmlVoiceGender.FEMALE),
    "Shireen": ("ar-XA", "ar-XA-Wavenet-A", texttospeech.SsmlVoiceGender.FEMALE),
    "Hadi": ("ar-XA", "ar-XA-Wavenet-B", texttospeech.SsmlVoiceGender.MALE),
    "Sultan": ("ar-XA", "ar-XA-Wavenet-C", texttospeech.SsmlVoiceGender.MALE),
    "Sarah": ("ar-XA", "ar-XA-Wavenet-D", texttospeech.SsmlVoiceGender.FEMALE),
}

# Retrieve API key and Google Cloud credentials
openai.api_key = st.secrets["OPENAI_API_KEY"]
google_credentials = service_account.Credentials.from_service_account_info(st.secrets["GOOGLE_CLOUD_CREDENTIALS"])
google_tts_client = texttospeech.TextToSpeechClient(credentials=google_credentials)

def apply_sukoon(text):
    # Arabic diacritics range, excluding sukoon
    diacritics = "[\u064B-\u0651\u0653-\u0654\u0670]"
    # Include Arabic comma (،) in the pattern
    pattern = re.compile(f"({diacritics})(?=[.,،])")

    def replace_with_sukoon(match):
        return "\u0652"  # sukoon

    adjusted_text = re.sub(pattern, replace_with_sukoon, text)
    return adjusted_text

def add_diacritics(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": f"Add diacritics to this Arabic text: '{text}'."}],
            temperature=1,
            max_tokens=3000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        diacritized_text = response.choices[0].message.content
        # Apply sukoon to the diacritized text
        adjusted_text = apply_sukoon(diacritized_text)
        return adjusted_text
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
    
# Streamlit UI
st.title("Arabic Text Harakat and Text to Speech Application")
selected_voice = st.selectbox("Choose a voice model:", list(voice_options.keys()))

user_input = st.text_area("Enter Arabic text here:", "هنا يمكنك كتابة النص العربي", max_chars=5000, height=300)

if st.button("Convert to Speech"):
    if user_input:
        with st.spinner('Adding diacritics...'):
            diacritized_text = add_diacritics(user_input)
            if not diacritized_text.startswith("Failed"):
                # Display the adjusted text with sukoon applied
                st.text_area("Diacritized Text", diacritized_text, height=300, max_chars=5000)
            else:
                st.error(diacritized_text)
        
        with st.spinner('Generating Speech...'):
            try:
                language_code, voice_name, ssml_gender = voice_options[selected_voice]
                audio_data = synthesize_speech(diacritized_text, language_code, voice_name, ssml_gender)
                st.audio(audio_data, format='audio/mp3')
            except Exception as e:
                st.error(f"Failed to generate speech: {str(e)}")
    else:
        st.error("Please input text.")
