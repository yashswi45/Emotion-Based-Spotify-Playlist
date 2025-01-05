from flask import Flask, render_template, request
from facial_emotion import detect_faces_and_emotions
from text_emotion import detect_text_emotion
from audio_emotion import detect_audio_emotion

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        emotion_type = request.form.get("emotion_type")

        if emotion_type == "facial":
            # Call the facial emotion detection
            emotion = detect_faces_and_emotions()
            return render_template("result.html", emotion=emotion)

        elif emotion_type == "text":
            # Call the text emotion detection
            text = request.form["text"]
            emotion = detect_text_emotion(text)
            return render_template("result.html", emotion=emotion)

        elif emotion_type == "audio":
            # Call the audio emotion detection
            emotion = detect_audio_emotion()
            return render_template("result.html", emotion=emotion)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
