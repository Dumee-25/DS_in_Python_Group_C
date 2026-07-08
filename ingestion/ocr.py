import io

def ocr_page_text(page) -> str:
    
    import pytesseract
    from PIL import Image

    im = page.to_image(resolution=300).original
    if not isinstance(im, Image.Image):
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        buf.seek(0)
        im = Image.open(buf)
    return pytesseract.image_to_string(im)