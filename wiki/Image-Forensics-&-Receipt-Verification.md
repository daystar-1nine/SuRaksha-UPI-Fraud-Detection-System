# Image Forensics & Receipt Verification 📷

One of the most common UPI scams involves buyers presenting merchants with fake, doctored screenshots of successful transactions. SuRaksha implements a zero-disk, in-memory image analysis pipeline to inspect visual authenticity and check for digital manipulation.

---

## 💾 Zero-Disk In-Memory Processing

To protect the server from security exploits (such as shell uploads, malicious metadata executions, or directory traversal attacks), SuRaksha processes uploaded images **entirely in RAM** and sanitizes them immediately:

1. **Upload stream**: Flask receives the image file stream into memory (`io.BytesIO`).
2. **EXIF Stripping**: The raw pixel canvas is reconstructed using Python's `PIL.Image`. This process strips out all header tags (including geolocation, software names, and EXIF metadata) and saves the raw canvas as clean JPEG bytes.
3. **No temp files**: The image never hits the server's hard drive, preventing temp directory pollution and local file inclusion exploits.

---

## 🔍 Error Level Analysis (ELA)

When a JPEG image is saved, the entire canvas is compressed uniformly in 8x8 pixel blocks. If an image is modified (e.g. altering the payment amount text), the modified region will contain different compression grids compared to the rest of the original canvas.

SuRaksha detects these variations using **Error Level Analysis (ELA)**:

```
┌─────────────────┐       Save at 75% Quality       ┌──────────────────┐
│  Original Image  ├───────────────────────────────►│ Re-compressed Img│
└────────┬────────┘                                 └────────┬─────────┘
         │                                                   │
         │                                                   │
         └─────────────► Compute Absolute ◄──────────────────┘
                            Difference
                                │
                                ▼
                     ┌─────────────────────┐
                     │ Raw Pixel Difference│
                     └──────────┬──────────┘
                                │
                        Scale / Amplify (18x)
                                │
                                ▼
                     ┌─────────────────────┐
                     │ ELA Forensic Heatmap│
                     └─────────────────────┘
```

### The Math behind ELA
1. The sanitized image is saved to memory at a fixed compression rate of **75% quality**.
2. We compute the absolute pixel-by-pixel difference between the original image and the re-saved image:
   $$\text{Difference} = |\text{Pixel}_{\text{original}} - \text{Pixel}_{\text{resaved-75\%}}|$$
3. The raw differences are typically very faint. We amplify the differences by multiplying each pixel value by **18x** to make anomalies visually distinct:
   $$\text{Color}_{\text{amplified}} = \min(255, \text{Difference} \times 18)$$
4. A genuine receipt shows uniform noise levels across the image. An edited region (like modified transaction digits) shows high maximum-to-mean local error ratios ($>25$), which highlight as bright clusters of localized pixels in the output ELA heatmap.

---

## 📐 Sharpness & Laplacian Variance

When scammers paste text layers over existing screenshots, the edges of the pasted text typically show different sharpness gradients than the rest of the image.

To identify text overlay tampering, SuRaksha calculates the **Laplacian Variance** of the image:

1. We convert the image to grayscale and compute the Laplacian operator (which calculates the second spatial derivative of the image brightness):
   $$L(x,y) = \frac{\partial^2 I}{\partial x^2} + \frac{\partial^2 I}{\partial y^2}$$
2. We compute the variance (standard deviation squared) of the Laplacian results.
3. A natural, flat screenshot has a low variance. If an image contains high-contrast overlay text or artificial upscaling, the variance spikes significantly ($>2000$), flagging a potential tamper risk.

---

## 🔠 Text Extraction (Tesseract OCR)

Once forensic checks confirm the image has not been structurally tampered with, the system performs **Optical Character Recognition (OCR)** using Tesseract to extract the transaction details:

- **Preprocessing**: The in-memory image is converted to grayscale and thresholded using Otsu's binarization to maximize text legibility.
- **Data extraction**: The engine extracts recipient handles, payment amounts, and transaction statuses.
- **Parsing**: The extracted text is then forwarded directly to the natural language processing (NLP) and name matching engines to verify transaction details.
