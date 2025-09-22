import os
import generate
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO
import uuid

app = Flask(__name__, template_folder='.')
app.config['UPLOAD_FOLDER'] = 'uploads'

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
def generate_dream():
    dream = request.form['dream']
    filename = secure_filename(request.files['file'].filename)
    name = request.form['name']
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    request.files['file'].save(filepath)

    response = generate.generate_dream_image_and_plan(dream, filepath)
    generated_text = ""
    image_filename = ""

    for part in response.candidates[0].content.parts:
        if part.text is not None:
            generated_text = part.text
        elif part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data))
            # save the image with uuid as filename
            image_filename = "generated_image_{}.png".format(uuid.uuid4())
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        elif part.text is None and part.inline_data is None:
            continue 

    if response:
        return render_template('DreamViewer.html', name=name, generated_text=generated_text, image_filename=image_filename)
    else:
        return jsonify({'error': 'Something went wrong'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
