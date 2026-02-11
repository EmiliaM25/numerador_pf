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
    total_pages = len(reader.pages)

    paginas_finales = [None] * total_pages

    if modo == "todas":
        # TODAS: última=1, anterior=2...
        contador = 1
        for idx in range(total_pages - 1, -1, -1):
            page = reader.pages[idx]
            page = poner_numero(page, contador, digitos=digitos)
            paginas_finales[idx] = page
            contador += 1

        # completar (aunque ya están todas)
        for i in range(total_pages):
            if paginas_finales[i] is None:
                paginas_finales[i] = reader.pages[i]

    elif modo == "impares":
        # SOLO IMPARES: última impar=1, anterior impar=2...
        impares = [p for p in range(1, total_pages + 1) if p % 2 == 1]  # 1-based
        contador = 1
        for p in reversed(impares):
            idx = p - 1
            page = reader.pages[idx]
            page = poner_numero(page, contador, digitos=digitos)
            paginas_finales[idx] = page
            contador += 1

        # las demás quedan igual (sin número)
        for i in range(total_pages):
            if paginas_finales[i] is None:
                paginas_finales[i] = reader.pages[i]

    elif modo == "pares":
        # SOLO PARES: última par=1, anterior par=2...
        pares = [p for p in range(1, total_pages + 1) if p % 2 == 0]  # 1-based
        contador = 1
        for p in reversed(pares):
            idx = p - 1
            page = reader.pages[idx]
            page = poner_numero(page, contador, digitos=digitos)
            paginas_finales[idx] = page
            contador += 1

        # las demás quedan igual (sin número)
        for i in range(total_pages):
            if paginas_finales[i] is None:
                paginas_finales[i] = reader.pages[i]

    else:
        raise ValueError("Modo no reconocido.")

    writer = PdfWriter()
    for p in paginas_finales:
        writer.add_page(p)

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


