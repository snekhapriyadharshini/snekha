import numpy as np
from PIL import Image, ImageOps
from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configure the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uploads.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create a model for storing file info
class UploadedImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    filepath = db.Column(db.String(150), nullable=False)

# Create the database tables
with app.app_context():
    db.create_all()

def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb

def give_most_hex(file_path, code):
    my_image = Image.open(file_path).convert('RGB')
    size = my_image.size
    if size[0] >= 400 or size[1] >= 400:
        my_image = ImageOps.scale(image=my_image, factor=0.2)
    elif size[0] >= 600 or size[1] >= 600:
        my_image = ImageOps.scale(image=my_image, factor=0.4)
    elif size[0] >= 800 or size[1] >= 800:
        my_image = ImageOps.scale(image=my_image, factor=0.5)
    elif size[0] >= 1200 or size[1] >= 1200:
        my_image = ImageOps.scale(image=my_image, factor=0.6)

    my_image = ImageOps.posterize(my_image, 2)
    image_array = np.array(my_image)

    unique_colors = {}
    for column in image_array:
        for rgb in column:
            t_rgb = tuple(rgb)
            if t_rgb not in unique_colors:
                unique_colors[t_rgb] = 0
            unique_colors[t_rgb] += 1

    sorted_unique_colors = sorted(unique_colors.items(), key=lambda x: x[1], reverse=True)
    converted_dict = dict(sorted_unique_colors)
    top_10 = list(converted_dict.keys())[:10]

    if code == 'hex':
        hex_list = [rgb_to_hex(key) for key in top_10]
        return hex_list
    else:
        return top_10

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        f = request.files['file']
        colour_code = request.form['colour_code']

        # Save the uploaded file
        filename = f.filename
        filepath = os.path.join('uploads', filename)  # Define your upload directory
        os.makedirs(os.path.dirname(filepath), exist_ok=True)  # Create the directory if it doesn't exist
        f.save(filepath)

        # Save file info to the database
        new_image = UploadedImage(filename=filename, filepath=filepath)
        db.session.add(new_image)
        db.session.commit()

        colours = give_most_hex(filepath, colour_code)
        
        # Save colors for download
        with open("color_palette.txt", "w") as file:
            for color in colours:
                file.write(f"{color}\n")

        return render_template('index.html', colors_list=colours, code=colour_code, images=UploadedImage.query.all())

    return render_template('index.html', images=UploadedImage.query.all())

@app.route('/download')
def download_palette():
    return send_file("color_palette.txt", as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
