import os
import uuid
import requests
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from dotenv import load_dotenv
# Load Azure key from .env file
load_dotenv()
print("DEBUG | AZURE_SPEECH_KEY:", os.getenv("AZURE_SPEECH_KEY"))
print("DEBUG | AZURE_REGION:", os.getenv("AZURE_REGION"))
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/audio'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ========== gTTS Settings ==========

def create_audio(text, voice_name, style, pitch, rate, volume):
    import requests
    AZURE_KEY = os.getenv("AZURE_SPEECH_KEY")
    AZURE_REGION = os.getenv("AZURE_REGION")

    lang = "-".join(voice_name.split('-')[:2])

    # Voices that support expressive styles
    supported_styles = {
        "fr-FR-DeniseNeural",
        "fr-FR-HenriNeural",
        "fr-FR-VivienneMultilingualNeural",
        "fr-FR-RemyMultilingualNeural",
        "fr-FR-LucienMultilingualNeural",
        "fr-FR-AlainNeural",
        "fr-FR-BrigitteNeural",
        "fr-FR-CelesteNeural", 
        "fr-FR-ClaudeNeural",
        "fr-FR-CoralieNeural",
        "fr-FR-EloiseNeural",
        "fr-FR-JacquelineNeural", 
        "fr-FR-JeromeNeural"
        "fr-FR-JosephineNeural", 
        "fr-FR-MauriceNeural",
        "fr-FR-YvesNeural",
        "fr-FR-YvetteNeural"
    }

    if voice_name not in supported_styles:
        style = ""  # reset unsupported style

    prosody_attrs = []
    if rate:
        prosody_attrs.append(f'rate="{rate}"')
    if pitch:
        prosody_attrs.append(f'pitch="{pitch}"')
    if volume:
        prosody_attrs.append(f'volume="{volume}"')
    prosody_open = f"<prosody {' '.join(prosody_attrs)}>" if prosody_attrs else ""
    prosody_close = "</prosody>" if prosody_attrs else ""

    style_open = f"<mstts:express-as style=\"{style}\">" if style else ""
    style_close = "</mstts:express-as>" if style else ""

    ssml = f"""
    <speak version='1.0' xmlns:mstts='https://www.w3.org/2001/mstts' xml:lang='{lang}'>
        <voice name='{voice_name}'>
            {style_open}
            {prosody_open}
            {text}
            {prosody_close}
            {style_close}
        </voice>
    </speak>
    """

    url = f"https://{AZURE_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        'Ocp-Apim-Subscription-Key': AZURE_KEY,
        'Content-Type': 'application/ssml+xml',
        'X-Microsoft-OutputFormat': 'audio-16khz-128kbitrate-mono-mp3',
        'User-Agent': 'storynest-app'
    }

    response = requests.post(url, headers=headers, data=ssml.encode('utf-8'))
    if response.status_code != 200:
        raise Exception(f"Azure TTS error: {response.status_code}, {response.text}")
    return response.content



@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        text = request.form['story_text']
        voice_name = request.form['voice']
        style = request.form.get('style', '')
        pitch = request.form.get('pitch', '')
        rate = request.form.get('rate', '')
        volume = request.form.get('volume', '')

        filename = f"story_{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        audio_data = create_audio(text, voice_name, style, pitch, rate, volume)
        with open(filepath, 'wb') as f:
            f.write(audio_data)

        return redirect(url_for('result', filename=filename))
    return render_template('index.html')

@app.route('/result/<filename>')
def result(filename):
    return render_template('result.html', audio_file=filename)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        filename,
        as_attachment=True
    )

if __name__ == '__main__':
    app.run(debug=True)