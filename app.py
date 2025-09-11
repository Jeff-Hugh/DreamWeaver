import os
import google.generativeai as genai
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename

# Configure the Gemini API key
# Make sure to set the GOOGLE_API_KEY environment variable
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("GOOGLE_API_KEY environment variable not set.")
    exit()

app = Flask(__name__, template_folder='.')
app.config['UPLOAD_FOLDER'] = 'uploads'

# Generation configuration for the model
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 1,
    "max_output_tokens": 2048,
}

# Safety settings for the model
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

# Initialize the generative model
model = genai.GenerativeModel(
    model_name="gemini-pro-vision",
    generation_config=generation_config,
    safety_settings=safety_settings,
)

@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/dreamcanvas')
def dream_canvas():
    return render_template('DreamCanvas.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/generate', methods=['POST'])
def generate():
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo uploaded'}), 400

    file = request.files['photo']
    name = request.form['name']
    dream = request.form['dream']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Prepare the image for the model
        image_part = {
            "mime_type": file.mimetype,
            "data": open(filepath, "rb").read(),
        }

        # Create the prompt for the model
        prompt_parts = [
            image_part,
            f"我的名字是{name}。我的梦想是{dream}。请以中文为我实现梦想写一个简短励志的故事。",
        ]

        # Generate content
        try:
            response = model.generate_content(prompt_parts)
            generated_text = response.text
        except Exception as e:
            print(f"Error generating content: {e}")
            return jsonify({'error': 'Failed to generate content from Gemini API.'}), 500


        return render_template('DreamViewer.html', name=name, dream=dream, generated_text=generated_text, image_filename=filename)

    return jsonify({'error': 'Something went wrong'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
