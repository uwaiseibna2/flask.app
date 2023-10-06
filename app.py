from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image,ExifTags
from google.cloud import storage

app = Flask(__name__)

# Define the directory where uploaded images will be stored
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
bucket_name = 'project-2-images'
# Function to generate a unique filename based on timestamp
def generate_unique_filename(filename):
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{current_time}_{filename}"

@app.route('/')
def home():
    # Get a list of uploaded images in the UPLOAD_FOLDER
    image_files = os.listdir(app.config['UPLOAD_FOLDER'])
    return render_template('home.html', image_files=image_files)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']

        # Check if the file is empty
        if file.filename == '':
            return redirect(request.url)

        if file:
            # Securely save the uploaded file with a unique name
            filename = generate_unique_filename(secure_filename(file.filename))
            
            # Upload the file to the GCS bucket
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(filename)
            blob.upload_from_file(file)

            return redirect(url_for('home'))
    return render_template('upload.html')


@app.route('/image/<filename>')
def image(filename):
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image_size = os.path.getsize(image_path)

    # Open the image
    image = Image.open(image_path)
    # Get image metadata (EXIF data)
    exif=image.getexif()
    image_metadata = {}
    image_metadata['format']=image.format_description
    image_metadata['dimension']=image.size
    image_metadata['color mode']=image.mode
    if(exif!=None):
        image_metadata['Capturing Device']=exif.get(271,'empty')
        image_metadata['Lens']=exif.get(272,'empty')
        image_metadata['Date Captured']=exif.get(306,'empty')
    return render_template('image.html', filename=filename, image_size=image_size, image_metadata=image_metadata)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

