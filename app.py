from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from PIL import Image
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ENCODED_FOLDER'] = 'encoded/'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ENCODED_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):

    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def encode_image(image_path, message, output_path):

    image = Image.open(image_path).convert('RGB')
    encoded_image = image.copy()
    width, height = image.size
    message += '#####'  # Delimiter to mark the end of the message

    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message += '00000000'  # Adding null terminator to the end

    message_index = 0
    for row in range(height):
        for col in range(width):
            pixel = list(image.getpixel((col, row)))
            for n in range(3):  # Iterate over RGB values
                if message_index < len(binary_message):
                    pixel[n] = pixel[n] & 254 | int(binary_message[message_index])
                    message_index += 1
            encoded_image.putpixel((col, row), tuple(pixel))
    
    encoded_image.save(output_path, 'PNG')

def decode_image(image_path):
    
    image = Image.open(image_path).convert('RGB')
    width, height = image.size
    binary_message = []
    for row in range(height):
        for col in range(width):
            pixel = list(image.getpixel((col, row)))
            for n in range(3):
                binary_message.append(pixel[n] & 1)
    binary_message = ''.join(str(bit) for bit in binary_message)
    byte_array = [binary_message[i:i+8] for i in range(0, len(binary_message), 8)]
    decoded_message = ''.join(chr(int(byte, 2)) for byte in byte_array)
    
    if '#####' in decoded_message:
        return decoded_message.split('#####')[0]
    else:
        return "Oops! Nothing to decode here"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    if 'image' not in request.files or 'message' not in request.form:
        return redirect(url_for('index'))

    file = request.files['image']
    message = request.form['message']

    if file.filename == '' or not allowed_file(file.filename):
        return redirect(url_for('index'))

    input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(input_path)

    output_path = os.path.join(app.config['ENCODED_FOLDER'], 'encoded_' + os.path.splitext(file.filename)[0] + '.png')
    encode_image(input_path, message, output_path)

    return redirect(url_for('encoded_image', filename='encoded_' + os.path.splitext(file.filename)[0] + '.png'))

@app.route('/decode', methods=['POST'])
def decode():
    
    if 'image' not in request.files:
        return redirect(url_for('index'))

    file = request.files['image']

    if file.filename == '' or not allowed_file(file.filename):
        return redirect(url_for('index'))

    input_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(input_path)

    message = decode_image(input_path)
    return render_template('result.html', message=message)

@app.route('/encoded/<filename>')
def encoded_image(filename):
    return render_template('result.html', filename=filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['ENCODED_FOLDER'], filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
