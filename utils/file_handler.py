"""
文件处理工具
用于解析各种格式的上传文件
"""
import PyPDF2
from docx import Document


def extract_text_from_pdf(file):
    """从PDF文件中提取文本"""
    text = ""
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text


def extract_text_from_docx(file):
    """从Word文件中提取文本"""
    doc = Document(file)
    text = ""
    for para in doc.paragraphs:
        text += para.text + "\n"
    return text


def extract_text_from_txt(file):
    """从文本文件中提取内容"""
    return file.getvalue().decode("utf-8")


def parse_uploaded_file(file):
    """解析上传的文件，返回文本内容"""
    file_type = file.name.split(".")[-1].lower()

    if file_type == "pdf":
        return extract_text_from_pdf(file)
    elif file_type == "docx":
        return extract_text_from_docx(file)
    elif file_type in ["txt", "md"]:
        return extract_text_from_txt(file)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")
