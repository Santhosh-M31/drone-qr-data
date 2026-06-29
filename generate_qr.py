import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

PAGES_BASE = "https://santhosh-m31.github.io/drone-qr-data/"
RAW_BASE   = "https://raw.githubusercontent.com/Santhosh-M31/drone-qr-data/master/"
LOGO_PATH  = "logo.jpg"
LOGO_URL   = "https://santhosh-m31.github.io/drone-qr-data/logo.jpg"

files = [
    "Product_Delivery_01.csv",
    "Product_Delivery_02.csv",
    "Product_Delivery_03.csv",
    "Product_Delivery_04.csv",
    "Input_Lidar_01.csv",
    "Input_Lidar_02.csv",
    "Input_Multispectral_01.csv",
    "Input_Multispectral_02.csv",
]

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{LABEL}</title>
</head>
<body>
  <script>
    (async function() {{
      const rawUrl = '{RAW_URL}';
      const redirectUrl = 'https://www.tecsolutiongroup.com/';
      const d = new Date();
      const ts = d.getFullYear() + String(d.getMonth()+1).padStart(2,'0') + String(d.getDate()).padStart(2,'0') + '_' + String(d.getHours()).padStart(2,'0') + String(d.getMinutes()).padStart(2,'0') + String(d.getSeconds()).padStart(2,'0');
      const filename = '{BASENAME}_' + ts + '.csv';
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
        setTimeout(() => URL.revokeObjectURL(blobUrl), 3000);
      }} catch (e) {{
        const a = document.createElement('a');
        a.href = rawUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }}
      setTimeout(() => {{ window.location.href = redirectUrl; }}, 1500);
    }})();
  </script>
</body>
</html>
"""

os.makedirs("download", exist_ok=True)
os.makedirs("qrcodes", exist_ok=True)

# Load and prepare logo for QR images
logo = Image.open(LOGO_PATH).convert("RGB")

for filename in files:
    label = filename.replace(".csv", "").replace("_", " ")
    raw_url  = RAW_BASE + filename
    page_url = PAGES_BASE + "download/" + filename.replace(".csv", ".html")

    # --- HTML download page ---
    html = HTML_TEMPLATE.format(
        LABEL=label, RAW_URL=raw_url, FILENAME=filename,
        BASENAME=filename.replace('.csv', ''), LOGO_URL=LOGO_URL
    )
    html_path = os.path.join("download", filename.replace(".csv", ".html"))
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML: {html_path}")

    # --- QR code image ---
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

    # Resize logo to QR width with padding, keep aspect ratio
    logo_padding = 20
    logo_target_w = qr_w - logo_padding * 2
    logo_ratio = logo_target_w / logo.width
    logo_h = int(logo.height * logo_ratio)
    logo_resized = logo.resize((logo_target_w, logo_h), Image.LANCZOS)

    label_height = 55
    total_h = logo_h + 12 + qr_h + label_height

    final_img = Image.new("RGB", (qr_w, total_h), "white")
    # Paste logo centered at top
    final_img.paste(logo_resized, (logo_padding, 8))
    # Paste QR below logo
    final_img.paste(qr_img, (0, logo_h + 12))

    draw = ImageDraw.Draw(final_img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 22)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), label, font=font)
    text_w = bbox[2] - bbox[0]
    x = (qr_w - text_w) // 2
    draw.text((x, logo_h + 12 + qr_h + 14), label, fill="black", font=font)

    out_path = os.path.join("qrcodes", filename.replace(".csv", "_QR.png"))
    final_img.save(out_path)
    print(f"QR:   {out_path}  ->  {page_url}\n")

print("Done! All 8 HTML pages and QR codes regenerated with logo.")
