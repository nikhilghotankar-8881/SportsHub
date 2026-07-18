"""
app/helpers/invoice_helper.py
Generates PDF invoices using ReportLab.
"""
import io
from datetime import datetime
from flask import current_app

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table,
        TableStyle, HRFlowable,
    )
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def generate_invoice_pdf(order) -> bytes:
    """
    Generate a PDF invoice for the given Order object.
    Returns raw bytes of the PDF.
    Falls back to a minimal text-based PDF if ReportLab unavailable.
    """
    if not REPORTLAB_AVAILABLE:
        return _fallback_pdf(order)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    elements = []

    # ── Color palette ─────────────────────────────────────────────────────────
    PRIMARY   = colors.HexColor("#5c6bc0")
    DARK      = colors.HexColor("#1a1a2e")
    LIGHT_BG  = colors.HexColor("#f5f7ff")
    GREEN     = colors.HexColor("#27ae60")
    RED       = colors.HexColor("#e74c3c")
    GREY      = colors.HexColor("#7f8c8d")
    BORDER    = colors.HexColor("#dde1f0")

    # ── Custom styles ─────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "InvoiceTitle",
        fontSize=22,
        fontName="Helvetica-Bold",
        textColor=DARK,
        alignment=TA_LEFT,
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        fontSize=10,
        textColor=GREY,
        alignment=TA_LEFT,
    )
    header_style = ParagraphStyle(
        "Header",
        fontSize=10,
        fontName="Helvetica-Bold",
        textColor=DARK,
    )
    normal_style = ParagraphStyle(
        "Normal",
        fontSize=9,
        textColor=DARK,
        leading=14,
    )
    small_grey = ParagraphStyle(
        "SmallGrey",
        fontSize=8,
        textColor=GREY,
        leading=12,
    )
    right_style = ParagraphStyle(
        "Right",
        fontSize=9,
        textColor=DARK,
        alignment=TA_RIGHT,
    )
    total_style = ParagraphStyle(
        "Total",
        fontSize=12,
        fontName="Helvetica-Bold",
        textColor=PRIMARY,
        alignment=TA_RIGHT,
    )

    company = current_app.config
    gst_rate = company.get("GST_RATE", 18)

    # ──────────────────────────────────────────────────────────────────────────
    # HEADER: Company + Invoice Info (2-column table)
    # ──────────────────────────────────────────────────────────────────────────
    company_col = [
        Paragraph("⚡ SportsHub", title_style),
        Paragraph(company.get("COMPANY_ADDRESS", ""), normal_style),
        Paragraph(f"📞 {company.get('COMPANY_PHONE', '')}", normal_style),
        Paragraph(f"✉ {company.get('COMPANY_EMAIL', '')}", normal_style),
        Paragraph(f"GST: {company.get('COMPANY_GST', '')}", small_grey),
    ]
    invoice_col = [
        Paragraph("INVOICE", ParagraphStyle(
            "Inv", fontSize=18, fontName="Helvetica-Bold",
            textColor=PRIMARY, alignment=TA_RIGHT,
        )),
        Paragraph(f"<b>Invoice No:</b> {order.invoice_number}", ParagraphStyle(
            "InvNo", fontSize=9, textColor=DARK, alignment=TA_RIGHT,
        )),
        Paragraph(f"<b>Order ID:</b> #{order.id}", ParagraphStyle(
            "OrdId", fontSize=9, textColor=DARK, alignment=TA_RIGHT,
        )),
        Paragraph(f"<b>Date:</b> {order.created_at.strftime('%d %b %Y')}", ParagraphStyle(
            "Date", fontSize=9, textColor=DARK, alignment=TA_RIGHT,
        )),
        Paragraph(f"<b>Status:</b> {order.status_label}", ParagraphStyle(
            "Status", fontSize=9, textColor=PRIMARY, alignment=TA_RIGHT,
        )),
    ]

    header_table = Table(
        [[company_col, invoice_col]],
        colWidths=["55%", "45%"],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LINEBELOW", (0, 0), (-1, 0), 1.5, PRIMARY),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 8 * mm))

    # ──────────────────────────────────────────────────────────────────────────
    # BILL TO / SHIP TO
    # ──────────────────────────────────────────────────────────────────────────
    bill_data = [
        [Paragraph("BILL TO / SHIP TO", ParagraphStyle(
            "BillHeader", fontSize=9, fontName="Helvetica-Bold",
            textColor=PRIMARY,
        ))],
        [Paragraph(order.shipping_name, header_style)],
        [Paragraph(order.shipping_address, normal_style)],
        [Paragraph(f"{order.shipping_city}", normal_style)],
        [Paragraph(f"📞 {order.shipping_phone}", normal_style)],
        [Paragraph(f"✉ {order.user.email}", normal_style)],
    ]
    bill_table = Table(bill_data, colWidths=["100%"])
    bill_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    elements.append(bill_table)
    elements.append(Spacer(1, 6 * mm))

    # ──────────────────────────────────────────────────────────────────────────
    # ITEMS TABLE
    # ──────────────────────────────────────────────────────────────────────────
    col_widths = ["5%", "45%", "15%", "17%", "18%"]
    item_data = [
        [
            Paragraph("#", ParagraphStyle("TH", fontSize=9, fontName="Helvetica-Bold",
                                          textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("Product", ParagraphStyle("TH", fontSize=9, fontName="Helvetica-Bold",
                                                textColor=colors.white)),
            Paragraph("Qty", ParagraphStyle("TH", fontSize=9, fontName="Helvetica-Bold",
                                            textColor=colors.white, alignment=TA_CENTER)),
            Paragraph("Unit Price", ParagraphStyle("TH", fontSize=9, fontName="Helvetica-Bold",
                                                   textColor=colors.white, alignment=TA_RIGHT)),
            Paragraph("Amount", ParagraphStyle("TH", fontSize=9, fontName="Helvetica-Bold",
                                               textColor=colors.white, alignment=TA_RIGHT)),
        ]
    ]

    for idx, item in enumerate(order.order_items, start=1):
        row_bg = colors.white if idx % 2 == 0 else LIGHT_BG
        item_data.append([
            Paragraph(str(idx), ParagraphStyle("Cell", fontSize=9, alignment=TA_CENTER)),
            Paragraph(item.product.name, ParagraphStyle("Cell", fontSize=9)),
            Paragraph(str(item.quantity), ParagraphStyle("Cell", fontSize=9, alignment=TA_CENTER)),
            Paragraph(f"₹{float(item.unit_price):,.2f}", ParagraphStyle("Cell", fontSize=9, alignment=TA_RIGHT)),
            Paragraph(f"₹{float(item.line_total):,.2f}", ParagraphStyle("Cell", fontSize=9, alignment=TA_RIGHT)),
        ])

    items_table = Table(item_data, colWidths=col_widths)
    ts = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ])
    # Alternate row colors
    for i in range(1, len(item_data)):
        if i % 2 == 0:
            ts.add("BACKGROUND", (0, i), (-1, i), colors.white)
        else:
            ts.add("BACKGROUND", (0, i), (-1, i), LIGHT_BG)
    items_table.setStyle(ts)
    elements.append(items_table)
    elements.append(Spacer(1, 4 * mm))

    # ──────────────────────────────────────────────────────────────────────────
    # TOTALS
    # ──────────────────────────────────────────────────────────────────────────
    subtotal   = float(sum(item.line_total for item in order.order_items))
    discount   = float(order.discount_amount or 0)
    gst_amount = float(order.gst_amount or 0)
    total      = float(order.total_amount)

    totals_data = [
        ["Subtotal",  f"₹{subtotal:,.2f}"],
    ]
    if discount > 0:
        totals_data.append([f"Discount ({order.coupon_code})", f"-₹{discount:,.2f}"])
    totals_data.append([f"GST ({gst_rate}%)", f"₹{gst_amount:,.2f}"])
    totals_data.append(["TOTAL", f"₹{total:,.2f}"])

    totals_rows = []
    for label, value in totals_data:
        is_total = label == "TOTAL"
        totals_rows.append([
            Paragraph(label, ParagraphStyle(
                "TL", fontSize=10 if is_total else 9,
                fontName="Helvetica-Bold" if is_total else "Helvetica",
                textColor=PRIMARY if is_total else DARK,
                alignment=TA_RIGHT,
            )),
            Paragraph(value, ParagraphStyle(
                "TV", fontSize=11 if is_total else 9,
                fontName="Helvetica-Bold" if is_total else "Helvetica",
                textColor=PRIMARY if is_total else DARK,
                alignment=TA_RIGHT,
            )),
        ])

    totals_table = Table(
        totals_rows,
        colWidths=["70%", "30%"],
        hAlign="RIGHT",
    )
    totals_style = TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, PRIMARY),
        ("BACKGROUND", (0, -1), (-1, -1), LIGHT_BG),
    ])
    if discount > 0:
        totals_style.add("TEXTCOLOR", (0, 1), (-1, 1), GREEN)
    totals_table.setStyle(totals_style)
    elements.append(totals_table)
    elements.append(Spacer(1, 8 * mm))

    # ──────────────────────────────────────────────────────────────────────────
    # FOOTER
    # ──────────────────────────────────────────────────────────────────────────
    elements.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph(
        "Thank you for shopping with SportsHub! For any queries, contact us at nikhilghotankar@gmail.com",
        ParagraphStyle("Footer", fontSize=8, textColor=GREY, alignment=TA_CENTER),
    ))
    elements.append(Paragraph(
        f"Generated on {datetime.utcnow().strftime('%d %b %Y %H:%M')} UTC · Invoice is computer-generated and valid without signature.",
        ParagraphStyle("Footer2", fontSize=7, textColor=GREY, alignment=TA_CENTER),
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


def _fallback_pdf(order) -> bytes:
    """Minimal text PDF fallback when ReportLab is not installed."""
    lines = [
        f"SPORTSHUB INVOICE",
        f"Invoice No: {order.invoice_number}",
        f"Order ID: #{order.id}",
        f"Date: {order.created_at.strftime('%d %b %Y')}",
        f"",
        f"Customer: {order.shipping_name}",
        f"Address: {order.shipping_address}, {order.shipping_city}",
        f"",
        f"ITEMS:",
    ]
    for item in order.order_items:
        lines.append(
            f"  {item.product.name} x{item.quantity} @ ₹{float(item.unit_price):,.2f}"
            f" = ₹{float(item.line_total):,.2f}"
        )
    lines.append(f"")
    lines.append(f"TOTAL: ₹{float(order.total_amount):,.2f}")
    content = "\n".join(lines)
    return content.encode("utf-8")
