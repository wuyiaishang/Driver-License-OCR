# Driver-License-OCR Dependncy
Tesseract, freetype, imagemagick@6, ghostscript, openCV, python3. Django

# What I achieved
- Login(authenticate)
  - Only authenticated users are able to use this service

- Upload image(jpg, png, jpeg) or pdf file(wand)
  - Use wand convert pdf to image

- Preprocess the picture(openCV, pillow)
  - Border Removal(Select image area with driver information)
  - Brightness Adjustment(BGR2HSV)
  - Smooth the picture(GaussianBlur)
  - Color Change(BGR2Gray)
  - Threshold Change(THRESH_BINARY/black and white)
  - Noise remove(erode and dilate)

- Recognize the picture(pytesseract)
  - Tesseract extract words from the processed image

- Get name and License numebr(rx)
  - Regular expression pick up the driver name and license nnumber

- Create the picture/pdf(wand, pypdf2, reportlab.pdfgen, zipfile)
  - Write driver name and number with Helvetica-Bold 14 size at correct position as Watermark
  - Merge Watermark and background pdf(create new pdf file)
  - Pdf to Image by using wand(optional)
  - Compress output files with zipfile

- Modify pages
  - bootstrap and css
