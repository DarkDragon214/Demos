import cv2
from PIL import Image
from flask import Flask, request, render_template, redirect, url_for, jsonify, send_from_directory, send_file
from hide import get_result, psnr, mse
from extract import get_stego
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    print(f"Created directory: {UPLOAD_FOLDER}")

if not os.path.exists("static/output"):
    os.makedirs("static/output")
    print(f"Created directory: static/output")

CARRIER_FILES = {'png', 'bmp', 'tiff'}
SECRET_FILES = {'png', 'jpg', 'jpeg', 'bmp', 'tiff', 'txt'}


def allowed_file_carrier(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in CARRIER_FILES


def allowed_file_secret(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in SECRET_FILES


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/encrypt')
def encrypt():
    return render_template('encrypt.html')


@app.route('/hide')
def hide():
    return render_template('hide.html')


@app.route('/unhide')
def unhide():
    return render_template('Unhide.html')


@app.route('/uploadStego', methods=['POST'])
def upload_stego():
    if 'stego_file' not in request.files:
        return 'No file part', 400

    stego_file = request.files['stego_file']

    if not stego_file:
        return 'No file selected', 400

    if allowed_file_carrier(stego_file.filename):
        stego_filename = os.path.join(app.config['UPLOAD_FOLDER'], stego_file.filename)
        stego_file.save(stego_filename)

        password = request.form.get('decryptPassword', '')
        # print(request.form)
        # print(password)
        res_file = get_stego(stego_file, password)

        if res_file == -1:
            return "No secret file found. May be corrupted."
        return send_file(f"static/output/{res_file}", as_attachment=True, download_name=res_file)

    return 'Invalid file format', 400

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'carrier_file' not in request.files or 'secret_file' not in request.files:
        return 'No file part', 400

    carrier_file = request.files['carrier_file']
    secret_file = request.files['secret_file']

    if not carrier_file or not secret_file:
        return 'No file selected', 400

    if carrier_file and allowed_file_carrier(carrier_file.filename) and secret_file and \
            allowed_file_secret(secret_file.filename):

        carrier_filename = os.path.join(app.config['UPLOAD_FOLDER'], carrier_file.filename)
        secret_filename = os.path.join(app.config['UPLOAD_FOLDER'], secret_file.filename)

        with Image.open(carrier_filename) as img:
            width, height = img.size
        carrier_file_size = (width * height * 3) / 8
        secret_file_size = os.path.getsize(secret_filename)
        if secret_file_size + 4 > carrier_file_size: # Added 4 bytes to account for the terminator
            return "Secret file too large"

        output_image = os.path.join("static/output", carrier_file.filename)
        password = request.form.get('encryptPassword', '')
        if not (len(password) > 12 or len(password) == 0):
            return "Password must be at least 12 characters long"
        get_result(carrier_filename, secret_filename, password, output_image)

        psnr_value = psnr(carrier_filename, output_image)
        mse_value = mse(carrier_filename, output_image)

        return render_template('preview.html',
                               image_url=url_for('static', filename='output/' + carrier_file.filename),
                               psnr=psnr_value, mse=mse_value)

    return 'Invalid file format', 400


@app.route('/show_max_size', methods=['POST'])
def show_max_size():
    carrier_file = request.files['carrier_file']
    secret_file = request.files['secret_file']

    if not carrier_file or not secret_file:
        return jsonify({"error": "No files provided"}), 400

    carrier_filename = os.path.join(app.config['UPLOAD_FOLDER'], carrier_file.filename)
    secret_filename = os.path.join(app.config['UPLOAD_FOLDER'], secret_file.filename)

    carrier_file.save(carrier_filename)
    secret_file.save(secret_filename)

    with Image.open(carrier_filename) as img:
        width, height = img.size
    carrier_file_size = (width * height * 3) / 8
    secret_file_size = os.path.getsize(secret_filename)

    progress_percentage = (secret_file_size / carrier_file_size) * 100 if carrier_file_size else 0

    return jsonify(
        max_secret_file_size=carrier_file_size / (1024 * 1024),
        progress_percentage=progress_percentage
    )


@app.route('/get_max_size', methods=['POST'])
def get_max_size():
    carrier_file = request.files['carrier_file']

    if not carrier_file:
        return jsonify({"error": "No carrier file provided"}), 400

    carrier_filename = os.path.join(app.config['UPLOAD_FOLDER'], carrier_file.filename)
    carrier_file.save(carrier_filename)

    with Image.open(carrier_filename) as img:
        width, height = img.size

    carrier_file_size = (width * height * 3) / 8

    return jsonify(
        max_secret_file_size=carrier_file_size / (1024 * 1024),
    )


if __name__ == '__main__':
    app.run(debug=True)
