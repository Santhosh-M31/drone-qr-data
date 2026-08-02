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
  <meta http-equiv="Cache-Control" content="no-store, no-cache, must-revalidate, max-age=0">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>{LABEL}</title>
  <style>
    * {{ box-sizing: border-box; }}
    html, body {{ height: 100%; margin: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      background: #f5f7fa;
      color: #1f2937;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 24px;
    }}
    .card {{
      background: #ffffff;
      border-radius: 16px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.08);
      padding: 32px 28px;
      max-width: 420px;
      width: 100%;
      text-align: center;
    }}
    .logo {{
      max-width: 180px;
      height: auto;
      margin-bottom: 20px;
    }}
    .msg {{
      font-size: 18px;
      font-weight: 600;
      margin: 12px 0 8px;
    }}
    .fname {{
      font-size: 20px;
      font-weight: 700;
      color: #0f62fe;
      margin-bottom: 22px;
      letter-spacing: 0.2px;
    }}
    .redirect {{
      font-size: 15px;
      color: #4b5563;
      margin-top: 12px;
    }}
    .count {{
      display: inline-block;
      min-width: 28px;
      font-weight: 700;
      color: #0f62fe;
      font-size: 20px;
    }}
    .manual {{
      display: block;
      margin-top: 18px;
      font-size: 13px;
      color: #6b7280;
      text-decoration: none;
    }}
    .manual a {{ color: #0f62fe; text-decoration: none; }}
  </style>
</head>
<body>
  <div class="card">
    <img class="logo" src="{LOGO_URL}" alt="Tec Solution Group">
    <div class="msg">You have downloaded</div>
    <div class="fname">{LABEL}</div>
    <div class="redirect">
      Redirecting to company website in <span class="count" id="count">5</span>
    </div>
    <div class="manual">
      Not redirecting? <a id="manualLink" href="https://www.tecsolutiongroup.com/">Click here</a>
    </div>
  </div>

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

      let n = 5;
      const countEl = document.getElementById('count');
      const timer = setInterval(() => {{
        n -= 1;
        if (n <= 0) {{
          clearInterval(timer);
          window.location.href = redirectUrl;
        }} else {{
          countEl.textContent = n;
        }}
      }}, 1000);
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
