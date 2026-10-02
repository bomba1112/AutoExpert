"""Branded PDF from the same immutable consumer projection used by the app."""

from __future__ import annotations

import io
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.paid_report import PaidVehicleReport
from app.services.paid_report import tr

FONT_DIR = Path(__file__).resolve().parents[1] / "assets" / "fonts"


def render_report_pdf(
    report: PaidVehicleReport,
    *,
    sources: list[dict],
    photo_assets: dict[str, bytes] | None = None,
) -> bytes:
    for style, filename in (("AE", "NotoSans-Regular.ttf"), ("AE-Bold", "NotoSans-Bold.ttf")):
        if style not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(style, str(FONT_DIR / filename)))
    ink, muted, gold = (
        colors.HexColor("#182D3A"),
        colors.HexColor("#52636D"),
        colors.HexColor("#137B80"),
    )
    normal = ParagraphStyle(
        "Body", fontName="AE", fontSize=10.5, leading=15.5, textColor=ink, spaceAfter=8
    )
    small = ParagraphStyle("Small", parent=normal, fontSize=8, leading=11, textColor=muted)
    title = ParagraphStyle(
        "Title", parent=normal, fontName="AE-Bold", fontSize=26, leading=33, spaceAfter=14
    )
    heading = ParagraphStyle(
        "Heading",
        parent=normal,
        fontName="AE-Bold",
        fontSize=16,
        leading=23,
        spaceBefore=13,
        spaceAfter=12,
        keepWithNext=True,
    )
    label = ParagraphStyle(
        "Label", parent=normal, fontSize=9.5, leading=14, textColor=muted, spaceAfter=0
    )
    value = ParagraphStyle("Value", parent=normal, fontSize=10.5, leading=15, spaceAfter=0)
    output = io.BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=66,
        bottomMargin=48,
        title=report.title,
        author="Auto Expert 2.0",
        pageCompression=1,
    )
    story = []

    def paragraph(text, style=normal):  # noqa: ANN001, ANN202
        text = text.translate(str.maketrans({"—": "-", "–": "-", "‑": "-"}))
        return Paragraph(escape(text).replace("\n", "<br/>"), style)

    story.extend(
        [
            paragraph(report.subtitle.upper(), small),
            paragraph(report.title, title),
            paragraph(f"VIN  {report.vin}", normal) if report.vin else Spacer(1, 1),
            paragraph(report.generated_at.strftime("%d.%m.%Y") + "  |  AUTO EXPERT 2.0", small),
            Spacer(1, 12),
        ]
    )
    if report.notice:
        story.extend([paragraph(report.notice, normal), Spacer(1, 10)])
    # Evidence sections vary in length; let content flow instead of reserving
    # whole pages for fixed section positions in the expanded report.
    page_starts = (
        set()
        if report.version in {"0.7.0", "0.8.0", "0.8.1"}
        else (
            set()
            if any(section.key == "history" for section in report.sections)
            else {"engine", "chassis", "weak_points", "expert_verdict"}
        )
    )
    for index, section in enumerate(report.sections):
        if section.key in page_starts:
            story.append(PageBreak())
        section_start = len(story)
        story.append(paragraph(f"{index + 1:02d}  {section.title}", heading))
        if section.rows:
            rows = [
                [paragraph(row.label, label), paragraph(row.value, value)] for row in section.rows
            ]
            table = Table(rows, colWidths=[175, A4[0] - 84 - 175], hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 3 if section.key == "vehicle" else 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4 if section.key == "vehicle" else 8),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#E2E7EA")),
                        (
                            "ROWBACKGROUNDS",
                            (0, 0),
                            (-1, -1),
                            [colors.white, colors.HexColor("#F6F8FA")],
                        ),
                    ]
                )
            )
            story.extend([table, Spacer(1, 10)])
        for item in section.paragraphs:
            story.append(paragraph(item.text))
        if section.key == "expert_verdict":
            story[section_start:] = [KeepTogether(story[section_start:])]
        if not section.rows and not section.paragraphs:
            story.append(
                paragraph(
                    tr(
                        report.language,
                        "Содержательные сведения в подключённых источниках не найдены.",
                        "Qoşulmuş mənbələrdə məzmunlu məlumat tapılmayıb.",
                        "No substantive information was found in connected sources.",
                    ),
                    small,
                )
            )
        if section.key == "history":
            for event in section.events:
                story.append(paragraph(event.title, heading))
                for row in event.rows:
                    story.append(paragraph(f"{row.label}: {row.value}"))
                for group in report.photo_sets:
                    if group.event_id != event.id:
                        continue
                    for photo in group.photos:
                        asset = (photo_assets or {}).get(photo.id)
                        if not asset:
                            raise ValueError("Cannot export a gallery without its verified assets")
                        picture = Image(io.BytesIO(asset))
                        picture._restrictSize(A4[0] - 84, 250)
                        story.append(KeepTogether([picture, paragraph(photo.caption, small)]))
            for photo_set in report.photo_sets:
                if section.events:
                    continue
                for photo in photo_set.photos:
                    asset = (photo_assets or {}).get(photo.id)
                    if asset:
                        picture = Image(io.BytesIO(asset))
                        picture._restrictSize(A4[0] - 84, 280)
                        story.append(KeepTogether([picture, paragraph(photo.caption, small)]))
                    else:
                        story.append(paragraph(photo.caption + " · " + str(photo.asset_url), small))
    story.extend(
        [
            Spacer(1, 14),
            paragraph(
                tr(report.language, "Источники отчёта", "Hesabatın mənbələri", "Report sources"),
                heading,
            ),
        ]
    )
    # Group the same publisher/date while retaining a separate link to every
    # source. Multiple NHTSA records must not create a mostly empty extra page.
    source_groups = {}
    for source in sources:
        if source["id"] not in report.source_ids:
            continue
        key = (source["publisher"], str(source.get("retrieved_at", ""))[:10])
        source_groups.setdefault(key, []).append(str(source.get("url", "")))
    for (publisher, date), urls in source_groups.items():
        links = [
            f'<link href="{escape(url)}" color="#805D25">{i + 1}</link>'
            for i, url in enumerate(urls)
            if url.startswith("https://")
        ]
        text = escape(f"{publisher} · {date}")
        if links:
            text += " · " + escape(tr(report.language, "Источники: ", "Mənbələr: ", "Sources: "))
            text += ", ".join(links)
        story.append(Paragraph(text, small))

    def page_frame(canvas, doc):  # noqa: ANN001, ANN202
        canvas.saveState()
        canvas.setFillColor(ink)
        canvas.setFont("AE-Bold", 11)
        canvas.drawString(42, A4[1] - 35, "AUTO EXPERT 2.0")
        canvas.setStrokeColor(gold)
        canvas.setLineWidth(1.5)
        canvas.line(42, A4[1] - 44, A4[0] - 42, A4[1] - 44)
        canvas.setFillColor(muted)
        canvas.setFont("AE", 8)
        canvas.drawString(42, 27, report.vin)
        canvas.drawRightString(A4[0] - 42, 27, str(doc.page))
        canvas.restoreState()

    normal.alignment = TA_LEFT
    document.build(story, onFirstPage=page_frame, onLaterPages=page_frame)
    return output.getvalue()
