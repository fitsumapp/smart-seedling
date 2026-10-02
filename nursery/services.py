"""QR Code generation and plant traceability utilities with High-DPI crystal-clear labels."""

import io
import os
import qrcode
from PIL import Image, ImageDraw, ImageFont
from django.core.files.base import ContentFile
from django.urls import reverse
from django.conf import settings


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Safely loads modern system TrueType fonts across Windows and Linux."""
    font_candidates = []
    if bold:
        font_candidates = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "segoeuib.ttf",
            "arialbd.ttf",
        ]
    else:
        font_candidates = [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "segoeui.ttf",
            "arial.ttf",
        ]

    for candidate in font_candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except (IOError, OSError):
            continue

    # Fallback to default Pillow font if no TrueType is found
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def generate_qr_code_image(url: str, box_size: int = 12, border: int = 2) -> bytes:
    """Generates a high-quality PNG QR code byte stream."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    # Generate image with dark forest green & white branding
    img = qr.make_image(fill_color="#072b15", back_color="#ffffff")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG', dpi=(300, 300))
    return buffer.getvalue()


def generate_printable_label(batch, base_url: str) -> bytes:
    """
    Generates a High-DPI, ultra-sharp printable plant pot label (1200x700 px @ 300 DPI)
    with crisp typography, dynamic badge sizing, and high-resolution QR code.
    """
    label_w, label_h = 1200, 700
    label_img = Image.new('RGB', (label_w, label_h), color='#ffffff')
    draw = ImageDraw.Draw(label_img)

    # Fonts
    font_header_title = get_font(34, bold=True)
    font_header_sub = get_font(18, bold=False)
    font_plant_name = get_font(42, bold=True)
    font_variety = get_font(24, bold=False)
    font_label_key = get_font(20, bold=True)
    font_label_val = get_font(22, bold=False)
    font_pill_bold = get_font(20, bold=True)
    font_scan_cta = get_font(21, bold=True)
    font_footer = get_font(16, bold=False)

    # 1. Outer Border & Background
    draw.rounded_rectangle([12, 12, label_w - 13, label_h - 13], radius=24, outline='#0c3b20', width=5)

    # 2. Header Banner
    draw.rounded_rectangle([14, 14, label_w - 15, 115], radius=20, fill='#072b15')
    # Flatten bottom corners of header
    draw.rectangle([14, 90, label_w - 15, 115], fill='#072b15')

    draw.text((45, 30), "SMART SEEDLING NURSERY", font=font_header_title, fill='#ffffff')
    facility_name = f"Certified Precision Agriculture • {batch.nursery.name if batch.nursery else 'Smart Nursery'}"
    draw.text((48, 78), facility_name[:55], font=font_header_sub, fill='#a3e635')

    # 3. Left Section: Plant Information Card
    # Plant Common Name
    draw.text((50, 145), batch.plant_name.upper(), font=font_plant_name, fill='#072b15')
    
    # Variety / Species
    species_text = f"Variety: {batch.variety or 'Standard'}"
    if batch.species:
        species_text += f" ({batch.species})"
    draw.text((52, 202), species_text[:50], font=font_variety, fill='#4b5563')

    # Divider line
    draw.line([(50, 245), (660, 245)], fill='#e5e7eb', width=2)

    # Metadata Grid Boxes
    meta_items = [
        ("BATCH CODE", batch.batch_code),
        ("PLANTED ON", batch.planting_date.strftime('%B %d, %Y')),
        ("NURSERY ZONE", batch.nursery_zone.name if batch.nursery_zone else "Primary Facility"),
        ("SEEDLING AGE", f"{batch.age_days} Days Old"),
    ]

    y_pos = 265
    for key, val in meta_items:
        draw.text((52, y_pos), key, font=font_label_key, fill='#072b15')
        draw.text((230, y_pos), str(val)[:32], font=font_label_val, fill='#1f2937')
        y_pos += 48

    # Dynamic Stage / Status Badge Pill
    status_name = (batch.get_status_display() if hasattr(batch, 'get_status_display') else str(batch.status)).upper()
    status_text = f"STATUS: {status_name}"
    
    # Calculate exact text width for perfect pill padding
    bbox = draw.textbbox((0, 0), status_text, font=font_pill_bold)
    text_w = bbox[2] - bbox[0]
    pill_w = text_w + 40
    draw.rounded_rectangle([52, 475, 52 + pill_w, 525], radius=14, fill='#dcfce7', outline='#16a34a', width=2)
    draw.text((72, 488), status_text, font=font_pill_bold, fill='#15803d')

    # 4. Right Section: QR Code Card & Frame
    qr_card_x1 = 700
    qr_card_y1 = 145
    qr_card_w = 445
    qr_card_h = 505

    # White QR Card Container with soft border
    draw.rounded_rectangle(
        [qr_card_x1, qr_card_y1, qr_card_x1 + qr_card_w, qr_card_y1 + qr_card_h],
        radius=20,
        fill='#f8faf8',
        outline='#cbd5e1',
        width=2
    )

    # High-Res QR Code
    qr_url = f"{base_url.rstrip('/')}{reverse('nursery:public-plant-detail', kwargs={'qr_token': batch.qr_token})}"
    qr_bytes = generate_qr_code_image(qr_url, box_size=10, border=1)
    qr_pil = Image.open(io.BytesIO(qr_bytes))
    
    # Resize with high-quality LANCZOS resampling to 350x350 px
    qr_pil_resized = qr_pil.resize((350, 350), Image.Resampling.LANCZOS)
    label_img.paste(qr_pil_resized, (qr_card_x1 + 47, qr_card_y1 + 35))

    # Scan CTA Banner below QR
    cta_y1 = qr_card_y1 + 405
    draw.rounded_rectangle(
        [qr_card_x1 + 25, cta_y1, qr_card_x1 + qr_card_w - 25, cta_y1 + 60],
        radius=14,
        fill='#072b15'
    )
    cta_text = "SCAN FOR CARE PASSPORT"
    cta_bbox = draw.textbbox((0, 0), cta_text, font=font_scan_cta)
    cta_text_w = cta_bbox[2] - cta_bbox[0]
    cta_text_x = qr_card_x1 + 25 + ((qr_card_w - 50) - cta_text_w) // 2
    draw.text((cta_text_x, cta_y1 + 17), cta_text, font=font_scan_cta, fill='#ffffff')

    # 5. Bottom Security & Traceability Stamp
    token_preview = f"Digital Passport Token: {batch.qr_token[:16]}... • Real-Time Environmental IoT Monitoring"
    draw.text((50, 648), token_preview, font=font_footer, fill='#6b7280')

    # Output High-Resolution PNG byte stream
    buffer = io.BytesIO()
    label_img.save(buffer, format='PNG', dpi=(300, 300), optimize=True)
    return buffer.getvalue()
