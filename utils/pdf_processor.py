import re


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extracts text from a PDF file.

    This is a very lightweight implementation designed for testing.
    It reads the file as bytes, checks for the presence of '/Encrypt'
    to detect an encrypted PDF, and then extracts any text found inside
    parentheses. The extracted text is returned as a single string.

    Parameters
    ----------
    pdf_path : str
        Path to the PDF file.

    Returns
    -------
    str
        Extracted text.

    Raises
    ------
    ValueError
        If the PDF appears to be encrypted or contains no extractable text.
    """
    with open(pdf_path, "rb") as file:
        content_bytes = file.read()

    content = content_bytes.decode("latin-1", errors="ignore")

    if "/Encrypt" in content:
        raise ValueError("PDF is encrypted and cannot be processed")

    texts = re.findall(r"\(([^()]*)\)", content)
    extracted = " ".join(t.strip() for t in texts if t.strip())

    if not extracted:
        raise ValueError("No text found in PDF")

    return extracted
