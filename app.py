from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from google.cloud import storage
import os
import io
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from PIL.ExifTags import TAGS
from google.cloud import storage
bucket_name='project-2-images'
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Set your secret key for session security

# Configuration for SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

# User model for database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
def generate_unique_filename(filename):
    current_time = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{current_time}_{filename}"
# Flask-Login user loader function
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            return "Invalid username or password"

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "This username already exists. Please choose a different one."

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('register.html', register=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    # Initialize the Google Cloud Storage client
    storage_client = storage.Client()

    # Get a list of all objects (images) in the GCS bucket
    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs()

    # Filter images to display only those associated with the current user
    user_images = []
    for blob in blobs:
        associated_user_id = blob.metadata.get('associated_user')
        if associated_user_id == current_user.username:
            user_images.append(blob.name)

    return render_template('home.html', image_files=user_images, username=current_user.username)

@login_required
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        if file:
            filename = generate_unique_filename(secure_filename(file.filename))
            storage_client = storage.Client()
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(filename)
            blob.upload_from_file(file)
            exif_data = {}
            try:
                with Image.open(file) as img:
                    if hasattr(img, '_getexif'):
                        exif_info = img._getexif()
                        if exif_info is not None:
                            # Specify the EXIF tags you want to extract
                            desired_tags = {
                                'Make': TAGS.get('Make', 'Make'),
                                'Model': TAGS.get('Model', 'Model'),
                                'ISO': TAGS.get('ISOSpeedRatings', 'ISO'),
                                # Add more tags as needed
                            }
                            for tag, value in exif_info.items():
                                tag_name = TAGS.get(tag, tag)
                                if tag_name in desired_tags:
                                    exif_data[desired_tags[tag_name]] = value
            except Exception as e:
                print(f"Error extracting EXIF data: {str(e)}")
            
            metadata = {
                'size': str(blob.size)+" Bytes" ,  # Convert the size to a string
                'directory': bucket_name+"/"+filename,
                'name': filename,
                'associated_user': current_user.username,
                **exif_data
            }

            blob.metadata = metadata

            # Update the object's metadata in the bucket
            blob.patch()

            return redirect(url_for('home'))
    return render_template('upload.html')

@app.route('/image/<filename>', methods=['GET', 'POST'])
def image(filename):
    storage_client = storage.Client()
    gcs_url = f'https://storage.googleapis.com/{bucket_name}/{filename}'
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.get_blob(filename)

    if blob.exists():
        image_metadata = blob.metadata
    else:
        image_metadata = {'Status': 'Image not found in GCS bucket'}

    if request.method == 'POST':
        # Delete image if the delete button is pressed
        if 'delete_image' in request.form:

            blob.delete()  # Delete the image blob
            return redirect(url_for('home'))

    return render_template('image.html', filename=filename, gcs_url=gcs_url, image_metadata=image_metadata)


@app.route('/download/<filename>')
def download(filename):
    # Construct the GCS URL for the file to be downloaded
    gcs_url = f'https://storage.googleapis.com/{bucket_name}/{filename}'

    # Redirect the user to the GCS URL for download
    return redirect(gcs_url)
@app.errorhandler(401)
def unauthorized(error):
    return redirect(url_for('login'))
if __name__ == "__main__":
    # Move the db.create_all() method here before running the app
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

