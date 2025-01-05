import speech_recognition as sr
from textblob import TextBlob

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

def detect_text_emotion(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    return "Positive" if polarity > 0 else "Negative" if polarity < 0 else "Neutral"

if __name__ == "__main__":
    emotion = detect_audio_emotion()
    print(f"Detected Emotion: {emotion}")
