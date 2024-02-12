import streamlit as st
import openai
from openai import OpenAI
from google.cloud import texttospeech
from google.oauth2 import service_account
import re
import datetime
import io

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
    "هالة": ("ar-XA", "ar-XA-Standard-A", texttospeech.SsmlVoiceGender.FEMALE),
    "سامي": ("ar-XA", "ar-XA-Standard-B", texttospeech.SsmlVoiceGender.MALE),
    "عمر": ("ar-XA", "ar-XA-Standard-C", texttospeech.SsmlVoiceGender.MALE),
    "سمر": ("ar-XA", "ar-XA-Standard-D", texttospeech.SsmlVoiceGender.FEMALE),
    "شيرين": ("ar-XA", "ar-XA-Wavenet-A", texttospeech.SsmlVoiceGender.FEMALE),
    "هادي": ("ar-XA", "ar-XA-Wavenet-B", texttospeech.SsmlVoiceGender.MALE),
    "سلطان": ("ar-XA", "ar-XA-Wavenet-C", texttospeech.SsmlVoiceGender.MALE),
    "سارة": ("ar-XA", "ar-XA-Wavenet-D", texttospeech.SsmlVoiceGender.FEMALE),
}

# Retrieve API key and Google Cloud credentials
openai.api_key = st.secrets["OPENAI_API_KEY"]
google_credentials = service_account.Credentials.from_service_account_info(st.secrets["GOOGLE_CLOUD_CREDENTIALS"])
google_tts_client = texttospeech.TextToSpeechClient(credentials=google_credentials)

def apply_sukoon(text):
    diacritics = "[\u064B-\u0651\u0653-\u0654\u0670]"
    pattern = re.compile(f"({diacritics})(?=[.,،])")
    def replace_with_sukoon(match):
        return "\u0652"
    adjusted_text = re.sub(pattern, replace_with_sukoon, text)
    return adjusted_text

def add_diacritics(text):
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": f"أضف الحركات لهذا النص العربي: '{text}'."}],
            temperature=1,
            max_tokens=3000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        diacritized_text = response.choices[0].message.content
        adjusted_text = apply_sukoon(diacritized_text)
        return adjusted_text
    except Exception as e:
        st.error(f"فشل في إضافة الحركات: {str(e)}")
        return None

def synthesize_speech(adjusted_text, language_code, voice_name, ssml_gender, speed):
    synthesis_input = texttospeech.SynthesisInput(text=adjusted_text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
        ssml_gender=ssml_gender
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speed
    )
    response = google_tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content

# App title
st.title("تطبيق تحويل النص العربي إلى كلام مع الحركات")

# Step 1: Input text and add diacritics
user_input = st.text_area("أدخل النص العربي هنا:", value="", height=300, key="user_text_input")
if st.button("إضافة الحركات"):
    diacritized_text = add_diacritics(user_input)
    if diacritized_text:
        # Save diacritized text in session state for further actions
        st.session_state['diacritized_text'] = diacritized_text
        st.text_area("مراجعة النص مع الحركات:", value=diacritized_text, height=300, key="diacritized_text_input", disabled=True)

# Step 2: Modify diacritized text if needed
if 'diacritized_text' in st.session_state:
    modified_text = st.text_area("تعديل النص مع الحركات حسب الحاجة:", value=st.session_state['diacritized_text'], height=300, key="modified_text_input")

    selected_voice = st.selectbox("اختر نموذج الصوت:", options=list(voice_options.keys()), key="voice_model_select")
    speech_speed = st.slider("سرعة الكلام", 0.5, 2.0, 1.0, key="speech_speed_slider")

    if st.button("تحويل إلى كلام"):
        if modified_text:
            language_code, voice_name, ssml_gender = voice_options[selected_voice]
            audio_data = synthesize_speech(modified_text, language_code, voice_name, ssml_gender, speech_speed)
            now = datetime.datetime.now()
            formatted_now = now.strftime("Audio-%Y-%m-%d-%H-%M-%S.mp3")
            audio_file = io.BytesIO(audio_data)
            audio_file.name = formatted_now
            st.audio(audio_data, format='audio/mp3')
            st.download_button(
                label="تحميل الكلام",
                data=audio_file,
                file_name=formatted_now,
                mime="audio/mp3"
            )
