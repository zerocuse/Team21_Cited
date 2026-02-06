import fitz  
import docx

def extract_pdf_text(filepath: str) -> str:
    doc = fitz.open(filepath)
    text = []

    for page in doc:
        page_text = page.get_text("text")
        if page_text:
            text.append(page_text)

    doc.close()
    return "\n".join(text)

def extract_docx_text(filepath: str) -> str:
    doc = docx.Document(filepath)
    return "\n".join(p.text for p in doc.paragraphs if p.text)

def extract_txt_text(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()
    
def extract_text(filepath: str) -> str:
    filepath = filepath.lower()

    if filepath.endswith(".pdf"):
        return extract_pdf_text(filepath)

    if filepath.endswith(".docx"):
        return extract_docx_text(filepath)

    if filepath.endswith(".txt"):
        return extract_txt_text(filepath)

    return ""
