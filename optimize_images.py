from PIL import Image
import os
from pathlib import Path

# مسیر پوشه تصاویر
image_paths = [
    Path("pms_app/static/img/hero"),
    Path(".")  # برای eagle.png در ریشه
]

max_width = 1920  # حداکثر عرض تصویر
quality = 82      # کیفیت خروجی (0-100)

def optimize_image(filepath):
    try:
        with Image.open(filepath) as img:
            # تبدیل به RGB برای فرمت JPEG
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # تغییر اندازه فقط اگر بزرگتر از max_width باشد
            if img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.LANCZOS)

            # ذخیره فشرده‌شده
            output_path = filepath.with_suffix(".jpg")  # همه را jpg می‌کنیم
            img.save(output_path, "JPEG", quality=quality, optimize=True)
            print(f"✅ Optimized: {filepath} -> {output_path} ({os.path.getsize(output_path)//1024} KB)")
    except Exception as e:
        print(f"❌ Error: {filepath}: {e}")

# پوشه hero
hero_dir = Path("pms_app/static/img/hero")
for img_file in hero_dir.glob("*.*"):
    if img_file.suffix.lower() in (".jpg", ".jpeg", ".png"):
        optimize_image(img_file)

# فایل eagle.png در ریشه
eagle = Path("eagle.png")
if eagle.exists():
    optimize_image(eagle)