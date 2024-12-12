from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import os
import PyPDF2
import io

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Use the /tmp directory for temporary storage in a serverless environment
app.config['UPLOAD_FOLDER'] = '/tmp/uploads/'
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
        try:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            num_pages = process_pdf(file_path)
            if num_pages > 0:
                result_text += f"Selected file: {filename}\n"
                result_text += f'The PDF file has {num_pages} pages.'
            else:
                result_text += f"Could not read the file: {filename}.\n"
        except Exception as e:
            result_text += f"An error occurred with the file: {file.filename}. Error: {e}\n"

    flash(result_text)
    return redirect(url_for('index'))


@app.route('/rotate_page', methods=['POST'])
def rotate_page():
    file = request.files['pdf_file']
    if not file or file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))

    try:
        rotation_angle = int(request.form['angle'])
        pageno = int(request.form['page']) - 1

        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        rotated_pdf_stream = rotate_pdf_to_stream(file_path, rotation_angle, pageno)

        # Return the rotated PDF as a file download
        return send_file(
            rotated_pdf_stream,
            as_attachment=True,
            download_name=f"rotated_{filename}",
            mimetype="application/pdf"
        )
    except Exception as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('index'))

@app.route('/merge_pdfs', methods=['POST'])
def merge_pdfs():
    files = request.files.getlist('pdf_files')
    if not files or files[0].filename == '':
        flash('No files selected')
        return redirect(url_for('index'))

    try:
        file_paths = []
        for file in files:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            file_paths.append(file_path)

        merged_pdf_stream = merge_pdfs_to_stream(file_paths)

        # Return the merged PDF as a file download
        return send_file(
            merged_pdf_stream,
            as_attachment=True,
            download_name="merged_output.pdf",
            mimetype="application/pdf"
        )
    except Exception as e:
        flash(f"An error occurred: {str(e)}")
        return redirect(url_for('index'))

def process_pdf(file_path):
    try:
        with open(file_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            num_pages = len(pdf.pages)
            return num_pages
    except Exception as e:
        print(f"Error processing PDF file: {file_path}. Error: {e}")
        return 0

def rotate_pdf_to_stream(file_path, angle, pageno):
    try:
        with open(file_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            output_pdf = PyPDF2.PdfWriter()
            
            for page_num in range(len(pdf.pages)):
                page = pdf.pages[page_num]
                if page_num == pageno:
                    page.rotate(angle)
                output_pdf.add_page(page)

            # Save the rotated PDF to an in-memory stream
            output_stream = io.BytesIO()
            output_pdf.write(output_stream)
            output_stream.seek(0)
            return output_stream
    except Exception as e:
        print(f"Error rotating PDF: {file_path}. Error: {e}")
        raise

def merge_pdfs_to_stream(file_paths):
    output_pdf = PyPDF2.PdfWriter()
    output_stream = io.BytesIO()

    for file_path in file_paths:
        with open(file_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            for page_num in range(len(pdf.pages)):
                output_pdf.add_page(pdf.pages[page_num])

    output_pdf.write(output_stream)
    output_stream.seek(0)
    return output_stream

# Expose the app callable for Vercel
if __name__ == '__main__':
    app.run(debug=True, port=5001)
