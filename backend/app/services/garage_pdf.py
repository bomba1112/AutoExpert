# ruff: noqa: E501
"""The service log of a Garage car as a PDF (product phase, stage 2): the history of works for the
sale of the car. The records are the owner's own entries; the PDF says so and does not present them
as verified."""

from __future__ import annotations

import io
from datetime import date
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.english import pick
from app.services.garage import day_text
from app.services.report_pdf import FONT_DIR

STATUS = {"DONE": ("выполнено", "edilib", "done"), "UNKNOWN": ("дата неизвестна", "tarix məlum deyil", "date unknown"),
          "ONBOARD_RESET": ("по сигналу бортовой системы", "bort sisteminin siqnalı ilə", "on the onboard system's request")}
ACTIONS = {"REPLACE": ("замена", "dəyişmə", "replacement"), "INSPECT": ("проверка", "yoxlama", "inspection"),
           "ROTATE": ("перестановка", "yerdəyişmə", "rotation"), "ADJUST": ("регулировка", "tənzimləmə", "adjustment"),
           "CLEAN": ("очистка", "təmizləmə", "cleaning")}


def render(view: dict, language: str, today: date | None = None) -> bytes:
    for style, filename in (("AE", "NotoSans-Regular.ttf"), ("AE-Bold", "NotoSans-Bold.ttf")):
        if style not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(style, str(FONT_DIR / filename)))
    ink, muted, accent = colors.HexColor("#182D3A"), colors.HexColor("#52636D"), colors.HexColor("#137B80")
    normal = ParagraphStyle("Body", fontName="AE", fontSize=10, leading=14, textColor=ink)
    small = ParagraphStyle("Small", parent=normal, fontSize=8, leading=11, textColor=muted)
    title = ParagraphStyle("Title", parent=normal, fontName="AE-Bold", fontSize=20, leading=26, spaceAfter=6)
    cell = ParagraphStyle("Cell", parent=normal, fontSize=9, leading=12)
    head = ParagraphStyle("Head", parent=cell, fontName="AE-Bold", textColor=colors.white)
    p = lambda ru, az, en: pick(language, ru, az, en)  # noqa: E731
    output = io.BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=56, bottomMargin=44,
                                 title=f"{view['title']} — service log", author="Auto Expert 2.0")
    story = [Paragraph(escape(p("Журнал обслуживания", "Texniki xidmət jurnalı", "Service log")), title),
             Paragraph(escape(view["title"] + (f" · {view['configuration']}" if view.get("configuration") else "")), normal)]
    if view.get("vin"):
        story.append(Paragraph(escape(f"VIN {view['vin']}"), normal))
    if view["mileage"].get("last"):
        last = view["mileage"]["last"]
        story.append(Paragraph(escape(p("Последний пробег", "Son yürüş", "Last odometer reading") + f": {last['text']} · "
                                      + day_text(date.fromisoformat(last["on"]), language)), normal))
    story += [Spacer(1, 10)]
    rows = [[Paragraph(escape(x), head) for x in (p("Дата", "Tarix", "Date"), p("Пробег", "Yürüş", "Odometer"),
                                                  p("Работа", "İş", "Work"), p("Отметка", "Qeyd", "Status"))]]
    for r in view["log"]:
        when = day_text(date.fromisoformat(r["on"]), language) if r["on"] else "—"
        work = r["label"] + f" · {pick(language, *ACTIONS.get(r['action'], (r['action'],) * 3))}"
        if r.get("note"):
            work += f" · {r['note']}"
        rows.append([Paragraph(escape(x or "—"), cell) for x in (when, r["km_text"], work, pick(language, *STATUS.get(r["status"], (r["status"],) * 3)))])
    if len(rows) == 1:
        rows.append([Paragraph(escape(p("Записей пока нет", "Hələ qeyd yoxdur", "No records yet")), cell), "", "", ""])
    table = Table(rows, colWidths=[78, 92, 238, 107], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), accent), ("VALIGN", (0, 0), (-1, -1), "TOP"),
                               ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#D5DDE1")),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story += [table, Spacer(1, 12),
              Paragraph(escape(p("Записи внесены владельцем в приложении Auto Expert; приложение их не проверяет. Подтверждают их заказ-наряды и чеки сервиса.",
                                 "Qeydlər sahibi tərəfindən Auto Expert tətbiqində daxil edilib; tətbiq onları yoxlamır. Onları servisin sifariş-aktları və çekləri təsdiqləyir.",
                                 "The records were entered by the owner in the Auto Expert app; the app does not verify them. Service work orders and receipts confirm them.")), small),
              Paragraph(escape(p("Сформировано", "Yaradılıb", "Generated") + f": {day_text(today or date.today(), language)}"), small)]

    def frame(canvas, doc):  # noqa: ANN001, ANN202
        canvas.saveState()
        canvas.setFont("AE-Bold", 11)
        canvas.setFillColor(ink)
        canvas.drawString(40, A4[1] - 32, "AUTO EXPERT 2.0")
        canvas.setStrokeColor(accent)
        canvas.line(40, A4[1] - 40, A4[0] - 40, A4[1] - 40)
        canvas.setFont("AE", 8)
        canvas.setFillColor(muted)
        canvas.drawRightString(A4[0] - 40, 24, str(doc.page))
        canvas.restoreState()

    document.build(story, onFirstPage=frame, onLaterPages=frame)
    return output.getvalue()
