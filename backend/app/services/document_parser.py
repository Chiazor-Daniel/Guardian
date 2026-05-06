import io
import base64
from typing import Dict, List
from PIL import Image

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


class DocumentParser:
    """
    Multi-format document parser supporting PDFs, images, and text files.
    Converts documents to structured markdown/text for analysis.
    """

    SUPPORTED_IMAGE_TYPES = {'image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/gif'}
    SUPPORTED_DOC_TYPES = {'application/pdf'}

    async def parse_file(self, filename: str, content: bytes, content_type: str) -> Dict:
        """
        Parse uploaded file based on content type.
        Returns extracted text and metadata.
        """
        result = {
            'filename': filename,
            'content_type': content_type,
            'text': '',
            'images': [],
            'metadata': {}
        }

        if content_type in self.SUPPORTED_DOC_TYPES or filename.lower().endswith('.pdf'):
            result.update(await self._parse_pdf(content))
        elif content_type in self.SUPPORTED_IMAGE_TYPES or any(
            filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp']
        ):
            result.update(await self._parse_image(content, filename))
        elif content_type.startswith('text/') or filename.lower().endswith(('.txt', '.md', '.csv')):
            result['text'] = content.decode('utf-8', errors='ignore')
        else:
            # Try to extract as text
            try:
                result['text'] = content.decode('utf-8', errors='ignore')
            except:
                result['error'] = f'Unsupported file type: {content_type}'

        return result

    async def _parse_pdf(self, content: bytes) -> Dict:
        """Extract text and images from PDF using PyMuPDF."""
        if not PYMUPDF_AVAILABLE:
            return {'error': 'PyMuPDF not installed. Run: pip install pymupdf'}

        result = {'text': '', 'images': [], 'metadata': {}}

        try:
            doc = fitz.open(stream=content, filetype="pdf")

            # Extract metadata
            result['metadata'] = {
                'page_count': len(doc),
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'subject': doc.metadata.get('subject', ''),
                'creator': doc.metadata.get('creator', ''),
                'keywords': doc.metadata.get('keywords', '')
            }

            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(doc):
                text_parts.append(f"\n--- Page {page_num + 1} ---\n")
                text_parts.append(page.get_text())

                # Extract images from page
                images = page.get_images()
                for img_index, img in enumerate(images[:5]):  # Limit to 5 images per page
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]

                    # Convert to base64
                    img_b64 = base64.b64encode(image_bytes).decode('utf-8')
                    result['images'].append({
                        'page': page_num + 1,
                        'format': image_ext,
                        'data': f'data:image/{image_ext};base64,{img_b64}'
                    })

            result['text'] = '\n'.join(text_parts)
            doc.close()

        except Exception as e:
            result['error'] = f'PDF parsing error: {str(e)}'

        return result

    async def _parse_image(self, content: bytes, filename: str) -> Dict:
        """Parse image and optionally run OCR if text is detected."""
        result = {'text': '', 'images': [], 'metadata': {}}

        try:
            # Open image
            img = Image.open(io.BytesIO(content))
            result['metadata'] = {
                'format': img.format,
                'size': img.size,
                'mode': img.mode
            }

            # Store image as base64
            img_b64 = base64.b64encode(content).decode('utf-8')
            mime_type = f'image/{img.format.lower()}' if img.format else 'image/png'

            result['images'].append({
                'filename': filename,
                'data': f'data:{mime_type};base64,{img_b64}'
            })

            # Try OCR if available
            if TESSERACT_AVAILABLE:
                try:
                    ocr_text = pytesseract.image_to_string(img)
                    if ocr_text.strip():
                        result['text'] = f"[OCR Extracted Text]\n{ocr_text}"
                except Exception as e:
                    result['ocr_error'] = str(e)

        except Exception as e:
            result['error'] = f'Image parsing error: {str(e)}'

        return result
