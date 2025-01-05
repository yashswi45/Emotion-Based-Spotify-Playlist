from flask import Flask, render_template, request, redirect, url_for, session
import cv2
import speech_recognition as sr
from textblob import TextBlob
from fer import FER
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up the Spotify credentials from .env
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SECRET_KEY = os.getenv("SECRET_KEY")

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = SECRET_KEY  # Set the session secret key

# Initialize SpotifyOAuth with required scope
sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-library-read playlist-modify-private playlist-modify-public"
)

# Helper function to detect facial emotion
def detect_faces_and_emotions():
    # Initialize FER emotion detector without MTCNN
    detector = FER(mtcnn=False)

    # Access the webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not access the webcam.")
        return None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read a frame from the webcam.")
            break

        # Detect emotions using FER
        emotion, score = detector.top_emotion(frame)
        if emotion:
            print(f"Detected Emotion: {emotion} (Score: {score:.2f})")
            cap.release()
            cv2.destroyAllWindows()
            return emotion

        # Display the video feed
        cv2.imshow("Facial Emotion Detection", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

# Helper function to detect audio emotion
def detect_audio_emotion():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)

        try:
            text = recognizer.recognize_google(audio)
            print(f"Recognized Text: {text}")
            return detect_text_emotion(text)
        except Exception as e:
            print(f"Error: {e}")
            return None

# Helper function to detect text emotion
def detect_text_emotion(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity

    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

# Emotion detection route (POST)
@app.route("/detect_emotion", methods=["POST"])
def detect_emotion():
    emotion_type = request.form.get("emotion_type")
    detected_emotion = None

    if emotion_type == "facial":
        detected_emotion = detect_faces_and_emotions()  # Call the facial emotion detection
    elif emotion_type == "text":
        text = request.form["text"]
        detected_emotion = detect_text_emotion(text)  # Call the text emotion detection
    elif emotion_type == "audio":
        detected_emotion = detect_audio_emotion()  # Call the audio emotion detection
    else:
        detected_emotion = "neutral"  # Default to 'neutral' if no emotion type is provided

    # Redirect to the generate_playlist route with the detected emotion
    return redirect(url_for("generate_playlist", emotion=detected_emotion))

# def get_token_info():
#     token_info = session.get("token_info", None)
#     if not token_info:
#         return None
#     if sp_oauth.is_token_expired(token_info):
#         token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
#         session["token_info"] = token_info
#     return token_info

def get_token_info():
    token_info = session.get("token_info", None)
    if not token_info:
        return None
    if sp_oauth.is_token_expired(token_info):
        try:
            token_info = sp_oauth.refresh_access_token(token_info["refresh_token"])
            session["token_info"] = token_info
        except Exception as e:
            print(f"Error refreshing token: {e}")
            return None
    return token_info



# Playlist generation route

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


# @app.route("/callback")
# def callback():
#     code = request.args.get("code")
#     token_info = sp_oauth.get_access_token(code)
#     session["token_info"] = token_info
#     return redirect(url_for("index"))

@app.route("/callback")
def callback():
    try:
        code = request.args.get("code")
        token_info = sp_oauth.get_access_token(code)
        session["token_info"] = token_info
        return redirect(url_for("index"))
    except Exception as e:
        print(f"Error during Spotify callback: {e}")
        return redirect(url_for("index"))


# @app.route('/generate_playlist')
# def generate_playlist():
#     # Ensure user is logged in
#     token_info = session.get('token_info', None)
#     if not token_info:
#         return redirect(url_for('index'))
#
#     # Get emotion from the query parameter
#     emotion = request.args.get('emotion', 'happy')  # Default to 'happy' if not provided
#
#     # Create a playlist based on the detected emotion
#     playlist_name = f"Emotion-Based Playlist ({emotion})"
#     playlist_description = f"A playlist based on your current emotion: {emotion}"
#
#     # Initialize Spotify client
#     sp = spotipy.Spotify(auth=token_info['access_token'])
#
#     user_id = sp.current_user()['id']
#     playlist = sp.user_playlist_create(user_id, playlist_name, public=False, description=playlist_description)
#
#     # Fetch songs based on emotion
#     tracks = get_songs_for_emotion(emotion)
#
#     # Add the tracks to the created playlist
#     sp.playlist_add_items(playlist['id'], tracks)
#
#     return render_template('playlist.html', playlist=playlist)







# @app.route('/generate_playlist', methods=['GET'])
# def generate_playlist():
#     emotion = request.args.get('emotion')
#
#     # Example logic to generate a playlist based on emotion
#     try:
#         playlist_id = create_playlist(emotion)  # Call your Spotify playlist creation function
#         message = f"Playlist for '{emotion}' emotion has been successfully added to your Spotify account!"
#         return render_template("success.html", message=message)
#     except Exception as e:
#         print(f"Error creating playlist: {e}")
#         message = "An error occurred while creating your playlist. Please try again."
#         return render_template("error.html", message=message)

@app.route('/generate_playlist', methods=['GET'])
def generate_playlist():
    emotion = request.args.get('emotion')
    token_info = get_token_info()

    if not token_info:
        return redirect(url_for('login'))  # Redirect to login if not authenticated

    try:
        playlist_id = create_playlist(emotion)
        message = f"Playlist for '{emotion}' emotion has been successfully added to your Spotify account!"
        return render_template("success.html", message=message)
    except Exception as e:
        print(f"Error creating playlist: {e}")
        message = "An error occurred while creating your playlist. Please try again."
        return render_template("error.html", message=message)

@app.route("/logout")
def logout():
    # Clear the session token or perform logout operations
    session.pop('token_info', None)  # Remove token info from session
    return redirect(url_for('index'))  # Redirect to the home page


def create_playlist(emotion):
    token_info = get_token_info()
    if not token_info:
        raise Exception("User is not authenticated with Spotify.")

    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.me()['id']
    playlist_name = f"{emotion.capitalize()} Vibes"
    playlist_description = f"Songs to match your {emotion} mood."
    playlist = sp.user_playlist_create(user_id, playlist_name, description=playlist_description)
    track_uris = get_tracks_for_emotion(emotion)
    sp.playlist_add_items(playlist['id'], track_uris)
    return playlist['id']



def get_tracks_for_emotion(emotion):
    search_query = {
        "happy": "uplifting mood",
        "sad": "melancholic mood",
        "neutral": "relaxing mood",
    }

    query = search_query.get(emotion.lower(), "chill mood")  # Default query if emotion not matched
    token_info = session.get('token_info', None)
    sp = spotipy.Spotify(auth=token_info['access_token'])

    results = sp.search(q=query, type='track', limit=10)  # Fetch top 10 tracks
    track_uris = [track['uri'] for track in results['tracks']['items']]

    return track_uris


# Helper function to fetch songs based on emotion
def get_songs_for_emotion(emotion):
    emotion_to_keywords = {
        "happy": "upbeat",
        "sad": "melancholy",
        "angry": "intense",
        "calm": "relaxing",
        "Positive": "feel-good",
        "Negative": "sad",
        "Neutral": "calm"
    }
    keyword = emotion_to_keywords.get(emotion, "chill")  # Default to "chill" if emotion is unknown

    # Search Spotify for tracks matching the emotion
    token_info = session.get('token_info', None)
    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.search(q=keyword, type='track', limit=10)  # Fetch 10 tracks based on the keyword

    # Extract track IDs from the search results
    track_ids = [item['id'] for item in results['tracks']['items']]
    return track_ids


if __name__ == "__main__":
    app.run(debug=True)
