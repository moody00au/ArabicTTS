import streamlit as st
from streamlit.components.v1 import html
import openai
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
    .audio-btn {
        width: 24px;
        height: 24px;
        background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path d="M0 384.662V127.338c0-31.202 34.425-51.202 61.856-35.419l186.297 107.338c20.367 11.756 20.367 41.083 0 52.838L61.856 419.081C34.425 435.864 0 415.864 0 384.662zM448 256c0 141.384-114.616 256-256 256s-256-114.616-256-256 256-256 256-256 256 114.616 256 256z"/></svg>') center/cover no-repeat;
        border: none;
        cursor: pointer;
    }
    audio::-webkit-media-controls-panel {
        display: none!important;
        -webkit-appearance: none;
    }
    audio::-webkit-media-controls-play-button {}
    audio::-webkit-media-controls-volume-slider {}
    audio::-webkit-media-controls-mute-button {}
    audio::-webkit-media-controls-timeline {}
    audio::-webkit-media-controls-current-time-display {}
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize the OpenAI client
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Define available voice models with user-friendly Arabic names and corresponding sample URLs
voice_options = {
    # Your voice options here...
}

# Retrieve Google Cloud credentials and initialize TTS client
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
        response = openai.Completion.create(
            model="gpt-4",
            prompt=f"أضف الحركات لهذا النص العربي: '{text}'.",
            temperature=1,
            max_tokens=3000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        diacritized_text = response.choices[0].text
        adjusted_text = apply_sukoon(diacritized_text)
        return adjusted_text
    except Exception as e:
        st.error(f"فشل في إضافة الحركات: {str(e)}")
        return None

# Initialize session state for selected voice and speech speed
if 'selected_voice' not in st.session_state:
    st.session_state.selected_voice = list(voice_options.keys())[0]  # Default to first option
if 'speech_speed' not in st.session_state:
    st.session_state.speech_speed = 1.0  # Default speed

# App title and introduction
st.title("تطبيق تحويل النص العربي إلى كلام مع الحركات")

# UI for input, diacritization, and modification
user_input = st.text_area("أدخل النص العربي هنا:", value="", height=300, key="user_text_input")
diacritized_text = None
if st.button("إضافة الحركات وتعديل النص"):
    diacritized_text = add_diacritics(user_input)
    if diacritized_text:
        modified_text = st.text_area("تعديل النص مع الحركات حسب الحاجة:", value=diacritized_text, height=300, key="modified_text_input")

    # Instead of using a selectbox for voice model selection, display them as clickable boxes with sample previews
    st.write("استمع إلى نماذج الأصوات قبل الاختيار:")
    # Define the number of columns you want, based on the number of voice options you have
    cols_per_row = 4  # Adjust based on your layout preference
    cols = st.columns(cols_per_row)
    
    # Iterate over your voice options and create a box in each column
    for index, (voice_name, voice_info) in enumerate(voice_options.items()):
        with cols[index % cols_per_row]:
            # Display voice name
            st.write(voice_name)
            # Audio sample button
            sample_url = voice_info[3]
            # Using HTML to embed the audio player directly, for preview
            audio_html = f"""
            <audio controls>
                <source src="{sample_url}" type="audio/mpeg">
                Your browser does not support the audio element.
            </audio>
            """
            html(audio_html)
            # Option to select this voice
            if st.button(f"اختر {voice_name}"):
                selected_voice = voice_name

    speech_speed = st.slider("سرعة الكلام", 0.5, 2.0, 1.0, key="speech_speed_slider")

    if st.button("تحويل إلى كلام"):
        if modified_text:
            language_code, voice_name, ssml_gender = voice_options[selected_voice][:3]  # Get the first three items
            audio_data = synthesize_speech(modified_text, language_code, voice_name, ssml_gender, speech_speed)
            now = datetime.datetime.now()
            formatted_now = now.strftime("%Y-%m-%d-%H-%M-%S") + ".mp3"
            audio_file = io.BytesIO(audio_data)
            audio_file.name = formatted_now
            st.audio(audio_data, format='audio/mp3')
            st.download_button(
                label="تحميل الكلام",
                data=audio_file,
                file_name=formatted_now,
                mime="audio/mp3"
            )
