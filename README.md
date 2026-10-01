# PDF → MusicXML

Website sederhana untuk mengonversi partitur PDF menjadi file MusicXML terkompresi (`.mxl`)
yang bisa dibuka di MuseScore, Finale, Sibelius, Dorico, Noteflight, dll.

Pengenalan not (Optical Music Recognition / OMR) dikerjakan oleh
[Audiveris](https://github.com/Audiveris/audiveris) (open source, AGPL-3.0).
Website ini hanya membungkusnya dengan antarmuka unggah/unduh berbasis Flask.

## Menjalankan dengan Docker (disarankan)

```bash
docker build -t pdf2musicxml .
docker run -p 5000:5000 pdf2musicxml
```

Buka http://localhost:5000, unggah PDF, dan file `.mxl` akan langsung terunduh.

## Menjalankan tanpa Docker (Ubuntu 24.04)

```bash
# 1. Pasang Audiveris (paket .deb resmi)
curl -LO https://github.com/Audiveris/audiveris/releases/download/5.11.0/Audiveris-5.11.0-ubuntu24.04-x86_64.deb
sudo apt install ./Audiveris-5.11.0-ubuntu24.04-x86_64.deb   # Windows/macOS: pakai installer dari halaman rilis

# 2. Data OCR untuk lirik/teks. Harus versi lengkap dari repo tessdata
#    (paket tesseract-ocr-eng dari apt TIDAK bisa dipakai Audiveris).
mkdir -p ~/tessdata
curl -L -o ~/tessdata/eng.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/eng.traineddata
export TESSDATA_PREFIX=~/tessdata

# 3. Jalankan web
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Tanpa data OCR konversi tetap berjalan, tetapi lirik, simbol akor, dan teks tidak ikut terbaca.
Untuk bahasa lain, tambahkan file `.traineddata` lain (mis. `ind`, `lat`). Di Docker gunakan
`docker build --build-arg OCR_LANGS="eng ind lat" -t pdf2musicxml .`

Jika Audiveris terpasang di lokasi lain, set `AUDIVERIS_BIN=/path/ke/Audiveris`.

## Konfigurasi (environment variable)

| Variabel          | Default                          | Keterangan                       |
|-------------------|----------------------------------|----------------------------------|
| `AUDIVERIS_BIN`   | `/opt/audiveris/bin/Audiveris`   | Path ke executable Audiveris     |
| `CONVERT_TIMEOUT` | `600`                            | Batas waktu konversi (detik)     |
| `MAX_UPLOAD_MB`   | `30`                             | Ukuran maksimum file unggahan    |
| `PORT`            | `5000`                           | Port saat menjalankan `app.py`   |

## Batasan yang perlu diketahui

- **Akurasi tidak 100%.** OMR bekerja baik pada partitur cetak/digital yang bersih. Hasil buruk
  pada tulisan tangan, hasil scan miring/buram, atau notasi yang padat (piano kompleks, banyak
  ornamen). Selalu periksa ulang di MuseScore.
- **Lirik dan teks** dikenali lewat OCR dan sering kurang akurat; simbol akor kadang terbaca
  sebagai lirik.
- **Coretan/anotasi tangan** di atas partitur (mis. tulisan pulpen merah) merusak pengenalan
  pada birama tersebut. Pakai PDF yang bersih bila ada.
- **Notasi khusus** (tablatur gitar, not angka, notasi drum tertentu) umumnya tidak didukung.
- Jika PDF berisi beberapa movement, hasilnya berupa `.zip` berisi beberapa file `.mxl`.
- Proses berjalan sinkron: request menunggu sampai konversi selesai. Cukup untuk pemakaian
  pribadi/kecil; untuk banyak pengguna sekaligus sebaiknya pakai antrean job.
