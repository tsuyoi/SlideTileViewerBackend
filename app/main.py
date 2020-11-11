from flask import Flask, jsonify
import os

from parsers import ISyntaxParser, OpenslideParser

app = Flask(__name__)

isyntax_ext = ['.isyntax']
isyntax_file = None

openslide_exts = ['.bif', '.mrxs', '.ndpi', '.scn', '.svs', '.svslide', '.tif', '.vms', '.vmu']
openslide_file = None

for file in os.listdir('/tmp/'):
    file_name, file_ext = os.path.splitext(file)
    if file_ext in isyntax_ext:
        isyntax_file = file
    if file_ext in openslide_exts:
        openslide_file = file

slide_file = isyntax_file if isyntax_file is not None else openslide_file
if slide_file is None:
    exit(1)

slide_path = f"/tmp/{slide_file}"
slide_name, slide_ext = os.path.splitext(slide_path)
print(f"slide_file: {slide_file}, slide_path: {slide_path}, slide_name: {slide_name}, slide_ext: {slide_ext}")


@app.route('/properties')
def slide_properties():
    if slide_ext == ".isyntax":
        parser = ISyntaxParser(slide_path)
    else:
        parser = OpenslideParser(slide_path)
    return jsonify(parser.slide_properties())


@app.route('/patch/<int:left>/<int:top>/<int:width>/<int:height>')
def get_patch(left, top, width, height):
    if slide_ext == ".isyntax":
        parser = ISyntaxParser(slide_path)
    else:
        parser = OpenslideParser(slide_path)
    return jsonify(parser.region_pixel_data(left, top, width, height))


@app.route('/patch/<int:left>/<int:top>/<int:width>/<int:height>/<int:level>')
def get_patch_with_level(left, top, width, height, level):
    if slide_ext == ".isyntax":
        parser = ISyntaxParser(slide_path)
    else:
        parser = OpenslideParser(slide_path)
    return jsonify(parser.region_pixel_data(left, top, width, height, level))


@app.route('/')
def index():
    info = {
        'version': 1.0
    }
    return jsonify(info)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
