# -*- coding: utf-8 -*-
"""يولّد أيقونة التطبيق وشعار شاشة البداية من هوية التصميم (بلا أصول خارجية).

    python design/make_icon.py

المخرجات:
- design/app-icon-1024.png (للتوثيق ومتجر Play)
- app/android/app/src/main/res/mipmap-*/ic_launcher.png (48..192)
- app/android/app/src/main/res/drawable-nodpi/launch_logo.png (شعار أبيض شفاف)

الرسم: قبعة تخرّج بيضاء على تدرّج أزرق من `#2E74B5` إلى `#173D5E`، وشرّابة ذهبية
`#E0B45C` — نفس ألوان `app_theme.dart` والتصميم.
"""
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "app" / "android" / "app" / "src" / "main" / "res"
DESIGN = ROOT / "design"

BLUE_TOP = (46, 116, 181)      # #2E74B5
BLUE_BOTTOM = (23, 61, 94)     # #173D5E
GOLD = (224, 180, 92)          # #E0B45C
WHITE = (255, 255, 255)

SIZE = 1024
SS = 2  # supersampling


def _gradient(size: int) -> Image.Image:
    image = Image.new("RGB", (1, size))
    for y in range(size):
        ratio = y / max(size - 1, 1)
        color = tuple(
            round(BLUE_TOP[i] + (BLUE_BOTTOM[i] - BLUE_TOP[i]) * ratio) for i in range(3)
        )
        image.putpixel((0, y), color)
    return image.resize((size, size))


def _draw_cap(draw: ImageDraw.ImageDraw, scale: float, offset: tuple[int, int]) -> None:
    ox, oy = offset

    def p(x: float, y: float) -> tuple[float, float]:
        return (ox + x * scale, oy + y * scale)

    # قاعدة القبعة (رأس متوازي أضلاع مستدير الزوايا)
    draw.rounded_rectangle(
        [p(392, 470), p(632, 640)],
        radius=38 * scale,
        fill=WHITE,
    )
    # السطح المائل (معيّن)
    draw.polygon(
        [p(512, 300), p(806, 424), p(512, 548), p(218, 424)],
        fill=WHITE,
    )
    # خط فاصل رقيق بلون الخلفية يعطي عمقاً للقبعة
    draw.line([p(392, 470), p(632, 470)], fill=BLUE_TOP, width=max(int(8 * scale), 1))
    # الشرّابة
    draw.line([p(806, 430), p(806, 650)], fill=GOLD, width=max(int(16 * scale), 2))
    draw.ellipse(
        [p(778, 650), p(834, 706)],
        fill=GOLD,
    )


def app_icon(size: int = SIZE) -> Image.Image:
    canvas = _gradient(size * SS)
    draw = ImageDraw.Draw(canvas)
    _draw_cap(draw, size * SS / 1024, (0, 0))
    return canvas.resize((size, size), Image.LANCZOS)


def launch_logo(size: int = 512) -> Image.Image:
    canvas = Image.new("RGBA", (size * SS, size * SS), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    _draw_cap(draw, size * SS / 1024, (0, 0))
    return canvas.resize((size, size), Image.LANCZOS)


def main() -> None:
    icon = app_icon()
    icon.save(DESIGN / "app-icon-1024.png")

    densities = {
        "mdpi": 48,
        "hdpi": 72,
        "xhdpi": 96,
        "xxhdpi": 144,
        "xxxhdpi": 192,
    }
    for folder, px in densities.items():
        target = RES / f"mipmap-{folder}" / "ic_launcher.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        icon.resize((px, px), Image.LANCZOS).save(target)

    logo_dir = RES / "drawable-nodpi"
    logo_dir.mkdir(parents=True, exist_ok=True)
    launch_logo().save(logo_dir / "launch_logo.png")
    print("icons written")


if __name__ == "__main__":
    main()
