from flask import Flask, render_template, request, redirect, url_for, session, Response
import requests
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
import io
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for session management

@app.route('/')
def index():
    if 'api_key' not in session:
        return redirect(url_for('setup'))
    return render_template('index.html')

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if request.method == 'POST':
        session['api_key'] = request.form['api_key']
        return redirect(url_for('index'))
    return render_template('setup.html')

@app.route('/submit', methods=['POST'])
def submit():
    if 'api_key' not in session:
        return redirect(url_for('setup'))

    api_key = session['api_key']
    addresses = request.form.get('address', '').split(',')

    results = []
    for address in addresses:
        address = address.strip()
        try:
            response = requests.get(f'https://public.chainalysis.com/api/v1/address/{address}', headers={'X-API-KEY': api_key})
            response.raise_for_status()
            datas = response.json()["identifications"]

            description = name = url = ""
            if datas:
                for data in datas:
                    if data["category"] == "sanctions":
                        url = data["url"]
                        description = data["description"].replace(url, '').replace('; ', ';\n')
                        name = data["name"]

            results.append({
                'address': address,
                'name': name,
                'description': description,
                'url': url
            })

        except requests.RequestException as e:
            results.append({'address': address, 'error': "Error fetching data: " + str(e)})

    return render_template('index.html', results=results)

@app.route('/export', methods=['POST'])
def export_pdf():
    if 'api_key' not in session:
        return redirect(url_for('setup'))

    addresses = request.form.getlist('address')
    names = request.form.getlist('name')
    descriptions = request.form.getlist('description')
    urls = request.form.getlist('url')

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    title_style = ParagraphStyle(name='Title', fontSize=14, spaceAfter=12, fontName='DejaVuSans')
    header_style = ParagraphStyle(name='Header', fontSize=12, spaceAfter=6, fontName='DejaVuSans')
    body_style = ParagraphStyle(name='Body', fontSize=10, spaceAfter=10, fontName='DejaVuSans')

    pdfmetrics.registerFont(TTFont('DejaVuSans', 'templates/fonts/dejavu-sans/DejaVuSans.ttf'))

    story = []

    for address, name, description, url in zip(addresses, names, descriptions, urls):
        print(description)
        story.append(Paragraph(f"Crypto Address: {address}\n", title_style))
        story.append(Paragraph(f"Name: {name}\n", header_style))
        story.append(Paragraph(f"Description: {description}\n", body_style))
        story.append(Paragraph(f"URL: <a href='{url}'>{url}</a>", body_style))
        story.append(Paragraph("<br /><br />", body_style))

    doc.build(story)

    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()

    return Response(pdf_data, mimetype='application/pdf', headers={"Content-Disposition": f"attachment;filename=report_address_{address[:10]}.pdf"})

if __name__ == "__main__":
    app.run(debug=True)
