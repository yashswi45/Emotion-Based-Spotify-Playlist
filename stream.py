import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import cv2
import numpy as np
import os
from dotenv import load_dotenv
from textblob import TextBlob
import speech_recognition as sr
from fer import FER
import requests

# Load environment variables
load_dotenv()

# Spotify credentials
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# Streamlit UI
st.title("🎵 Emotion-Based Playlist Generator")

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-library-read playlist-modify-private playlist-modify-public"
)

# Function to get Spotify token
def get_spotify_token():
    token_info = sp_oauth.get_access_token(as_dict=False)
    return token_info

# Emotion detection functions
def detect_text_emotion(text):
    """Detect emotion from text using TextBlob."""
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0:
        return "happy"
    elif polarity < 0:
        return "sad"
    else:
        return "neutral"

def detect_audio_emotion():
    """Detect emotion from voice input."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.write("🎙 Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            return detect_text_emotion(text)
        except Exception as e:
            st.error(f"Error: {e}")
            return None

def detect_faces_and_emotions():
    """Detect emotion from webcam."""
    detector = FER(mtcnn=False)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("Error: Could not access the webcam.")
        return None

    st.write("📸 Capturing image... Look at the camera and wait.")

    ret, frame = cap.read()
    cap.release()
    cv2.destroyAllWindows()

    if not ret:
        st.error("Error: Could not capture image.")
        return None

    emotion, score = detector.top_emotion(frame)
    return emotion

# Fetch tracks from Spotify based on emotion
def get_tracks_for_emotion(emotion):
    query = {
        "happy": "uplifting",
        "sad": "melancholy",
        "neutral": "relaxing"
    }.get(emotion.lower(), "chill")

    token = get_spotify_token()
    if not token:
        return None

    sp = spotipy.Spotify(auth=token)
    results = sp.search(q=query, type="track", limit=10)
    return [track["uri"] for track in results["tracks"]["items"]]

# Generate Spotify playlist
def generate_playlist(emotion):
    token = get_spotify_token()
    if not token:
        st.error("⚠️ Please authenticate with Spotify first!")
        return None

    sp = spotipy.Spotify(auth=token)
    user = sp.me()
    playlist_name = f"{emotion.capitalize()} Vibes"
    playlist_description = f"Songs to match your {emotion} mood."
    playlist = sp.user_playlist_create(user["id"], playlist_name, description=playlist_description)

    tracks = get_tracks_for_emotion(emotion)
    if tracks:
        sp.playlist_add_items(playlist["id"], tracks)
        return playlist["external_urls"]["spotify"]
    else:
        st.warning("⚠️ No tracks found for the detected emotion.")
        return None

# Sidebar authentication
with st.sidebar:
    st.header("🔑 Spotify Authentication")
    if st.button("Authenticate with Spotify"):
        auth_url = sp_oauth.get_authorize_url()
        st.markdown(f"[Click here to authenticate]({auth_url})", unsafe_allow_html=True)

# Emotion detection UI
st.subheader("🎭 How do you want to detect emotion?")
option = st.radio("", ["Text", "Voice", "Facial Expression"])

emotion = None

if option == "Text":
    user_text = st.text_area("✍️ Enter a sentence describing your mood:")
    if st.button("Analyze Emotion"):
        if user_text:
            emotion = detect_text_emotion(user_text)
        else:
            st.warning("⚠️ Please enter some text.")

elif option == "Voice":
    if st.button("🎤 Start Voice Recording"):
        emotion = detect_audio_emotion()

elif option == "Facial Expression":
    if st.button("📷 Capture Image & Detect Emotion"):
        emotion = detect_faces_and_emotions()

# Display detected emotion
if emotion:
    st.success(f"✅ Detected Emotion: **{emotion.capitalize()}**")
    if st.button("🎶 Generate Playlist"):
        playlist_url = generate_playlist(emotion)
        if playlist_url:
            st.markdown(f"🎧 Your Playlist: [Click Here]({playlist_url})", unsafe_allow_html=True)
