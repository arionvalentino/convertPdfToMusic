"""Website sederhana untuk mengonversi PDF partitur menjadi MusicXML (.mxl).

Pengenalan not (OMR) dilakukan oleh Audiveris yang dipanggil lewat CLI.
"""
import os
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from flask import Flask, render_template, request, send_file, after_this_request
from werkzeug.utils import secure_filename

AUDIVERIS_BIN = os.environ.get("AUDIVERIS_BIN", "/opt/audiveris/bin/Audiveris")
TIMEOUT_SECONDS = int(os.environ.get("CONVERT_TIMEOUT", "600"))
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "30"))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


def convert_pdf(pdf_path: Path, out_dir: Path) -> Path:
    """Jalankan Audiveris dan kembalikan path file .mxl hasilnya."""
    cmd = [AUDIVERIS_BIN, "-batch", "-export", "-output", str(out_dir), "--", str(pdf_path)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
    # Partitur multi-movement bisa menghasilkan beberapa file (nama.mvt1.mxl, ...)
    outputs = sorted(out_dir.rglob("*.mxl"))
    if not outputs:
        log_tail = (result.stdout + result.stderr)[-1500:]
        raise RuntimeError(log_tail or "Audiveris tidak menghasilkan output.")
    if len(outputs) == 1:
        return outputs[0]
    bundle = shutil.make_archive(str(out_dir / f"{pdf_path.stem}-musicxml"), "zip", out_dir, ".")
    return Path(bundle)


@app.get("/")
def index():
    return render_template("index.html", max_mb=MAX_UPLOAD_MB)


@app.post("/convert")
def convert():
    upload = request.files.get("file")
    if not upload or not upload.filename:
        return render_template("index.html", max_mb=MAX_UPLOAD_MB, error="Pilih file PDF terlebih dahulu."), 400
    name = secure_filename(upload.filename) or "score.pdf"
    if not name.lower().endswith(".pdf"):
        return render_template("index.html", max_mb=MAX_UPLOAD_MB, error="File harus berformat PDF."), 400

    work = Path(tempfile.mkdtemp(prefix="pdf2mxl-"))

    @after_this_request
    def cleanup(response):
        shutil.rmtree(work, ignore_errors=True)
        return response

    pdf_path = work / name
    upload.save(pdf_path)
    if pdf_path.read_bytes()[:5] != b"%PDF-":
        return render_template("index.html", max_mb=MAX_UPLOAD_MB, error="File bukan PDF yang valid."), 400

    try:
        output = convert_pdf(pdf_path, work / "out")
    except subprocess.TimeoutExpired:
        return render_template("index.html", max_mb=MAX_UPLOAD_MB,
                               error=f"Konversi melebihi batas waktu {TIMEOUT_SECONDS} detik."), 504
    except Exception as exc:  # noqa: BLE001 - tampilkan pesan ke pengguna
        return render_template("index.html", max_mb=MAX_UPLOAD_MB,
                               error="Gagal mengenali partitur.", detail=str(exc)), 422

    data = output.read_bytes()  # baca ke memori supaya folder kerja aman dihapus
    mimetype = "application/zip" if output.suffix == ".zip" else "application/vnd.recordare.musicxml"
    return send_file(BytesIO(data), as_attachment=True, download_name=output.name, mimetype=mimetype)


@app.errorhandler(413)
def too_large(_):
    return render_template("index.html", max_mb=MAX_UPLOAD_MB,
                           error=f"Ukuran file melebihi {MAX_UPLOAD_MB} MB."), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
