import streamlit as st
from streamlit.components.v1 import html
import openai
from openai import OpenAI
from google.cloud import texttospeech
from google.oauth2 import service_account
import re
import datetime
import io

# Custom CSS to enhance RTL layout and appearance
st.markdown(
    """
    <style>
    body, textarea, select, input, button {
        direction: RTL; /* Apply Right to Left layout */
        text-align: right; /* Align text to the right */
    }
    textarea {
        height: 300px !important; /* Set a fixed height for text areas */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize the OpenAI client
client = OpenAI()

# Define available voice models with user-friendly Arabic names and corresponding sample URLs
voice_options = {
    "هالة": ("ar-XA", "ar-XA-Standard-A", texttospeech.SsmlVoiceGender.FEMALE, "https://raw.githubusercontent.com/moody00au/ArabicTTS/main/Hala_sample.mp3"),
    "سامي": ("ar-XA", "ar-XA-Standard-B", texttospeech.SsmlVoiceGender.MALE, "https://raw.githubusercontent.com/moody00au/ArabicTTS/main/Sami_sample.mp3"),
    "عمر": ("ar-XA", "ar-XA-Standard-C", texttospeech.SsmlVoiceGender.MALE, "https://raw.githubusercontent.com/moody00au/ArabicTTS/main/Omar_sample.mp3"),
    "سمر": ("ar-XA", "ar-XA-Standard-D", texttospeech.SsmlVoiceGender.FEMALE, "https://raw.githubusercontent.com/moody00au/ArabicTTS/main/Samar_sample.mp3"),
    "شيرين": ("ar-XA", "ar-XA-Wavenet-A", texttospeech.SsmlVoiceGender.FEMALE, "https://raw.githubusercontent.com/moody00au/ArabicTTS/main/Shireen_sample.mp3"),
    "هادي": ("ar-XA", "ar-XA-Wavenet-B", texttospeech.SsmlVoiceGender.MALE, "https://raw.githubusercontent.com/moody00au/ArabicTTS/main/Hadi_sample.mp3"),
    "سلطان": ("ar-XA", "ar-XA-Wavenet-C", texttospeech.SsmlVoiceGender.MALE, "https://raw.githubusercontent.com/moody00au/ArabicTTS/main/Sultan_sample.mp3"),
    "سارة": ("ar-XA", "ar-XA-Wavenet-D", texttospeech.SsmlVoiceGender.FEMALE, "https://raw.githubusercontent.com/moody00au/ArabicTTS/main/Sarah_sample.mp3"),
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

# Function to apply Sukoon
def apply_sukoon(text):
    diacritics = "[\u064B-\u0651\u0653-\u0654\u0670]"
    pattern = re.compile(f"({diacritics})(?=[.,،])")
    def replace_with_sukoon(match):
        return "\u0652"
    return re.sub(pattern, replace_with_sukoon, text)

# Function to add diacritics
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

# Synthesize speech
def synthesize_speech(adjusted_text, language_code, voice_name, ssml_gender, speed):
    synthesis_input = texttospeech.SynthesisInput(text=adjusted_text)
    voice = texttospeech.VoiceSelectionParams(language_code=language_code, name=voice_name, ssml_gender=ssml_gender)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=speed)
    return google_tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config).audio_content

# App title and introduction
st.title("تطبيق تحويل النص العربي إلى كلام مع الحركات")

# Detailed explanation in Arabic
st.markdown("""
#### كيف يعمل التطبيق:
1. **أدخل النص العربي**: اكتب النص الذي تريد تحويله إلى كلام في المربع المخصص.
2. **إضافة الحركات**: يستخدم التطبيق تقنية من OpenAI لإضافة الحركات إلى النص العربي لتحسين دقة النطق.
3. **تعديل النص**: بعد إضافة الحركات، يمكنك تعديل النص كما تريد.
4. **اختر نموذج الصوت**: استمع إلى عينات الأصوات واختر الصوت الذي تفضله لتحويل النص إلى كلام.
5. **تحويل النص إلى كلام**: يقوم التطبيق بتحويل النص المعدل إلى كلام باستخدام Google Cloud Text-to-Speech.

#### التقنيات المستخدمة:
- **Streamlit**: لإنشاء واجهة المستخدم الخاصة بالتطبيق.
- **OpenAI GPT-4**: لإضافة الحركات إلى النص العربي.
- **Google Cloud Text-to-Speech**: لتحويل النص إلى كلام بطريقة طبيعية.

يتم استخدام الحركات لضمان دقة النطق ووضوح المعنى، مما يساعد في تحسين جودة النص المحول إلى كلام.
""", unsafe_allow_html=True)

# UI for input, diacritization, and modification
user_input = st.text_area("أدخل النص العربي هنا:", height=300)
if st.button("إضافة الحركات وتعديل النص"):
    diacritized_text = add_diacritics(user_input)
    if diacritized_text:
        modified_text = st.text_area("تعديل النص مع الحركات حسب الحاجة:", value=diacritized_text, height=300)

# Voice model selection simplified to a selectbox
selected_voice = st.selectbox("اختر نموذج الصوت:", options=list(voice_options.keys()))

# Slider for speech speed
speech_speed = st.slider("سرعة الكلام", 0.5, 2.0, 1.0)

# After diacritization
if diacritized_text:
    st.session_state['diacritized_text'] = diacritized_text  # Store in session state if needed

# Button to trigger speech synthesis
if st.button("تحويل إلى كلام"):
    # Check here if diacritized_text or its equivalent session state variable is set
    if 'diacritized_text' in st.session_state and st.session_state['diacritized_text']:
        # Proceed with speech synthesis
        voice_info = voice_options[selected_voice]
        audio_data = synthesize_speech(st.session_state['diacritized_text'], *voice_info[:3], speech_speed)
        # Remaining code for handling audio data...
