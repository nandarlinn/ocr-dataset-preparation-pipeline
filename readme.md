# PDF Page & Myanmar Text OCR Extraction Pipeline

A unified and configurable pipeline script to render PDF files into high-resolution images, extract layout bounding boxes, and recognize Myanmar text using PyMuPDF, PaddleOCR, and PyTesseract OCR.

---

## 🚀 Key Features

* **Combined & Selective Execution (`--mode` / `-m`)**:
  * **`all` (Default)**: Render PDF pages to PNGs and extract text blocks continuously.
  * **`pdf`**: Rendering phase only. Converts PDF files to PNG images at a customizable resolution.
  * **`ocr`**: OCR phase only. Scans existing image folders to generate layout bounding boxes and text annotations.
* **Flexible Directory Configuration**: Custom paths for the input PDF source folder (`--raw-dir`) and the output destination folder (`--output-dir`).
* **Custom Zoom Resolution (`--zoom` / `-z`)**: High-resolution rendering configurations (e.g., zoom factor `4.0` for ~288 DPI, `5.0` for ~360 DPI).
* **Automated Space & Name Sanitization**: Replaces space characters `' '` with underscores `'_'` in target folder names to comply with safe directory layouts.
* **Standard Annotation Integration**: Generates bounding boxes and extracted text in standard **X-AnyLabeling** JSON format directly adjacent to each rendered image.

---

## 🛠️ Prerequisites & Installation

To run this pipeline, ensure your system has `tesseract-ocr` with Myanmar language support (`mya`) installed, along with Python dependencies.

### 1. System Dependencies (Linux)

Ensure `tesseract` and the Myanmar translation package are installed on your Linux system:
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-mya libgl1-mesa-glx -y
```

### 2. Python Packages (Virtual Environment)
Ensure you are using your dedicated virtual environment:
```bash
source path/to/envs/bin/activate
pip install pymupdf opencv-python pillow pytesseract paddleocr paddlepaddle
```

---

## 💻 Usage Instructions

Always activate the virtual environment before executing the pipeline:
```bash
source path/to/envs/bin/activate
```

### 1. Run Complete Pipeline (Default)
Render all PDFs from `raw_data` to images under `dataset` directory, then automatically perform layout detection and text extraction:
```bash
python pdf_text_extraction_pipeline.py --mode all --raw-dir raw_data --output-dir dataset --zoom 5.0
```

### 2. Run PDF Rendering Phase Only
Convert PDFs to high-resolution PNG images without initiating OCR text extraction:
```bash
python pdf_text_extraction_pipeline.py --mode pdf --raw-dir raw_data --output-dir dataset --zoom 4.0
```

### 3. Run Layout & Myanmar Text OCR Phase Only
If you already rendered your PDF files, perform layout detection and Myanmar OCR on the pre-existing PNGs inside the dataset folder:
```bash
python pdf_text_extraction_pipeline.py --mode ocr --output-dir dataset
```

---

## ⚙️ Command-Line Arguments Reference

| Argument | Short | Default | Description |
| :--- | :--- | :--- | :--- |
| `--mode` | `-m` | `all` | Execution mode: `all` (both phases), `pdf` (rendering only), or `ocr` (OCR only) |
| `--raw-dir` | `-r` | `raw_data` | Directory containing raw input PDF files |
| `--output-dir`| `-o` | `dataset` | Output directory where rendered PNGs and JSON annotations will be stored |
| `--zoom` | `-z` | `5.0` | High-quality zoom factor for PDF page rendering (e.g. `4.0` / `5.0`) |

---

## 📁 Output Folder Structure

After a successful run, your output directory will look like this:
```text
dataset/
└── my_pdf_document_name/
    ├── page_001.png
    ├── page_001.json   <-- X-AnyLabeling compatible annotation containing OCR text
    ├── page_002.png
    └── page_002.json
```

## Open X-AnyLabeling
```bash
xanylabeling
```
![Img-1](https://github.com/nandarlinn/ocr-dataset-preparation-pipeline/blob/main/img/img1.png)
