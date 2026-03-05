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

def numerar_pdf(input_path, output_path, numero_inicial=1, digitos=7, direccion="desde_ultima", modo="todas"):
    reader = PdfReader(input_path)
    writer = PdfWriter()
    total = len(reader.pages)

    # 1) Definir qué páginas se numeran (índices 0..total-1)
    if modo == "todas":
        indices = list(range(total))
    elif modo == "salto_final":
        # Saltando una hoja desde el FINAL: ultima, anteultima-2, etc.
        indices = list(range(total - 1, -1, -2))
        indices.sort()  # importante: para escribir el PDF en orden normal
    elif modo == "salto_inicio":
        # (opcional) saltando desde el inicio: 0,2,4...
        indices = list(range(0, total, 2))
    else:
        indices = list(range(total))

    # 2) Calcular numeración SOLO para páginas seleccionadas
    # Queremos que:
    # - si direccion="desde_ultima": la última página seleccionada = numero_inicial (y hacia atrás suma)
    # - si direccion="desde_primera": la primera página seleccionada = numero_inicial (y hacia adelante suma)
    if direccion == "desde_ultima":
        indices_orden_numeracion = list(reversed(indices))  # empezamos por la última seleccionada
    else:
        indices_orden_numeracion = indices[:]               # empezamos por la primera seleccionada

    mapa_numero = {}
    n = numero_inicial
    for idx in indices_orden_numeracion:
        mapa_numero[idx] = n
        n += 1

    # 3) Escribir páginas en orden normal y poner número solo donde toca
    for i in range(total):
        page = reader.pages[i]

        if i in mapa_numero:
            texto = str(mapa_numero[i]).zfill(digitos)
            page = poner_numero(page, texto)

        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)
def numerar_saltando_una(input_path, output_path, numero_inicial=1, digitos=7, direccion="desde_ultima"):
    """
    Numerar una página sí / una no, con numeración consecutiva.
    - desde_ultima: numera última, salta una, numera, ...
    - desde_primera: numera primera, salta una, numera, ...
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()
    total = len(reader.pages)

    contador = numero_inicial

    for i in range(total):
        page = reader.pages[i]

        num_desde_final = total - i   # última=1
        num_desde_inicio = i + 1      # primera=1

        if direccion == "desde_ultima":
            numerar_esta = (num_desde_final % 2 == 1)   # 1,3,5 desde el final
        else:
            numerar_esta = (num_desde_inicio % 2 == 1)  # 1,3,5 desde el inicio

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
        modo = request.form.get("modo", "todas")  # <- VIENE DE TU SELECT

        filename = f"{uuid.uuid4().hex}.pdf"
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, f"numerado_{filename}")

        file.save(input_path)

        # Elegir modo
        if modo == "salto":
            numerar_saltando_una(
                input_path=input_path,
                output_path=output_path,
                numero_inicial=numero_inicial,
                digitos=digitos,
                direccion=direccion
            )
        else:
            numerar_todas(
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