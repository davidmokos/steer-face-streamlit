import time
from urllib.parse import quote

import streamlit as st
import requests
import firebase_admin
from firebase_admin import credentials, storage
import uuid

BASE_URL = "https://face.steercode.com/api/v1"

# Initialize Firebase
cred = credentials.Certificate("firebase_credentials.json")

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'steer-bb667.appspot.com'
    })


def video_to_text(original_video_url):
    url = f"{BASE_URL}/video_to_text?video_url={quote(original_video_url)}"
    print(url)
    result = requests.get(url)
    print(result.status_code, result.text)
    return result.json()['result']


def translate(text, language):
    url = f"{BASE_URL}/translate?text={quote(text)}?&lang={quote(language)}"
    print(url)
    result = requests.get(url)
    print(result.status_code, result.text)
    return result.json()["message"]


def text_to_speech(translation):
    url = f"{BASE_URL}/text_to_speach?text={quote(translation)}&session_id=123"
    print(url)
    result = requests.get(url)
    print(result.status_code, result.text)
    return result.json()['result_url']


def create_new_video(original_video_url, audio_url):

    url = f"https://votrumar--wav2lib-v1-execute.modal.run/?input_video_url={quote(original_video_url)}&input_audio_url={quote(audio_url)}"
    print(url)
    result = requests.get(url)
    print(result.status_code, result.text)
    video_url = result.text
    if video_url[0] == '"':
        video_url = video_url[1:-1]
    return video_url


def download_file(url):
    local_filename = "/tmp/generated_video.mp4"
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename


st.title("Steer Video")

if 'state' not in st.session_state:
    st.session_state['state'] = 0


if st.session_state['state'] == 0:

    uploaded_file = st.file_uploader('Choose a video...', type=["mp4", "mov"])

    if uploaded_file is not None:
        st.video(uploaded_file)
        with open('temp_video.mp4', 'wb') as f:
            f.write(uploaded_file.getbuffer())

        # Upload to firebase storage
        if st.button('Upload to Firebase'):
            with st.spinner(text='Uploading Video'):
                bucket = storage.bucket()
                blob = bucket.blob(f'videos/{uuid.uuid4()}')
                blob.upload_from_filename('temp_video.mp4')
                blob.make_public()
                st.session_state['video_url'] = blob.public_url
                st.success('Video uploaded to Firebase')
                st.write(f'Access URL: {st.session_state["video_url"]}')

            if 'video_url' in st.session_state:
                with st.spinner(text='Extracting text from video using whisper...'):
                    st.session_state['transcript'] = video_to_text(st.session_state['video_url'])
                    st.success('Transcript generated')
                    st.session_state['state'] = 1
                    time.sleep(1)
                    st.experimental_rerun()


elif st.session_state['state'] == 1:

    extracted_updated = st.text_area('Extracted text', value=st.session_state['transcript'], height=200)

    lang = st.text_input("Language", value="German")

    if st.button('Translate to {}'.format(lang)):
        with st.spinner(text='Translating...'):
            st.session_state['translated'] = translate(extracted_updated, lang)
            st.success('Successfully translated')
            st.session_state['state'] = 2
            time.sleep(1)
            st.experimental_rerun()


elif st.session_state['state'] == 2:

    translated_updated = st.text_area("Translated text", value=st.session_state['translated'], height=200)

    if st.button('Generate new video'):
        with st.spinner(text='Generating audio...'):
            st.session_state['new_audio_url'] = text_to_speech(translated_updated)
            st.success('Audio created')
            st.text(st.session_state['new_audio_url'])

        with st.spinner(text='Generating video with the new audio...'):
            st.session_state['new_video_url'] = create_new_video(st.session_state['video_url'], st.session_state['new_audio_url'])
            st.success('New video created')
            st.session_state['state'] = 3
            time.sleep(1)
            st.experimental_rerun()


elif st.session_state['state'] == 3:
    st.text(st.session_state['new_video_url'])
    filename = download_file(st.session_state['new_video_url'])
    st.video(filename)
    with open(filename, "rb") as file:
        st.download_button(label="Download", data=file, file_name="output_video.mp4")




