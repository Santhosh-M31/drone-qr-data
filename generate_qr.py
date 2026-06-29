import qrcode
from PIL import Image, ImageDraw, ImageFont
import os

BASE_URL = "https://github.com/Santhosh-M31/drone-qr-data/raw/master/"

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

os.makedirs("qrcodes", exist_ok=True)

for filename in files:
    url = BASE_URL + filename
    label = filename.replace(".csv", "").replace("_", " ")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Add label below QR code
    qr_w, qr_h = qr_img.size
    label_height = 50
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
    y = qr_h + 10
    draw.text((x, y), label, fill="black", font=font)

    out_path = os.path.join("qrcodes", filename.replace(".csv", "_QR.png"))
    final_img.save(out_path)
    print(f"Saved: {out_path}  ->  {url}")

print("\nAll 8 QR codes generated in: qrcodes/")
