from flask import Flask, request, redirect, session, url_for, render_template
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

# Home route that checks for authentication
@app.route('/')
def index():
    if 'token_info' in session:
        return redirect(url_for('profile'))  # If logged in, go to the profile page
    return '<a href="/login">Log in with Spotify</a>'  # Show login link if not logged in

# Login route, redirects to Spotify's authorization page
@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)  # Redirect the user to Spotify's login page

# Callback route, where Spotify will redirect after login
@app.route('/callback')
def callback():
    # Get the authorization code from the URL
    code = request.args.get('code')

    if code:
        try:
            # Exchange the code for an access token
            token_info = sp_oauth.get_access_token(code)  # Get access token from the code
            session['token_info'] = token_info  # Store the token in the session

            return redirect(url_for('profile'))  # Redirect to the profile page to show user info
        except Exception as e:
            return f"Error during authentication: {str(e)}"  # Error if the exchange fails
    else:
        return "Error: No code in callback"


# Profile route to show the logged-in user's profile
@app.route('/profile')
def profile():
    # Check if the user is authenticated
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('login'))  # If no token, redirect to login

    # Use the access token to authenticate the Spotify client
    sp = spotipy.Spotify(auth=token_info['access_token'])

    try:
        # Fetch the user's profile information
        user = sp.current_user()

        # Return the display name of the logged-in user
        return render_template('profile.html', user=user)
    except Exception as e:
        print("Error fetching user profile:", e)
        return "Error fetching profile"

@app.route('/generate_playlist')
def generate_playlist():
    # Ensure user is logged in
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect(url_for('login'))

    # Initialize Spotify client
    sp = spotipy.Spotify(auth=token_info['access_token'])

    # Get emotion from the query parameter
    emotion = request.args.get('emotion', 'happy')  # Default to 'happy' if not provided

    # Create a playlist based on the detected emotion
    playlist_name = f"Emotion-Based Playlist ({emotion})"
    playlist_description = f"A playlist based on your current emotion: {emotion}"

    user_id = sp.current_user()['id']
    playlist = sp.user_playlist_create(user_id, playlist_name, public=False, description=playlist_description)

    # Fetch songs based on emotion
    tracks = get_songs_for_emotion(emotion)

    # Add the tracks to the created playlist
    sp.playlist_add_items(playlist['id'], tracks)

    return render_template('playlist.html', playlist=playlist)


def get_songs_for_emotion(emotion):
    # Map emotions to keywords for Spotify search
    emotion_to_keywords = {
        "happy": "upbeat",
        "sad": "melancholy",
        "angry": "intense",
        "calm": "relaxing"
    }
    keyword = emotion_to_keywords.get(emotion, "chill")  # Default to "chill" if emotion is unknown

    # Search Spotify for tracks matching the emotion
    token_info = session.get('token_info', None)
    sp = spotipy.Spotify(auth=token_info['access_token'])
    results = sp.search(q=keyword, type='track', limit=10)  # Fetch 10 tracks based on the keyword

    # Extract track IDs from the search results
    track_ids = [item['id'] for item in results['tracks']['items']]
    return track_ids






if __name__ == '__main__':
    app.run(debug=True)  # Run the Flask app
