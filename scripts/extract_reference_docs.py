from docx import Document
from pypdf import PdfReader
import re

# Extract DOCX structure
docx_path = r"D:\Gitproject\RJBRJB\docs\required_docs\旷野智行-基于机器视觉与切线退出策略的无人车自主导航平台(3)(2).docx"
doc = Document(docx_path)
out = []
out.append('=== DOCX: 旷野智行 ===')
out.append('')
for para in doc.paragraphs:
    text = para.text.strip()
    if not text:
        continue
    style = para.style.name if para.style else 'Normal'
    # Only include headings and first 60 chars of important paragraphs
    if style.startswith('Heading') or '标题' in style:
        level = style.replace('Heading ', '').replace('标题', '')
        out.append(f'[H{level}] {text}')
    elif len(text) < 150:
        out.append(f'      {text}')

# Extract PDF text structure (best effort)
pdf_path = r"D:\Gitproject\RJBRJB\docs\required_docs\作品设计文档.pdf"
reader = PdfReader(pdf_path)
out.append('')
out.append('=== PDF: 作品设计文档 ===')
out.append(f'Total pages: {len(reader.pages)}')
out.append('')
for i, page in enumerate(reader.pages[:30]):  # first 30 pages
    text = page.extract_text()
    if text:
        lines = text.split('\n')
        out.append(f'--- Page {i+1} ---')
        for line in lines[:40]:  # limit lines per page
            line = line.strip()
            if line:
                out.append(line)

with open(r'D:\Gitproject\RJBRJB\docs\reference_docs_structure.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print('Extracted reference docs structure to docs/reference_docs_structure.txt')
print('\n'.join(out[:80]))
