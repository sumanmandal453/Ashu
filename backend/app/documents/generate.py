from __future__ import annotations

from io import BytesIO
from typing import Any


def generate_docx(title: str, student: dict[str, Any], subject: str, qa: list[dict[str, str]]) -> bytes:
    from docx import Document
    from docx.shared import Pt

    doc = Document()
    doc.add_heading(title, 0)
    doc.add_paragraph(f"Student: {student.get('full_name') or 'Student'}")
    doc.add_paragraph(f"Roll number: {student.get('roll_number') or 'Not provided'}")
    doc.add_paragraph(f"Department: {student.get('department') or 'Not provided'}")
    doc.add_paragraph(f"Subject: {subject or 'Not specified'}")
    doc.add_paragraph("")
    for index, item in enumerate(qa, 1):
        doc.add_heading(f"Question {index}", level=2)
        doc.add_paragraph(item.get("question", ""))
        doc.add_heading("Answer", level=3)
        doc.add_paragraph(item.get("answer", ""))
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(11)
    out = BytesIO()
    doc.save(out)
    return out.getvalue()


def generate_pdf(title: str, student: dict[str, Any], subject: str, qa: list[dict[str, str]]) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    from xml.sax.saxutils import escape

    out = BytesIO()
    doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=18*mm, bottomMargin=18*mm)
    styles = getSampleStyleSheet()
    story = [Paragraph(escape(title), styles["Title"]), Spacer(1, 8)]
    story += [Paragraph(f"Student: {escape(str(student.get('full_name') or 'Student'))}", styles["Normal"]),
              Paragraph(f"Roll number: {escape(str(student.get('roll_number') or 'Not provided'))}", styles["Normal"]),
              Paragraph(f"Subject: {escape(subject or 'Not specified')}", styles["Normal"]), Spacer(1, 12)]
    for index, item in enumerate(qa, 1):
        story.append(Paragraph(f"Question {index}", styles["Heading2"]))
        story.append(Paragraph(escape(item.get("question", "" )).replace("\n", "<br/>"), styles["BodyText"]))
        story.append(Paragraph("Answer", styles["Heading3"]))
        story.append(Paragraph(escape(item.get("answer", "")).replace("\n", "<br/>"), styles["BodyText"]))
        story.append(Spacer(1, 10))
    doc.build(story)
    return out.getvalue()
