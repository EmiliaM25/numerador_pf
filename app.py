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

def poner_numero(page, texto, font_size=18, margen_derecho=15, margen_superior=15):
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

def numerar_pdf(input_path, output_path, numero_inicial=1, digitos=7, direccion="desde_ultima", modo="todas"):
    """
    modo:
      - "todas": numera todas las páginas
      - "salto": numera saltando una hoja, empezando desde la última (última=numero_inicial)

    direccion:
      - "desde_ultima" o "desde_primera" SOLO aplica en modo "todas"
      - en modo "salto" siempre es desde la última (como pediste)
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()
    total = len(reader.pages)

    # ----------------------------
    # Selección de páginas a numerar
    # ----------------------------
    if modo == "salto":
        # última, antepenúltima, quinta desde el final... (N-1, N-3, N-5...)
        indices = list(range(total - 1, -1, -2))
        # Numeración consecutiva desde la última
        mapa_numero = {}
        n = numero_inicial
        for idx in indices:  # ya está desde la última hacia atrás
            mapa_numero[idx] = n
            n += 1

    else:
        # modo == "todas"
        mapa_numero = {}
        if direccion == "desde_ultima":
            # última = numero_inicial
            for i in range(total):
                mapa_numero[i] = numero_inicial + (total - 1 - i)
        else:
            # primera = numero_inicial
            for i in range(total):
                mapa_numero[i] = numero_inicial + i

    # ----------------------------
    # Escribir el PDF en orden normal
    # ----------------------------
    for i in range(total):
        page = reader.pages[i]
        if i in mapa_numero:
            texto = str(mapa_numero[i]).zfill(digitos)
            page = poner_numero(page, texto)
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("pdf")
        if not file:
            return "No se subió ningún PDF", 400

        # ✅ FALTABA ESTO EN TU CÓDIGO
        numero_inicial = int(request.form.get("numero_inicial", "1"))
        digitos = int(request.form.get("digitos", "7"))
        direccion = request.form.get("direccion", "desde_ultima")
        modo = request.form.get("modo", "todas")  # "todas" o "salto"

        filename = f"{uuid.uuid4().hex}.pdf"
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, f"numerado_{filename}")

        file.save(input_path)

        numerar_pdf(
            input_path=input_path,
            output_path=output_path,
            numero_inicial=numero_inicial,
            digitos=digitos,
            direccion=direccion,
            modo=modo
        )

        return send_file(output_path, as_attachment=True, download_name="PDF_numerado.pdf")

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
