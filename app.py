import os
import generate
import share
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from PIL import Image
from io import BytesIO
import uuid

app = Flask(__name__, template_folder='.')
app.config['UPLOAD_FOLDER'] = 'uploads'
# Create the uploads directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route('/')
def home():
    return render_template('Home.html')

import config
import webbrowser
from threading import Timer

@app.route('/dreamcanvas')
def dream_canvas():
    available_services = config.get_available_services()
    return render_template('DreamCanvas.html', available_services=available_services)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/share', methods=['POST'])
def share_dream():
    data = request.get_json()
    image_filename = data.get('image_filename')
    text = data.get('text')
    name = data.get('name')

    if not image_filename or not text or not name:
        return jsonify({'error': 'Missing image_filename, text, or name'}), 400

    # 1. Create the composite image
    try:
        composite_filename = share.create_composite_image(image_filename, text, name)
    except Exception as e:
        print(f"Error creating composite image: {e}")
        return jsonify({'error': 'Could not create composite image'}), 500

    # 2. Share the composite image and get QR code
    qr_filename = share.share(composite_filename)
    if qr_filename:
        qr_code_url = url_for('uploaded_file', filename=qr_filename, _external=True)
        return jsonify({'qr_code_url': qr_code_url})
    else:
        return jsonify({'error': 'Could not share image'}), 500

@app.route('/download_composite', methods=['POST'])
def download_composite():
    data = request.get_json()
    image_filename = data.get('image_filename')
    text = data.get('text')
    name = data.get('name')

    if not image_filename or not text or not name:
        return jsonify({'error': 'Missing image_filename, text, or name'}), 400

    try:
        composite_filename = share.create_composite_image(image_filename, text, name)
        return send_from_directory(app.config['UPLOAD_FOLDER'], composite_filename, as_attachment=True)
    except Exception as e:
        print(f"Error creating composite image: {e}")
        return jsonify({'error': 'Could not create composite image'}), 500

@app.route('/generate', methods=['POST'])
def generate_dream():
    dream = request.form['dream']
    filename = secure_filename(request.files['photo'].filename)
    name = request.form['name']
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    request.files['photo'].save(filepath)

    # generated_text, image_filename = generate.generate_dream_image_and_plan_qwen(dream, filepath)
    # generated_text, image_filename = generate.generate_dream_image_and_plan_doubao(dream, filepath)
    # generated_text, image_filename = generate.generate_dream_image_and_plan(dream, filepath)
    
    api_service = request.form['api_service']

    if api_service == 'gemini':
        generated_text, image_filename = generate.generate_dream_image_and_plan(dream, filepath)
    elif api_service == 'qwen':
        generated_text, image_filename = generate.generate_dream_image_and_plan_qwen(dream, filepath)
    elif api_service == 'doubao':
        generated_text, image_filename = generate.generate_dream_image_and_plan_doubao(dream, filepath)
    else:
        return jsonify({'error': 'Invalid API service selected'}), 400
    
    if generated_text and image_filename:
        return render_template('DreamViewer.html', name=name, generated_text=generated_text, image_filename=image_filename)
    else:
        return jsonify({'error': 'Something went wrong'}), 500

def open_browser():
    webbrowser.open_new("http://127.0.0.1:5001/")

if __name__ == '__main__':
    config.init_config()
    # 确保所有必需的模板文件都存在
    required_files = ['Home.html', 'DreamCanvas.html', 'DreamViewer.html']
    for file in required_files:
        if not os.path.exists(file):
            print(f"Missing required file: {file}")
            exit(1)
    
    Timer(1, open_browser).start()
    app.run(debug=False, port=5001, host='127.0.0.1')