from flask import Flask, render_template, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from io import BytesIO
import os

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def poner_numero(page, numero, digitos=7, font_size=10, margen_derecho=15, margen_superior=15):
    packet = BytesIO()
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)

    can = canvas.Canvas(packet, pagesize=(width, height))
    texto = str(numero).zfill(digitos)

    # Superior derecha
    can.setFont("Helvetica-Bold", font_size)
    can.drawRightString(width - margen_derecho, height - margen_superior, texto)

    can.save()
    packet.seek(0)

    overlay = PdfReader(packet)
    if overlay.pages:
        page.merge_page(overlay.pages[0])

    return page

def numerar_pdf(input_path, output_path, modo, digitos=7):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    total = len(reader.pages)

    contador = 1

    for i in range(total):
        page = reader.pages[i]
        numero_pagina_real = i + 1
        numero_desde_final = total - i

        if modo == "todas":
            numero = numero_desde_final
            page = poner_numero(page, numero, digitos)

        elif modo == "impares":
            if numero_pagina_real % 2 == 1:
                numero = numero_desde_final
                page = poner_numero(page, contador, digitos)
                contador += 1

        elif modo == "pares":
            if numero_pagina_real % 2 == 0:
                numero = numero_desde_final
                page = poner_numero(page, contador, digitos)
                contador += 1

        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["pdf"]
        modo = request.form.get("modo", "todas")

        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        output_path = os.path.join(OUTPUT_FOLDER, "pdf_numerado.pdf")

        file.save(input_path)

        numerar_pdf(input_path, output_path, modo, digitos=7)

        return send_file(output_path, as_attachment=True)

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


