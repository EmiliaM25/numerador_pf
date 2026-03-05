from flask import Flask, render_template, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from io import BytesIO
import os
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def poner_numero(page, texto, font_size=10, margen_derecho=15, margen_superior=15):
    packet = BytesIO()
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)

    can = canvas.Canvas(packet, pagesize=(width, height))
    can.setFont("Helvetica-Bold", font_size)
    can.drawRightString(width - margen_derecho, height - margen_superior, texto)
    can.save()

    packet.seek(0)
    overlay = PdfReader(packet)
    if overlay.pages:
        page.merge_page(overlay.pages[0])
    return page

def numerar_todas(input_path, output_path, numero_inicial=1, digitos=7, direccion="desde_ultima"):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    total = len(reader.pages)

    for i in range(total):  # siempre escribimos en orden normal 1..N
        page = reader.pages[i]

        if direccion == "desde_ultima":
            # última = numero_inicial
            numero = numero_inicial + (total - 1 - i)
        else:
            # primera = numero_inicial
            numero = numero_inicial + i

        texto = str(numero).zfill(digitos)
        page = poner_numero(page, texto)
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

def numerar_saltando_una(input_path, output_path, numero_inicial=1, digitos=7, direccion="desde_ultima"):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    total = len(reader.pages)

    # Selección de páginas a numerar:
    # - Si direccion = desde_ultima: numerar última, saltar una, numerar, etc.
    #   Eso equivale a numerar páginas donde (total - i) sea impar.
    # - Si direccion = desde_primera: numerar primera, saltar una, numerar, etc.
    #   Eso equivale a numerar páginas donde (i+1) sea impar.

    contador = numero_inicial

    for i in range(total):
        page = reader.pages[i]

        num_desde_final = total - i      # última=1
        num_desde_inicio = i + 1         # primera=1

        if direccion == "desde_ultima":
            # Numerar: última(1), tercera desde el final(3), quinta(5)...
            numerar_esta = (num_desde_final % 2 == 1)
        else:
            # Numerar: 1,3,5...
            numerar_esta = (num_desde_inicio % 2 == 1)

        if numerar_esta:
            texto = str(contador).zfill(digitos)
            page = poner_numero(page, texto)
            contador += 1

        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("pdf")
        if not file:
            return "No se subió ningún PDF", 400

        numero_inicial = int(request.form.get("numero_inicial", "1"))
        digitos = int(request.form.get("digitos", "7"))
        direccion = request.form.get("direccion", "desde_ultima")
        modo = request.form.get("modo", "todas")

        filename = f"{uuid.uuid4().hex}.pdf"
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, f"numerado_{filename}")

        file.save(input_path)

    if modo == "todas":
        numerar_todas(
            input_path=input_path,
            output_path=output_path,
            numero_inicial=numero_inicial,
            digitos=digitos,
            direccion=direccion
        )
    else:  # modo == "salto"
        numerar_saltando_una(
            input_path=input_path,
            output_path=output_path,
            numero_inicial=numero_inicial,
            digitos=digitos,
            direccion=direccion
        )
        return send_file(output_path, as_attachment=True, download_name="PDF_numerado.pdf")

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)