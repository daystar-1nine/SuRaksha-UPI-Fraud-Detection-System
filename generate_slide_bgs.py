import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

W_PX, H_PX = 1920, 1080  # 16:9 1080p
assets_dir = r"S:\Hackathon\SuRaksha\assets\screenshots"
bg_dir = r"S:\Hackathon\SuRaksha\assets\slide_backgrounds"
os.makedirs(bg_dir, exist_ok=True)

def create_base_canvas(theme="blue"):
    img = Image.new("RGBA", (W_PX, H_PX), (7, 10, 19, 255)) # #070a13
    draw = ImageDraw.Draw(img)
    
    # Subtle cyber grid
    grid_color = (15, 23, 42, 100)
    for x in range(0, W_PX, 80):
        draw.line([(x, 0), (x, H_PX)], fill=(15, 23, 42, 60), width=1)
    for y in range(0, H_PX, 80):
        draw.line([(0, y), (W_PX, y)], fill=(15, 23, 42, 60), width=1)

    # Glow Orbs
    glow = Image.new("RGBA", (W_PX, H_PX), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    if theme == "hero":
        glow_draw.ellipse([W_PX - 600, -200, W_PX + 400, 800], fill=(30, 58, 138, 70))
        glow_draw.ellipse([100, H_PX - 400, 700, H_PX + 200], fill=(16, 185, 129, 40))
        glow_draw.ellipse([W_PX // 2 - 300, H_PX // 2 - 300, W_PX // 2 + 300, H_PX // 2 + 300], fill=(56, 189, 248, 30))
    elif theme == "red":
        glow_draw.ellipse([W_PX - 500, -100, W_PX + 300, 700], fill=(239, 68, 68, 50))
        glow_draw.ellipse([-100, H_PX - 400, 500, H_PX + 200], fill=(245, 158, 11, 40))
    elif theme == "green":
        glow_draw.ellipse([W_PX - 500, -100, W_PX + 300, 700], fill=(16, 185, 129, 60))
        glow_draw.ellipse([-100, -100, 600, 600], fill=(56, 189, 248, 40))
    elif theme == "vision":
        glow_draw.ellipse([W_PX // 2 - 600, H_PX // 2 - 600, W_PX // 2 + 600, H_PX // 2 + 600], fill=(30, 58, 138, 80))
        glow_draw.ellipse([W_PX // 2 - 300, H_PX // 2 - 300, W_PX // 2 + 300, H_PX // 2 + 300], fill=(56, 189, 248, 50))
    else:
        glow_draw.ellipse([W_PX - 400, -100, W_PX + 300, 600], fill=(59, 130, 246, 50))
        glow_draw.ellipse([-100, H_PX - 300, 500, H_PX + 300], fill=(15, 23, 42, 100))

    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img = Image.alpha_composite(img, glow)
    
    # Corner HUD tech accents
    draw_final = ImageDraw.Draw(img)
    corner_color = (56, 189, 248, 180)
    # Top Left
    draw_final.line([(40, 40), (80, 40)], fill=corner_color, width=2)
    draw_final.line([(40, 40), (40, 80)], fill=corner_color, width=2)
    # Top Right
    draw_final.line([(W_PX - 40, 40), (W_PX - 80, 40)], fill=corner_color, width=2)
    draw_final.line([(W_PX - 40, 40), (W_PX - 40, 80)], fill=corner_color, width=2)
    # Bottom Left
    draw_final.line([(40, H_PX - 40), (80, H_PX - 40)], fill=corner_color, width=2)
    draw_final.line([(40, H_PX - 40), (40, H_PX - 80)], fill=corner_color, width=2)
    # Bottom Right
    draw_final.line([(W_PX - 40, H_PX - 40), (W_PX - 80, H_PX - 40)], fill=corner_color, width=2)
    draw_final.line([(W_PX - 40, H_PX - 40), (W_PX - 40, H_PX - 80)], fill=corner_color, width=2)
    
    return img

print("Generating custom background artwork...")
themes = {
    "slide1": "hero",
    "slide2": "red",
    "slide3": "blue",
    "slide4": "blue",
    "slide5": "green",
    "slide6": "blue",
    "slide7": "blue",
    "slide8": "green",
    "slide9": "vision"
}
bg_paths = {}
for name, th in themes.items():
    bg_img = create_base_canvas(th)
    out_file = os.path.join(bg_dir, f"{name}_bg.png")
    bg_img.save(out_file)
    bg_paths[name] = out_file
    print(f"Generated {out_file}")

print("All background artwork created successfully!")
