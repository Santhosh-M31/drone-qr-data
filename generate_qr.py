import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

PAGES_BASE = "https://santhosh-m31.github.io/drone-qr-data/"
RAW_BASE = "https://raw.githubusercontent.com/Santhosh-M31/drone-qr-data/master/"

files = [
    "Product_Delivery_01.csv",
    "Product_Delivery_02.csv",
    "Product_Delivery_03.csv",
    "Product_Delivery_04.csv",
    "Input_L3_01.csv",
    "Input_L3_02.csv",
    "Input_Multispectral_01.csv",
    "Input_Multispectral_02.csv",
]

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Download {LABEL}</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:Arial,sans-serif;background:#f0f4f8;display:flex;align-items:center;justify-content:center;min-height:100vh}}
    .card{{background:#fff;border-radius:16px;padding:40px 32px;text-align:center;box-shadow:0 6px 24px rgba(0,0,0,.12);max-width:420px;width:92%}}
    h1{{font-size:1.3em;color:#1a1a2e;margin-bottom:10px}}
    p{{color:#555;font-size:.95em;margin-bottom:24px}}
    .btn{{display:inline-block;background:#1976d2;color:#fff;padding:14px 32px;border-radius:10px;text-decoration:none;font-size:1.05em;font-weight:bold;cursor:pointer;transition:background .2s}}
    .btn:hover{{background:#1565c0}}
    .status{{margin-top:18px;color:#888;font-size:.88em}}
    .icon{{font-size:2.5em;margin-bottom:16px}}
  </style>
</head>
<body>
  <div class="card">
    <div class="icon">📊</div>
    <h1>{LABEL}</h1>
    <p>Your CSV file will download automatically.<br>Tap the button if it doesn't start.</p>
    <a id="dlbtn" class="btn" href="{RAW_URL}" download="{FILENAME}">&#8675; Download CSV</a>
    <p class="status" id="status">Starting download...</p>
  </div>
  <script>
    (async function() {{
      const rawUrl = '{RAW_URL}';
      const filename = '{FILENAME}';
      const status = document.getElementById('status');
      try {{
        const res = await fetch(rawUrl);
        const blob = await res.blob();
        const blobUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(() => URL.revokeObjectURL(blobUrl), 2000);
        status.textContent = 'Download started!';
      }} catch (e) {{
        status.textContent = 'Tap the button above to download.';
      }}
    }})();
  </script>
</body>
</html>
"""

os.makedirs("download", exist_ok=True)
os.makedirs("qrcodes", exist_ok=True)

for filename in files:
    label = filename.replace(".csv", "").replace("_", " ")
    raw_url = RAW_BASE + filename
    page_url = PAGES_BASE + "download/" + filename.replace(".csv", ".html")

    # Write HTML download page
    html = HTML_TEMPLATE.format(LABEL=label, RAW_URL=raw_url, FILENAME=filename)
    html_path = os.path.join("download", filename.replace(".csv", ".html"))
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML page: {html_path}")

    # Generate QR code pointing to GitHub Pages URL
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(page_url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    qr_w, qr_h = qr_img.size
    label_height = 55
    final_img = Image.new("RGB", (qr_w, qr_h + label_height), "white")
    final_img.paste(qr_img, (0, 0))

    draw = ImageDraw.Draw(final_img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    x = (qr_w - text_w) // 2
    draw.text((x, qr_h + 14), label, fill="black", font=font)

    out_path = os.path.join("qrcodes", filename.replace(".csv", "_QR.png"))
    final_img.save(out_path)
    print(f"QR saved:  {out_path}  ->  {page_url}\n")

print("Done! All 8 HTML pages and QR codes generated.")
