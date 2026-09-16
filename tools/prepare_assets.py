"""Split the generated atlas; preserve the original RGBA pixels."""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sheet = Image.open(ROOT / "assets" / "sprite-sheet.png").convert("RGBA")
# Atlas divider observed during visual QA (the generated sheet is 1278x1230).
cells = {"idle": (0, 0, 640, 640), "happy": (640, 0, 1278, 640),
         "sleep": (0, 640, 640, 1230), "walk": (640, 640, 1278, 1230)}
for name, box in cells.items():
    cell = sheet.crop(box)
    bbox = cell.getchannel("A").point(lambda a: 255 if a > 80 else 0).getbbox()
    sprite = cell.crop(bbox)
    sprite.thumbnail((608, 608), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (640, 640))
    canvas.paste(sprite, ((640 - sprite.width) // 2, 622 - sprite.height))
    canvas.save(ROOT / "assets" / f"{name}.png")
Image.open(ROOT / "assets" / "idle.png").save(
    ROOT / "assets" / "pet.ico", sizes=[(32, 32), (48, 48), (128, 128), (256, 256)])
