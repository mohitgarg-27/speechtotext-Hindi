from flask import Flask, render_template, request
import os
import speech_recognition as sr
from pydub import AudioSegment

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def split_and_transcribe_large_audio(input_file, chunk_size=10, language='hi-IN'):
    audio = AudioSegment.from_file(input_file)

    num_chunks = len(audio) // (chunk_size * 1000) + 1

    transcribed_text = ""

    for i in range(num_chunks):
        start_time = i * chunk_size * 1000
        end_time = min((i + 1) * chunk_size * 1000, len(audio))

        chunk = audio[start_time:end_time]

        chunk_file = f"chunk_{i}.wav"
        chunk.export(chunk_file, format="wav")

        chunk_text = transcribe_audio(chunk_file, language)
        transcribed_text += chunk_text + ' '

        os.remove(chunk_file)

    return transcribed_text.strip()

def transcribe_audio(audio_file, language='hi-IN'):
    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_file) as source:
        recognizer.adjust_for_ambient_noise(source)
        audio_stream = recognizer.record(source, duration=None)

    try:
        text = recognizer.recognize_google(audio_stream, language=language)
        return text
    except sr.UnknownValueError:
        return "[Unrecognized]"
    except sr.RequestError as e:
        return f"Error connecting to Google Speech Recognition service: {e}"

def save_text_to_file(text, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(text)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'audio_file' not in request.files:
            return render_template('index.html', error="No file part")

        audio_file = request.files['audio_file']

        if audio_file.filename == '':
            return render_template('index.html', error="No selected file")

        if audio_file:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'audio.wav')

            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            audio_file.save(file_path)

            transcribed_text = split_and_transcribe_large_audio(file_path)
            os.remove(file_path)

            # Save the transcribed text to a file
            output_file = 'output.txt'
            save_text_to_file(transcribed_text, output_file)

            return render_template('index.html', transcribed_text=transcribed_text, output_file=output_file)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
