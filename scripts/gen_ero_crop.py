import sys
sys.stdout.reconfigure(encoding='utf-8')

from PIL import Image
import os

BASE = r'C:\Users\riseo\Cluade Test\stock-charts'
TEMP_DIR = os.path.join(BASE, 'images', 'temp_ero')
IMG_DIR = os.path.join(BASE, 'images')

# Crop specifications: (left, top, right, bottom)
CROPS = [
    {
        'src': 'erocopper_1_full.png',
        'dst': 'erocopper_1.png',
        'crop': (0, 100, 1280, 1050),  # Caraiba: hero + overview section with aerial facility photo + description text
        'desc': 'Caraiba Operations - copper mining complex overview with aerial facility photo'
    },
    {
        'src': 'erocopper_2_full.png',
        'dst': 'erocopper_2.png',
        'crop': (0, 100, 1280, 850),  # Tucuma: hero + aerial mine photo + overview text
        'desc': 'Tucuma Operation - open pit copper mine aerial view'
    },
    {
        'src': 'erocopper_3_full.png',
        'dst': 'erocopper_3.png',
        'crop': (0, 100, 1280, 1100),  # Xavantina: hero + overview with mining photos + text
        'desc': 'Xavantina Operations - gold mine overview with facility photos and details'
    },
    {
        'src': 'erocopper_4_full.png',
        'dst': 'erocopper_4.png',
        'crop': (0, 100, 1280, 1050),  # Furnas: hero + overview with workers photo + description text
        'desc': 'Furnas Copper-Gold Project - development project overview with team photo'
    },
    {
        'src': 'erocopper_5_full.png',
        'dst': 'erocopper_5.png',
        'crop': (0, 40, 1280, 700),  # What We Do: hero + Brazil operations map
        'desc': 'What We Do Overview - Brazil operations map showing all mining locations'
    },
]

for item in CROPS:
    src_path = os.path.join(TEMP_DIR, item['src'])
    dst_path = os.path.join(IMG_DIR, item['dst'])

    img = Image.open(src_path)
    w, h = img.size
    print(f"\n{item['src']}: {w}x{h}")

    crop_box = item['crop']
    # Clamp to image bounds
    crop_box = (
        max(0, crop_box[0]),
        max(0, crop_box[1]),
        min(w, crop_box[2]),
        min(h, crop_box[3])
    )

    cropped = img.crop(crop_box)
    cropped.save(dst_path)
    fsize = os.path.getsize(dst_path)
    cw, ch = cropped.size
    print(f"  Cropped to {cw}x{ch} -> {dst_path}")
    print(f"  File size: {fsize:,} bytes")
    print(f"  Content: {item['desc']}")

print("\n\nAll images cropped and saved.")

# Summary
print("\nFile size summary:")
for item in CROPS:
    dst_path = os.path.join(IMG_DIR, item['dst'])
    fsize = os.path.getsize(dst_path)
    print(f"  {item['dst']}: {fsize:,} bytes")
