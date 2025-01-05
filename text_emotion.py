from textblob import TextBlob

def detect_text_emotion(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity

    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

if __name__ == "__main__":
    text = input("Enter a text: ")
    emotion = detect_text_emotion(text)
    print(f"Detected Emotion: {emotion}")
