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

@app.route('/dreamcanvas')
def dream_canvas():
    return render_template('DreamCanvas.html')

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

@app.route('/generate', methods=['POST'])
def generate_dream():
    dream = request.form['dream']
    filename = secure_filename(request.files['photo'].filename)
    name = request.form['name']
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    request.files['photo'].save(filepath)

    generated_text, image_filename = generate.generate_dream_image_and_plan_qwen(dream, filepath)
    
    if generated_text and image_filename:
        return render_template('DreamViewer.html', name=name, generated_text=generated_text, image_filename=image_filename)
    else:
        return jsonify({'error': 'Something went wrong'}), 500

if __name__ == '__main__':
    # 确保所有必需的模板文件都存在
    required_files = ['Home.html', 'DreamCanvas.html', 'DreamViewer.html']
    for file in required_files:
        if not os.path.exists(file):
            print(f"Missing required file: {file}")
            exit(1)
            
    app.run(debug=True, port=5001, host='0.0.0.0')