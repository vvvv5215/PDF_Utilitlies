from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
import PyPDF2
import webbrowser

app = Flask(__name__)
app.secret_key = "supersecretkey"
app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/count_pages', methods=['POST'])
def count_pages():
    files = request.files.getlist('pdf_files')
    if not files or files[0].filename == '':
        flash('No files selected')
        return redirect(url_for('index'))

    result_text = ""
    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        num_pages = process_pdf(file_path)
        result_text += f"Selected file: {filename}\n"
        result_text += f'The PDF file has {num_pages} pages.\n'
    
    flash(result_text)
    return redirect(url_for('index'))

@app.route('/rotate_page', methods=['POST'])
def rotate_page():
    file = request.files['pdf_file']
    if not file or file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))
    
    rotation_angle = int(request.form['angle'])
    pageno = int(request.form['page']) - 1
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    rotated_file_path = rotate_pdf(file_path, rotation_angle, pageno)
    flash(f"Page {pageno + 1} of the PDF file has been rotated by {rotation_angle} degrees. Saved as {rotated_file_path}")
    return redirect(url_for('index'))

@app.route('/merge_pdfs', methods=['POST'])
def merge_pdfs():
    files = request.files.getlist('pdf_files')
    if not files or files[0].filename == '':
        flash('No files selected')
        return redirect(url_for('index'))
    
    file_paths = []
    for file in files:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        file_paths.append(file_path)
    
    merged_file_path = merge_pdfs(file_paths)
    flash(f"The PDF files have been merged into {merged_file_path}")
    return redirect(url_for('index'))

def process_pdf(file_path):
    with open(file_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        num_pages = len(pdf.pages)
        return num_pages

def rotate_pdf(file_path, angle, pageno):
    with open(file_path, 'rb') as f:
        pdf = PyPDF2.PdfReader(f)
        output_pdf = PyPDF2.PdfWriter()
        
        for page_num in range(len(pdf.pages)):
            page = pdf.pages[page_num]
            if page_num == pageno:
                page.rotate(angle)
            output_pdf.add_page(page)
        
        rotated_file_path = file_path.replace(".pdf", f"_rotated_{angle}_page_{pageno + 1}.pdf")
        with open(rotated_file_path, 'wb') as out_f:
            output_pdf.write(out_f)
        
        return rotated_file_path

def merge_pdfs(file_paths):
    output_pdf = PyPDF2.PdfWriter()
    
    for file_path in file_paths:
        with open(file_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            for page_num in range(len(pdf.pages)):
                output_pdf.add_page(pdf.pages[page_num])
    
    merged_file_path = "merged_output.pdf"
    with open(merged_file_path, 'wb') as out_f:
        output_pdf.write(out_f)
    
    return merged_file_path

if __name__ == '__main__':
    app.run(debug=True, port=5001)
