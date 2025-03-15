from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone
import cv2
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
from textblob import TextBlob
import speech_recognition as sr
from fer import FER


# Load environment variables
load_dotenv()

# App Config
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Initialize extensions
bcrypt = Bcrypt(app)
db = SQLAlchemy(app)

# Spotify credentials
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-library-read playlist-modify-private playlist-modify-public"
)




# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    access_token = db.Column(db.String(255))
    refresh_token = db.Column(db.String(255))
    token_expires = db.Column(db.DateTime)

    # Establish relationship with EmotionHistory model
    emotion_history = db.relationship('EmotionHistory', backref='user', lazy=True)


# EmotionHistory model to track emotions
class EmotionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    emotion = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


# Database initialization
with app.app_context():
    db.create_all()


# Helper functions
def get_token_info():
    """Retrieve and refresh Spotify tokens for the logged-in user."""
    user = User.query.filter_by(id=session.get('user_id')).first()
    if not user:
        return None

    if user.token_expires and user.token_expires.tzinfo is None:
        user.token_expires = user.token_expires.replace(tzinfo=timezone.utc)

    if user.token_expires and user.token_expires < datetime.now(timezone.utc):
        try:
            token_info = sp_oauth.refresh_access_token(user.refresh_token)
            user.access_token = token_info['access_token']
            user.refresh_token = token_info['refresh_token']
            user.token_expires = datetime.utcnow() + timedelta(seconds=token_info['expires_in'])
            db.session.commit()
        except Exception as e:
            print(f"Error refreshing token: {e}")
            flash("Session expired. Please log in again.")
            return None

    return user.access_token


def detect_faces_and_emotions():
    """Detect emotion from facial expressions using webcam."""
    detector = FER(mtcnn=False)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not access the webcam.")
        return None
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read a frame from the webcam.")
            break
        emotion, score = detector.top_emotion(frame)
        if emotion:
            cap.release()
            cv2.destroyAllWindows()
            return emotion
        cv2.imshow("Facial Emotion Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
    return None


def detect_audio_emotion():
    """Detect emotion from voice input."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            return detect_text_emotion(text)
        except Exception as e:
            print(f"Error: {e}")
            return None


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


def get_tracks_for_emotion(emotion):
    """Fetch tracks from Spotify based on emotion."""
    query = {
        "happy": "uplifting",
        "sad": "melancholy",
        "neutral": "relaxing"
    }.get(emotion.lower(), "chill")

    token = get_token_info()
    if not token:
        return None

    sp = spotipy.Spotify(auth=token)
    results = sp.search(q=query, type="track", limit=10)
    return [track["uri"] for track in results["tracks"]["items"]]


# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(email=email, username=username, password=hashed_pw)

        db.session.add(new_user)
        db.session.commit()

        flash("Account created successfully!")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            flash("Login successful!")
            return redirect(url_for("index"))
        else:
            flash("Invalid credentials. Please try again.")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out successfully!")
    return redirect(url_for("index"))


@app.route("/spotify_auth")
def spotify_auth():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route("/callback")
def callback():
    code = request.args.get("code")
    token_info = sp_oauth.get_access_token(code)
    user = User.query.filter_by(id=session.get("user_id")).first()
    if user:
        user.access_token = token_info["access_token"]
        user.refresh_token = token_info["refresh_token"]
        user.token_expires = datetime.utcnow() + timedelta(seconds=token_info["expires_in"])
        db.session.commit()
    flash("Spotify connected successfully!")
    return redirect(url_for("index"))

#
# @app.route("/detect_emotion", methods=["POST"])
# def detect_emotion():
#     emotion_type = request.form.get("emotion_type")
#     if emotion_type == "text":
#         text = request.form.get("text")
#         emotion = detect_text_emotion(text)
#     elif emotion_type == "audio":
#         emotion = detect_audio_emotion()
#     else:
#         emotion = detect_faces_and_emotions()
#
#     if not emotion:
#         flash("No emotion detected. Please try again.")
#         return redirect(url_for("index"))
#
#     # Save detected emotion to history
#     if session.get("user_id"):
#         user = User.query.get(session["user_id"])
#         emotion_history = EmotionHistory(user_id=user.id, emotion=emotion)
#         db.session.add(emotion_history)
#         db.session.commit()
#
#     flash(f"Detected emotion: {emotion}")
#     return redirect(url_for("generate_playlist", emotion=emotion))
#
#
# # @app.route("/generate_playlist", methods=["GET"])
# # def generate_playlist():
# #     emotion = request.args.get("emotion")
# #     token = get_token_info()
# #     if not token:
# #         return redirect(url_for("spotify_auth"))
# #
# #     try:
# #         sp = spotipy.Spotify(auth=token)
# #         user = sp.me()
# #         playlist_name = f"{emotion.capitalize()} Vibes"
# #         playlist_description = f"Songs to match your {emotion} mood."
# #         playlist = sp.user_playlist_create(user["id"], playlist_name, description=playlist_description)
# #
# #         tracks = get_tracks_for_emotion(emotion)
# #         if tracks:
# #             sp.playlist_add_items(playlist["id"], tracks)
# #         else:
# #             flash("No tracks found for the emotion.")
# #             return redirect(url_for("index"))
# #
# #         playlist_url = playlist["external_urls"]["spotify"]
# #         flash("Playlist created successfully!")
# #         return render_template("playlist.html", playlist_url=playlist_url)
# #
# #     except Exception as e:
# #         print(f"Error creating playlist: {e}")
# #         flash(f"An error occurred: {e}. Please try again.")
# #         return redirect(url_for("index"))
#
#
# @app.route("/generate_playlist", methods=["GET"])
# def generate_playlist():
#     emotion = request.args.get("emotion")
#     token = get_token_info()
#     if not token:
#         return redirect(url_for("spotify_auth"))
#
#     try:
#         sp = spotipy.Spotify(auth=token)
#         user = sp.me()
#         playlist_name = f"{emotion.capitalize()} Vibes"
#         playlist_description = f"Songs to match your {emotion} mood."
#         playlist = sp.user_playlist_create(user["id"], playlist_name, description=playlist_description)
#
#         tracks = get_tracks_for_emotion(emotion)
#         if tracks:
#             sp.playlist_add_items(playlist["id"], tracks)
#         else:
#             flash("No tracks found for the emotion.")
#             return redirect(url_for("index"))
#
#         playlist_url = playlist["external_urls"]["spotify"]
#
#         # Flash success message
#         flash(
#             f"Playlist '{playlist_name}' created successfully! Click <a href='{playlist_url}' target='_blank'>here</a> to listen.",
#             "success")
#
#         return render_template("playlist.html", playlist_url=playlist_url)
#
#     except Exception as e:
#         print(f"Error creating playlist: {e}")
#         flash(f"An error occurred: {e}. Please try again.", "danger")
#         return redirect(url_for("index"))


@app.route("/detect_emotion", methods=["POST"])
def detect_emotion():
    emotion_type = request.form.get("emotion_type")
    if emotion_type == "text":
        text = request.form.get("text")
        emotion = detect_text_emotion(text)
    elif emotion_type == "audio":
        emotion = detect_audio_emotion()
    else:
        emotion = detect_faces_and_emotions()

    if not emotion:
        flash("No emotion detected. Please try again.")
        return redirect(url_for("index"))

    # Save detected emotion to session
    session["detected_emotion"] = emotion

    # Save detected emotion to history
    if session.get("user_id"):
        user = User.query.get(session["user_id"])
        emotion_history = EmotionHistory(user_id=user.id, emotion=emotion)
        db.session.add(emotion_history)
        db.session.commit()

    flash(f"Detected emotion: {emotion}")
    return redirect(url_for("index"))


# @app.route("/generate_playlist", methods=["POST"])
# def generate_playlist():
#     emotion = session.get("detected_emotion")
#     if not emotion:
#         flash("No emotion detected. Please detect emotion first.")
#         return redirect(url_for("index"))
#
#     token = get_token_info()
#     if not token:
#         return redirect(url_for("spotify_auth"))
#
#     try:
#         sp = spotipy.Spotify(auth=token)
#         user = sp.me()
#         playlist_name = f"{emotion.capitalize()} Vibes"
#         playlist_description = f"Songs to match your {emotion} mood."
#         playlist = sp.user_playlist_create(user["id"], playlist_name, description=playlist_description)
#
#         tracks = get_tracks_for_emotion(emotion)
#         if tracks:
#             sp.playlist_add_items(playlist["id"], tracks)
#         else:
#             flash("No tracks found for the emotion.")
#             return redirect(url_for("index"))
#
#         playlist_url = playlist["external_urls"]["spotify"]
#
#         # Flash success message
#         flash(
#             f"Playlist '{playlist_name}' created successfully! Click <a href='{playlist_url}' target='_blank'>here</a> to listen.",
#             "success")
#
#         return render_template("playlist.html", playlist_url=playlist_url, playlist_name=playlist_name)
#
#     except Exception as e:
#         print(f"Error creating playlist: {e}")
#         flash(f"An error occurred: {e}. Please try again.", "danger")
#         return redirect(url_for("index"))












# @app.route("/generate_playlist", methods=["POST"])
# def generate_playlist():
#     emotion = session.get("detected_emotion")
#     if not emotion:
#         flash("No emotion detected. Please detect emotion first.")
#         return redirect(url_for("index"))
#
#     token = get_token_info()
#     if not token:
#         return redirect(url_for("spotify_auth"))
#
#     try:
#         sp = spotipy.Spotify(auth=token)
#         user = sp.me()
#         playlist_name = f"{emotion.capitalize()} Vibes"
#         playlist_description = f"Songs to match your {emotion} mood."
#         playlist = sp.user_playlist_create(user["id"], playlist_name, description=playlist_description)
#
#         tracks = get_tracks_for_emotion(emotion)
#         if tracks:
#             sp.playlist_add_items(playlist["id"], tracks)
#         else:
#             flash("No tracks found for the emotion.")
#             return redirect(url_for("index"))
#
#         playlist_url = playlist["external_urls"]["spotify"]
#
#         # Store playlist details in session
#         session["playlist_name"] = playlist_name
#         session["playlist_url"] = playlist_url
#
#         # Flash success message
#         flash(f"Playlist '{playlist_name}' created successfully! Click <a href='{playlist_url}' target='_blank'>here</a> to listen.", "success")
#
#         return redirect(url_for("index"))
#
#     except Exception as e:
#         print(f"Error creating playlist: {e}")
#         flash(f"An error occurred: {e}. Please try again.", "danger")
#         return redirect(url_for("index"))









@app.route("/generate_playlist", methods=["POST"])
def generate_playlist():
    emotion = session.get("detected_emotion")
    if not emotion:
        flash("No emotion detected. Please detect emotion first.")
        return redirect(url_for("index"))

    token = get_token_info()
    if not token:
        return redirect(url_for("spotify_auth"))

    try:
        sp = spotipy.Spotify(auth=token)
        user = sp.me()
        playlist_name = f"{emotion.capitalize()} Vibes"
        playlist_description = f"Songs to match your {emotion} mood."
        playlist = sp.user_playlist_create(user["id"], playlist_name, description=playlist_description)

        tracks = get_tracks_for_emotion(emotion)
        if tracks:
            sp.playlist_add_items(playlist["id"], tracks)
        else:
            flash("No tracks found for the emotion.")
            return redirect(url_for("index"))

        playlist_url = playlist["external_urls"]["spotify"]

        # Store playlist details in session
        session["playlist_name"] = playlist_name
        session["playlist_url"] = playlist_url

        # Flash success message
        flash(f"Playlist '{playlist_name}' created successfully! Click <a href='{playlist_url}' target='_blank'>here</a> to listen.", "success")

        return redirect(url_for("index"))

    except Exception as e:
        print(f"Error creating playlist: {e}")
        flash(f"An error occurred: {e}. Please try again.", "danger")
        return redirect(url_for("index"))






@app.route("/emotion_history")
def emotion_history():
    user_id = session.get("user_id")
    history = EmotionHistory.query.filter_by(user_id=user_id).all()
    return render_template("history.html", history=history)


@app.route("/api/emotion", methods=["POST"])
def api_detect_emotion():
    data = request.get_json()
    emotion = detect_text_emotion(data.get("text"))
    return {"emotion": emotion}, 200


if __name__ == "__main__":
    app.run(debug=True)




# latest