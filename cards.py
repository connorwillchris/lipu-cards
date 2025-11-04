import json
import os
from PIL import Image, ImageDraw, ImageFont

# --- CONFIG ---
DPI = 300  # high-quality print
CARDS_PER_ROW = 4
CARDS_PER_COL = 4
PAGE_WIDTH_IN = 8.5
PAGE_HEIGHT_IN = 11
CARD_WIDTH_IN = PAGE_WIDTH_IN / CARDS_PER_ROW
CARD_HEIGHT_IN = PAGE_HEIGHT_IN / CARDS_PER_COL



CARD_W = int(CARD_WIDTH_IN * DPI)
CARD_H = int(CARD_HEIGHT_IN * DPI)
PAGE_W = int(PAGE_WIDTH_IN * DPI)
PAGE_H = int(PAGE_HEIGHT_IN * DPI)

FONT_PATH = None  # Use default PIL font if none is specified
OUTPUT_FILE = "kalama_ike_cards.pdf"

# --- LOAD JSON DATA ---
def load_cards(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

# --- UTILITY: measure text ---
def measure_text(draw, text, font):
    """Return (width, height) of text, compatible with Pillow >=10."""
    if hasattr(draw, "textbbox"):
        bbox = draw.textbbox((0, 0), text, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        return w, h
    else:
        # fallback for older Pillow versions
        return draw.textsize(text, font=font)

# --- CREATE A SINGLE CARD IMAGE ---
def create_card(text, color="white"):
    if color == "black":
        bg = (0, 0, 0)
        fg = (255, 255, 255)
    else:
        bg = (255, 255, 255)
        fg = (0, 0, 0)

    img = Image.new("RGB", (CARD_W, CARD_H), bg)
    draw = ImageDraw.Draw(img)

    # Try loading font
    try:
        font = ImageFont.truetype(FONT_PATH or "arial.ttf", 72)
    except:
        font = ImageFont.load_default()

    # Wrap text manually
    max_width = CARD_W - 80
    lines = []
    words = text.split()
    line = ""
    for word in words:
        test_line = line + (" " if line else "") + word
        w, _ = measure_text(draw, test_line, font)
        if w <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)

    # Center text vertically
    total_text_height = sum(measure_text(draw, l, font)[1] for l in lines)
    y = (CARD_H - total_text_height) // 2

    for l in lines:
        w, h = measure_text(draw, l, font)
        x = (CARD_W - w) // 2
        draw.text((x, y), l, font=font, fill=fg)
        y += h + 10

    # Draw border
    draw.rectangle([5, 5, CARD_W - 5, CARD_H - 5], outline=(128, 128, 128), width=4)

    return img

# --- ARRANGE CARDS ON PDF PAGES ---
def arrange_to_pdf(cards, output_file):
    pages = []
    page = Image.new("RGB", (PAGE_W, PAGE_H), (255, 255, 255))

    x = y = 0
    card_count = 0

    for card_img in cards:
        page.paste(card_img, (x, y))
        card_count += 1

        x += CARD_W
        if card_count % CARDS_PER_ROW == 0:
            x = 0
            y += CARD_H

        if card_count % (CARDS_PER_ROW * CARDS_PER_COL) == 0:
            pages.append(page)
            page = Image.new("RGB", (PAGE_W, PAGE_H), (255, 255, 255))
            x = y = 0

    if card_count % (CARDS_PER_ROW * CARDS_PER_COL) != 0:
        pages.append(page)

    # Save all pages as one PDF
    pages[0].save(output_file, "PDF", resolution=DPI, save_all=True, append_images=pages[1:])
    print(f"✅ PDF created: {output_file}")

# --- MAIN ---
def main(json_path):
    data = load_cards(json_path)
    cards = []

    # Create black cards
    for text in data.get("black", []):
        cards.append(create_card(text, "black"))

    # Create white cards
    for text in data.get("white", []):
        cards.append(create_card(text, "white"))

    arrange_to_pdf(cards, OUTPUT_FILE)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate Toki Pona CAH-style cards using PIL")
    parser.add_argument("--json", required=True, help="Path to JSON file with 'black' and 'white' keys")
    args = parser.parse_args()
    main(args.json)
