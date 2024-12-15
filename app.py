from flask import Flask, render_template, request, jsonify, send_file
from PyPDF2 import PdfReader, PdfWriter
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/count_pages', methods=['POST'])
def count_pages():
    pdf_files = request.files.getlist('pdf_files')  # Handle multiple files
    results = []

    try:
        for pdf_file in pdf_files:
            # Read the PDF
            reader = PdfReader(pdf_file)
            num_pages = len(reader.pages)
            results.append(f"File: {pdf_file.filename} has {num_pages} pages.")

        # Return results as a list of messages
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 400

@app.route('/rotate_page', methods=['POST'])
def rotate_page():
    try:
        pdf_file = request.files['pdf_file']
        angle = int(request.form['angle'])
        pages = request.form['pages']

        print(f"Processing file: {pdf_file.filename}, Angle: {angle}, Pages: {pages}")
        page_numbers = parse_page_numbers(pages)

        reader = PdfReader(pdf_file)
        writer = PdfWriter()

        for i, page in enumerate(reader.pages):
            if i in page_numbers:
                page.rotate(angle)
            writer.add_page(page)

        output_pdf_stream = io.BytesIO()
        writer.write(output_pdf_stream)
        output_pdf_stream.seek(0)

        print(f"Rotated PDF generated. Size: {output_pdf_stream.tell()} bytes")
        return send_file(output_pdf_stream, as_attachment=True, download_name="rotated_output.pdf", mimetype='application/pdf')

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': f'Error: {str(e)}'}), 400

@app.route('/merge_pdfs', methods=['POST'])
def merge_pdfs():
    files = request.files.getlist('pdf_files')
    writer = PdfWriter()
    try:
        for pdf in files:
            reader = PdfReader(pdf)
            for page in reader.pages:
                writer.add_page(page)

        output_pdf_stream = io.BytesIO()
        writer.write(output_pdf_stream)
        output_pdf_stream.seek(0)

        print(f"Merged PDF generated. Size: {output_pdf_stream.tell()} bytes")
        return send_file(output_pdf_stream, as_attachment=True, download_name="merged_output.pdf", mimetype='application/pdf')
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': f'Error: {str(e)}'}), 400


def parse_page_numbers(pages):
    """
    Parse page numbers from a string like "1,2,3-5".
    Returns a set of zero-based page indices.
    """
    page_numbers = set()
    for part in pages.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            page_numbers.update(range(start - 1, end))
        else:
            page_numbers.add(int(part) - 1)
    return page_numbers

if __name__ == '__main__':
    app.run(debug=True)
