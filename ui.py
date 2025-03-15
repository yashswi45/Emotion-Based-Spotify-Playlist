import streamlit as st
from PIL import Image
import time


def main():
    st.set_page_config(page_title="Emotion-Based Playlist", layout="wide")

    # Background Image & Styling
    page_bg = """
    <style>
    body {
        background: url('https://source.unsplash.com/1600x900/?music,concert');
        background-size: cover;
    }
    .main-container {
        background: rgba(0, 0, 0, 0.6);
        padding: 3rem;
        border-radius: 20px;
        box-shadow: 0px 8px 20px rgba(255, 255, 255, 0.2);
    }
    .title-text {
        color: #FFD700;
        font-size: 2.5rem;
        text-align: center;
        font-weight: bold;
        text-shadow: 3px 3px 8px rgba(255, 99, 71, 0.6);
    }
    .btn-glow {
        background: #FF6347;
        border: none;
        color: white;
        padding: 12px 24px;
        font-size: 1.2rem;
        border-radius: 25px;
        box-shadow: 0px 0px 20px rgba(255, 99, 71, 0.5);
        transition: all 0.3s ease;
    }
    .btn-glow:hover {
        background: #FF4500;
        transform: scale(1.1);
        box-shadow: 0px 0px 30px rgba(255, 69, 0, 0.7);
    }
    </style>
    """
    st.markdown(page_bg, unsafe_allow_html=True)

    # Main UI Layout
    st.markdown("""<div class='main-container'>""", unsafe_allow_html=True)
    st.markdown("<p class='title-text'>Welcome to Emotion-Based Playlist</p>", unsafe_allow_html=True)

    # Sidebar for Navigation
    menu = ["Login", "Sign Up", "Explore"]
    choice = st.sidebar.selectbox("Navigate", menu)

    if choice == "Login":
        login_page()
    elif choice == "Sign Up":
        signup_page()
    elif choice == "Explore":
        explore_page()

    st.markdown("""</div>""", unsafe_allow_html=True)


def login_page():
    st.subheader("Login to Your Account")
    email = st.text_input("Email", "", placeholder="Enter your email")
    password = st.text_input("Password", "", type="password", placeholder="Enter your password")
    if st.button("Login", key="login_btn", help="Click to login", use_container_width=True):
        with st.spinner("Authenticating..."):
            time.sleep(2)
        st.success("Logged in successfully!")
        st.balloons()


def signup_page():
    st.subheader("Create a New Account")
    username = st.text_input("Username", "", placeholder="Choose a username")
    email = st.text_input("Email", "", placeholder="Enter your email")
    password = st.text_input("Password", "", type="password", placeholder="Create a password")
    if st.button("Sign Up", key="signup_btn", use_container_width=True):
        with st.spinner("Creating account..."):
            time.sleep(2)
        st.success("Account created successfully!")


def explore_page():
    st.subheader("Discover Emotion-Based Playlists")
    emotion = st.selectbox("Choose your mood", ["Happy", "Sad", "Energetic", "Calm", "Romantic", "Angry"])
    if st.button("Find Playlist", key="playlist_btn", use_container_width=True):
        st.info(f"Fetching songs for {emotion} mood...")
        time.sleep(2)
        st.success("Playlist generated successfully!")


if __name__ == "__main__":
    main()
