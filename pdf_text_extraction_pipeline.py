import os
import sys
import glob
import json
import argparse
import cv2
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from paddleocr import PaddleOCR

def clean_folder_name(pdf_name):
    # Replace spaces with underscores
    pdf_name_clean = pdf_name.replace(' ', '_')
    # Filter other special characters (keep alphanumeric, underscores, and hyphens)
    pdf_name_clean = "".join([c if c.isalnum() or c in ('_', '-') else '_' for c in pdf_name_clean])
    # Strip any leading/trailing underscores or whitespace
    return pdf_name_clean.strip('_').strip()

def extract_pdf_pages(pdf_path, output_dir, zoom=5.0):
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    pdf_name_clean = clean_folder_name(pdf_name)
    pdf_output_dir = os.path.join(output_dir, pdf_name_clean)
    os.makedirs(pdf_output_dir, exist_ok=True)
    
    print(f"Opening PDF: {pdf_path}")
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening {pdf_path}: {e}")
        return None
        
    num_pages = len(doc)
    print(f"Total pages to process: {num_pages}")
    
    matrix = fitz.Matrix(zoom, zoom)
    
    for page_num in range(num_pages):
        page = doc[page_num]
        print(f"  Rendering page {page_num + 1}/{num_pages}...")
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        output_filename = f"page_{page_num + 1:03d}.png"
        output_path = os.path.join(pdf_output_dir, output_filename)
        pix.save(output_path)
        print(f"    Saved: {output_path}")
        
    doc.close()
    print(f"Finished processing {pdf_name} into {pdf_output_dir}\n")
    return pdf_output_dir

def run_anylabeling_pipeline(output_dir):
    print("Initializing X-AnyLabeling Pipeline...")
    
    try:
        det_engine = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=False)
        print("PaddleOCR Detection initialized successfully.")
    except Exception as e:
        print(f"[Error] Failed to initialize PaddleOCR: {e}")
        return

    try:
        pytesseract.get_tesseract_version()
    except Exception:
        print("[Error] Tesseract OCR engine not found.")
        return

    if not os.path.exists(output_dir):
        print(f"Error: '{output_dir}' directory not found.")
        sys.exit(1)

    image_pattern = os.path.join(output_dir, "**", "*.png")
    image_paths = sorted(glob.glob(image_pattern, recursive=True))
    
    if not image_paths:
        print(f"No image pages found in the output folder: {output_dir}")
        return

    print(f"Found {len(image_paths)} images. Generating JSON files directly in their respective folders...\n")

    for idx, img_path in enumerate(image_paths):
        base_dir = os.path.dirname(img_path)
        base_filename = os.path.basename(img_path)
        
        json_filename = os.path.splitext(base_filename)[0] + ".json"
        json_path = os.path.join(base_dir, json_filename)
        
        if os.path.exists(json_path):
            print(f"[{idx+1}/{len(image_paths)}] Skipping (already processed): {img_path}")
            continue
            
        print(f"[{idx+1}/{len(image_paths)}] Processing: {img_path}")
        
        try:
            cv_img = cv2.imread(img_path)
            if cv_img is None:
                print(f"    -> [Error] Could not read image: {img_path}")
                continue
                
            h, w, _ = cv_img.shape
            
            det_result = det_engine.ocr(img_path, det=True, rec=False)
            shapes = []
            
            if det_result and det_result[0]:
                boxes = sorted(det_result[0], key=lambda b: (b[0][1], b[0][0]))
                
                for box in boxes:
                    points = [[float(pt[0]), float(pt[1])] for pt in box]
                    xs, ys = [pt[0] for pt in points], [pt[1] for pt in points]
                    xmin, xmax = int(min(xs)), int(max(xs))
                    ymin, ymax = int(min(ys)), int(max(ys))
                    
                    if xmax <= xmin or ymax <= ymin: continue
                    
                    crop_img = cv_img[ymin:ymax, xmin:xmax]
                    if crop_img.size == 0: continue
                        
                    pil_crop = Image.fromarray(cv2.cvtColor(crop_img, cv2.COLOR_BGR2RGB))
                    raw_text = pytesseract.image_to_string(pil_crop, lang='mya', config='--psm 7')
                    
                    text = raw_text.replace('\n', ' ').replace('\r', '').replace('\t', ' ').strip()
                    if not text: text = " "
                    
                    shapes.append({
                        "label": "Text",
                        "score": None,
                        "points": points,
                        "group_id": None,
                        "description": text,
                        "difficult": False,
                        "shape_type": "polygon",
                        "flags": {},
                        "attributes": {},
                        "kie_linking": []
                    })
            
            anylabeling_data = {
                "version": "3.3.10",
                "flags": {},
                "shapes": shapes,
                "imagePath": base_filename, 
                "imageData": None,
                "imageHeight": h,
                "imageWidth": w
            }
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(anylabeling_data, f, ensure_ascii=False, indent=2)
            
            print(f"    -> Success. Extracted {len(shapes)} text boxes.")
            
        except Exception as e:
            print(f"    -> Error in Processing: {e}")

    print(f"\nPipeline Completed Successfully!")

def main():
    parser = argparse.ArgumentParser(description="Combined PDF page image extraction and OCR/text annotation pipeline.")
    parser.add_argument("-m", "--mode", choices=["all", "pdf", "ocr"], default="all",
                        help="Execution mode: 'all' (both), 'pdf' (PDF rendering only), or 'ocr' (OCR processing only). Default: all")
    parser.add_argument("-r", "--raw-dir", default="raw_data", help="Directory containing the raw input PDFs (default: raw_data)")
    parser.add_argument("-o", "--output-dir", default="dataset", help="Directory to save extracted images and JSON files (default: dataset)")
    parser.add_argument("-z", "--zoom", type=float, default=5.0, help="Zoom factor for rendering PDF pages (default: 5.0)")
    
    args = parser.parse_args()
    
    # 1. Run PDF page image extraction if mode is 'all' or 'pdf'
    if args.mode in ["all", "pdf"]:
        if not os.path.exists(args.raw_dir):
            print(f"Error: '{args.raw_dir}' directory not found.")
            sys.exit(1)
            
        pdf_files = glob.glob(os.path.join(args.raw_dir, "*.pdf"))
        if not pdf_files:
            print(f"No PDF files found in '{args.raw_dir}'.")
        else:
            print(f"Found {len(pdf_files)} PDF files in '{args.raw_dir}'. Starting page extraction...")
            os.makedirs(args.output_dir, exist_ok=True)
            
            for pdf_file in pdf_files:
                extract_pdf_pages(pdf_file, args.output_dir, zoom=args.zoom)
                
    # 2. Run text/layout OCR extraction if mode is 'all' or 'ocr'
    if args.mode in ["all", "ocr"]:
        print("Starting text/layout OCR extraction...")
        run_anylabeling_pipeline(args.output_dir)

if __name__ == "__main__":
    main()
