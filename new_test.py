from dotenv import load_dotenv
import os

load_dotenv()

# Check if variables are loaded correctly
print(os.getenv("SPOTIPY_REDIRECT_URI"))  # Should print 'http://127.0.0.1:8501/callback'
