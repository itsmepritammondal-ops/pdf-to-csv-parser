import re
from pathlib import Path

import pdfplumber
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
PDF_FOLDER = BASE_DIR / "pdfs"
OUTPUT = BASE_DIR / "graphics-cards.csv"


FIELDS = [
    "Brand",
    "Product",
    "Chipset",
    "Core Clock",
    "RTX-OPS",
    "CUDA Cores",
    "Memory Clock",
    "Memory Size",
    "Memory Type",
    "Memory Bus",
    "Memory Bandwidth (GB/sec)",
    "Card Bus",
    "Digital max resolution",
    "Multi-view",
    "Card size",
    "PCB Form",
    "DirectX",
    "OpenGL",
    "Power requirement",
    "Power Connectors",
    "Output",
    "SLI support",
    "Accessories",
]


def clean(value):
    if value is None:
        return ""

    text = str(value).replace("\n", " ").strip()

    text = re.sub(
        r"::selection\s*\{.*?\}",
        "",
        text,
        flags=re.I,
    )

    text = re.sub(
        r"#model-header\s*>\s*ul\s*>\s*li\.active\s*>\s*a\s*\{.*?\}",
        "",
        text,
        flags=re.I,
    )

    return re.sub(r"\s+", " ", text).strip()


def parse_pdf(pdf_path):
    products = []

    with pdfplumber.open(pdf_path) as pdf:

        for page in pdf.pages:

            tables = page.extract_tables()

            for table in tables:

                if not table:
                    continue

                first_row = table[0]

                if not first_row:
                    continue

                headers = [clean(x) for x in first_row[1:]]

                if not headers:
                    continue

                page_products = [
                    {field: "" for field in FIELDS}
                    for _ in headers
                ]

                for i, product_name in enumerate(headers):
                    page_products[i]["Brand"] = "GIGABYTE"
                    page_products[i]["Product"] = product_name

                for row in table[1:]:

                    if not row or not row[0]:
                        continue

                    spec = clean(row[0])

                    if spec not in FIELDS:
                        continue

                    for i, value in enumerate(row[1:]):

                        if i < len(page_products):
                            page_products[i][spec] = clean(value)

                products.extend(page_products)

    return products


def main():

    if not PDF_FOLDER.exists():
        PDF_FOLDER.mkdir(parents=True, exist_ok=True)

        print(f"Created folder: {PDF_FOLDER}")
        print("Put your PDF files inside the 'pdfs' folder.")
        print("Then run the script again.")
        return

    pdf_files = sorted(PDF_FOLDER.glob("*.pdf"))

    if not pdf_files:
        print(f"No PDF files found in: {PDF_FOLDER}")
        return

    all_products = []

    for pdf_path in pdf_files:

        print(f"Processing: {pdf_path.name}")

        try:
            products = parse_pdf(pdf_path)

            print(f"  Found {len(products)} products.")

            all_products.extend(products)

        except Exception as e:
            print(f"ERROR in {pdf_path.name}: {e}")

    df = pd.DataFrame(all_products, columns=FIELDS)

    df.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    print()
    print(df)
    print()
    print(f"Saved: {OUTPUT}")
    print(f"Total products: {len(df)}")


if __name__ == "__main__":
    main()