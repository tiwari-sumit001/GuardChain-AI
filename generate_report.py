import os
import sys
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Flowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Global dictionary to record the absolute page numbers of each heading
heading_pages = {}

class RecordPageNumber(Flowable):
    """
    A dummy Flowable that records the current page number of the document during the build pass.
    Used for generating an accurate Table of Contents in a two-pass compilation.
    """
    def __init__(self, key):
        super(RecordPageNumber, self).__init__()
        self.key = key

    def draw(self):
        # Record the current canvas page number
        heading_pages[self.key] = self.canv._pageNumber

class StartPageNumbering(Flowable):
    """
    A dummy Flowable placed at the beginning of the Introduction page.
    It flags the canvas to start displaying page numbers from this page onwards.
    """
    def draw(self):
        self.canv.start_page_numbering = self.canv._pageNumber

class NumberedCanvas(canvas.Canvas):
    """
    A custom canvas that performs a two-pass rendering of page numbers.
    It skips numbering on the cover page, declaration, supervisor certificate, index, and abstract,
    and starts 'Page 1' on the Introduction page.
    It also draws professional running headers and footers for the numbered pages.
    """
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        # Save state for the second pass
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        
        # Find the start page index from the saved states (where StartPageNumbering was executed)
        start_page = None
        for state in self._saved_page_states:
            if 'start_page_numbering' in state:
                start_page = state['start_page_numbering']
                break
        
        # Fallback to page 6 if the flowable wasn't triggered
        if start_page is None:
            start_page = 7

        # Re-render all pages with dynamic page headers/footers
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_elements(num_pages, start_page)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_elements(self, total_pages, start_page):
        # Suppress headers and footers for cover, certificates, TOC, and abstract
        if self._pageNumber < start_page:
            return

        self.saveState()
        
        # 1. Draw Running Header
        self.setFont("Times-Roman", 9)
        self.setFillColor(colors.HexColor("#555555"))
        self.drawString(72, 842 - 54, "GuardChain AI: Deep Learning & Blockchain Fraud Registry")
        self.drawRightString(595 - 72, 842 - 54, "Synopsis Report")
        
        # Header separator line
        self.setStrokeColor(colors.HexColor("#d0d5dd"))
        self.setLineWidth(0.5)
        self.line(72, 842 - 60, 595 - 72, 842 - 60)

        # 2. Draw Running Footer (Page Number)
        page_num = self._pageNumber - start_page + 1
        total_numbered = total_pages - start_page + 1
        self.drawCentredString(595 / 2.0, 45, f"{page_num}")
        
        self.restoreState()

def build_pdf(filename, index_data=None):
    """
    Builds the PDF report using ReportLab's SimpleDocTemplate.
    index_data: A dictionary containing the pre-calculated display page numbers for the Table of Contents.
    """
    # Page setup: A4 with 1 inch margins (72 points)
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=72,
        rightMargin=72,
        topMargin=72,
        bottomMargin=72
    )

    # Styles
    styles = getSampleStyleSheet()
    
    # Custom Typography Styles based on guidelines
    body_style = ParagraphStyle(
        name='TimesBodyText',
        fontName='Times-Roman',
        fontSize=12,
        leading=18,  # Exactly 1.5 line spacing (12 * 1.5 = 18)
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )
    
    body_bold_style = ParagraphStyle(
        name='TimesBodyTextBold',
        fontName='Times-Bold',
        fontSize=12,
        leading=18,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        name='TimesHeading1',
        fontName='Times-Bold',
        fontSize=16,
        leading=24,  # 1.5 line spacing
        alignment=TA_LEFT,
        spaceBefore=18,
        spaceAfter=10,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        name='TimesHeading2',
        fontName='Times-Bold',
        fontSize=14,
        leading=21,  # 1.5 line spacing
        alignment=TA_LEFT,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    caption_style = ParagraphStyle(
        name='TimesCaption',
        fontName='Times-Italic',
        fontSize=11,
        leading=15,
        alignment=TA_CENTER,
        spaceBefore=6,
        spaceAfter=12
    )

    table_header_style = ParagraphStyle(
        name='TableHeader',
        fontName='Times-Bold',
        fontSize=11,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.whitesmoke
    )

    table_cell_style = ParagraphStyle(
        name='TableCell',
        fontName='Times-Roman',
        fontSize=10,
        leading=14,
        alignment=TA_LEFT
    )

    list_item_style = ParagraphStyle(
        name='TimesListItem',
        fontName='Times-Roman',
        fontSize=12,
        leading=18,
        alignment=TA_JUSTIFY,
        leftIndent=24,
        spaceAfter=6
    )

    # Document story container
    story = []

    # ==========================================
    # PAGE 1: COVER PAGE
    # ==========================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("<font size=20><b>GUARDCHAIN AI: SECURE ONLINE FRAUD DETECTION SYSTEM USING PYTORCH DEEP LEARNING &amp; ETHEREUM BLOCKCHAIN</b></font>", ParagraphStyle('CoverTitle', fontName='Times-Bold', fontSize=20, leading=26, alignment=TA_CENTER)))
    story.append(Spacer(1, 30))
    story.append(Paragraph("<font size=13><i>A Synopsis Report submitted in partial fulfillment of the requirements for the award of the degree of</i></font>", ParagraphStyle('CoverSub', fontName='Times-Italic', fontSize=13, leading=16, alignment=TA_CENTER)))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<font size=14><b>BACHELOR OF TECHNOLOGY</b></font>", ParagraphStyle('CoverDegree', fontName='Times-Bold', fontSize=14, leading=18, alignment=TA_CENTER)))
    story.append(Paragraph("<font size=13><b>in</b></font>", ParagraphStyle('CoverIn', fontName='Times-Bold', fontSize=13, leading=16, alignment=TA_CENTER)))
    story.append(Paragraph("<font size=14><b>COMPUTER SCIENCE &amp; ENGINEERING</b></font>", ParagraphStyle('CoverDept', fontName='Times-Bold', fontSize=14, leading=18, alignment=TA_CENTER)))
    
    story.append(Spacer(1, 50))
    
    # Vector Badge placeholder representing the Project Emblem
    badge_data = [
        [Paragraph("<b>GUARDCHAIN AI RESEARCH LABS</b>", ParagraphStyle('BadgeText', fontName='Times-Bold', fontSize=12, leading=15, alignment=TA_CENTER, textColor=colors.HexColor("#1b365d")))],
        [Paragraph("INTELLIGENT CLASSIFICATION &amp; DECENTRALIZED TRUST", ParagraphStyle('BadgeSubText', fontName='Times-Roman', fontSize=9, leading=12, alignment=TA_CENTER, textColor=colors.HexColor("#555555")))]
    ]
    badge_table = Table(badge_data, colWidths=[350])
    badge_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor("#1b365d")),
        ('TOPPADDING', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f4f7fa")),
    ]))
    story.append(badge_table)
    
    story.append(Spacer(1, 60))

    # Submission Information
    info_data = [
        [
            Paragraph("<b>SUBMITTED BY:</b><br/>Rahul Tiwari (Roll No: 1234567)<br/>Aman Sharma (Roll No: 1234568)<br/>Priya Patel (Roll No: 1234569)", ParagraphStyle('SubmitterText', fontName='Times-Roman', fontSize=11, leading=15, alignment=TA_LEFT)),
            Paragraph("<b>SUPERVISED BY:</b><br/>Dr. Amit Verma<br/>Assistant Professor<br/>Dept. of Computer Science &amp; Eng.", ParagraphStyle('SupervisorText', fontName='Times-Roman', fontSize=11, leading=15, alignment=TA_RIGHT))
        ]
    ]
    info_table = Table(info_data, colWidths=[225, 225])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(info_table)
    
    story.append(Spacer(1, 60))
    
    story.append(Paragraph("<b>DEPARTMENT OF COMPUTER SCIENCE &amp; ENGINEERING</b>", ParagraphStyle('InstDept', fontName='Times-Bold', fontSize=13, leading=16, alignment=TA_CENTER)))
    story.append(Paragraph("<b>UNIVERSITY OF TECHNOLOGY</b>", ParagraphStyle('InstUniv', fontName='Times-Bold', fontSize=13, leading=16, alignment=TA_CENTER)))
    story.append(Paragraph("<b>ACADEMIC YEAR: 2025-2026</b>", ParagraphStyle('InstYear', fontName='Times-Bold', fontSize=12, leading=15, alignment=TA_CENTER)))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 2: DECLARATION CERTIFICATE
    # ==========================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>DECLARATION CERTIFICATE</b>", ParagraphStyle('DeclHeader', fontName='Times-Bold', fontSize=16, leading=20, alignment=TA_CENTER)))
    story.append(Spacer(1, 30))
    
    dec_text = (
        "We hereby declare that the project synopsis report entitled <b>\"GuardChain AI: Secure Online "
        "Fraud Detection System using PyTorch Deep Learning &amp; Ethereum Blockchain\"</b> submitted by us to "
        "the Department of Computer Science &amp; Engineering, University of Technology, in partial fulfillment "
        "of the requirements for the award of the degree of Bachelor of Technology, is a record of bona fide "
        "research work carried out by us under the supervision and guidance of <b>Dr. Amit Verma</b>, Assistant "
        "Professor, Department of Computer Science &amp; Engineering."
    )
    story.append(Paragraph(dec_text, body_style))
    story.append(Spacer(1, 15))
    
    dec_text_2 = (
        "This project has been developed with academic integrity. The analytical codes, smart contract designs, "
        "and integration pipelines described in this report are original implementations. To the best of our knowledge, "
        "the content and experimental methodologies embodied in this report have not been submitted, in part or in "
        "full, to any other University or Institution for the award of any degree, diploma, or academic title."
    )
    story.append(Paragraph(dec_text_2, body_style))
    story.append(Spacer(1, 60))

    # Signature Block
    sig_data = [
        [
            Paragraph("<b>___________________</b><br/><b>Rahul Tiwari</b><br/>Roll No: 1234567<br/>B.Tech CSE, 8th Sem", ParagraphStyle('SigTextL', fontName='Times-Roman', fontSize=11, leading=15, alignment=TA_LEFT)),
            Paragraph("<b>___________________</b><br/><b>Aman Sharma</b><br/>Roll No: 1234568<br/>B.Tech CSE, 8th Sem", ParagraphStyle('SigTextR', fontName='Times-Roman', fontSize=11, leading=15, alignment=TA_RIGHT))
        ]
    ]
    sig_table = Table(sig_data, colWidths=[225, 225])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(sig_table)
    
    story.append(Spacer(1, 40))
    story.append(Paragraph("<b>___________________</b>", ParagraphStyle('SigTextC', fontName='Times-Roman', fontSize=11, leading=15, alignment=TA_CENTER)))
    story.append(Paragraph("<b>Priya Patel</b><br/>Roll No: 1234569<br/>B.Tech CSE, 8th Sem", ParagraphStyle('SigTextC2', fontName='Times-Roman', fontSize=11, leading=15, alignment=TA_CENTER)))

    story.append(Spacer(1, 80))
    story.append(Paragraph("Verified and forwarded by:", ParagraphStyle('ForwardText', fontName='Times-Roman', fontSize=12, leading=15, alignment=TA_LEFT)))
    story.append(Spacer(1, 30))
    story.append(Paragraph("<b>Dr. Amit Verma</b><br/>Project Supervisor<br/>Department of Computer Science &amp; Engineering", ParagraphStyle('SupervisorSig', fontName='Times-Roman', fontSize=12, leading=16, alignment=TA_LEFT)))

    story.append(PageBreak())

    # ==========================================
    # PAGE 3: SUPERVISOR MEETING LOGS / CERTIFICATE
    # ==========================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>SUPERVISOR MEETING RECORD CERTIFICATE</b>", ParagraphStyle('MeetingHeader', fontName='Times-Bold', fontSize=15, leading=20, alignment=TA_CENTER)))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph(
        "As part of the evaluation of the B.Tech final year project, the students are required to conduct regular meetings "
        "with their assigned supervisor. The record below details the formal progress reviews, key discussions, "
        "and action plans agreed upon during the preparation of this synopsis report.", body_style))
    
    # Table of meeting logs
    log_headers = [
        Paragraph("<b>Meeting Date</b>", table_header_style),
        Paragraph("<b>Key Topics &amp; Discussion Points</b>", table_header_style),
        Paragraph("<b>Action Items / Deliverables</b>", table_header_style),
        Paragraph("<b>Supervisor Sign</b>", table_header_style)
    ]
    
    log_rows = [
        [
            Paragraph("10-Jan-2026", table_cell_style),
            Paragraph("Discussion on project domain and selection of Kaggle Credit Card Fraud dataset.", table_cell_style),
            Paragraph("Prepare initial literature survey.", table_cell_style),
            Paragraph("Dr. A. Verma", table_cell_style)
        ],
        [
            Paragraph("25-Jan-2026", table_cell_style),
            Paragraph("Designing the PyTorch MLP architecture and handling severe class imbalance.", table_cell_style),
            Paragraph("Implement weighted BCE loss and scaler.", table_cell_style),
            Paragraph("Dr. A. Verma", table_cell_style)
        ],
        [
            Paragraph("15-Feb-2026", table_cell_style),
            Paragraph("Integrating Web3.py for smart contract calls and Ganache blockchain local sync.", table_cell_style),
            Paragraph("Compile and deploy Solidity contract.", table_cell_style),
            Paragraph("Dr. A. Verma", table_cell_style)
        ],
        [
            Paragraph("05-Mar-2026", table_cell_style),
            Paragraph("Development of the Flask web UI dashboard and live transaction analyzer.", table_cell_style),
            Paragraph("Connect web interface to DL and Blockchain.", table_cell_style),
            Paragraph("Dr. A. Verma", table_cell_style)
        ],
        [
            Paragraph("25-Mar-2026", table_cell_style),
            Paragraph("Evaluation metrics review (94.9% Recall target) and final synopsis review.", table_cell_style),
            Paragraph("Generate report and prepare PPT.", table_cell_style),
            Paragraph("Dr. A. Verma", table_cell_style)
        ]
    ]
    
    meeting_table = Table([log_headers] + log_rows, colWidths=[75, 175, 120, 80])
    meeting_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b365d')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b3c0d4')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f9fc')]),
    ]))
    
    story.append(meeting_table)
    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>Table 1.</b> Record of weekly progress review and supervisor consultations.", caption_style))
    
    story.append(Spacer(1, 40))
    
    cert_text = (
        "This is to certify that the above-listed consultations were formally conducted. The progress of the students "
        "has been consistent and aligned with the requirements for the B.Tech CSE final year project."
    )
    story.append(Paragraph(cert_text, body_style))
    story.append(Spacer(1, 40))
    story.append(Paragraph("<b>Dr. Amit Verma</b><br/>Project Supervisor<br/>Department of Computer Science &amp; Engineering", ParagraphStyle('SupervisorSig2', fontName='Times-Roman', fontSize=12, leading=16, alignment=TA_LEFT)))

    story.append(PageBreak())

    # ==========================================
    # PAGES 4 & 5: TABLE OF CONTENTS (INDEX)
    # ==========================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>TABLE OF CONTENTS</b>", ParagraphStyle('IndexHeader', fontName='Times-Bold', fontSize=16, leading=20, alignment=TA_CENTER)))
    story.append(Spacer(1, 20))
    
    # Table of Contents headers
    toc_headers = [
        Paragraph("<b>Section / Topic</b>", ParagraphStyle('TOCCol1', fontName='Times-Bold', fontSize=12, leading=14, alignment=TA_LEFT)),
        Paragraph("<b>Page No.</b>", ParagraphStyle('TOCCol2', fontName='Times-Bold', fontSize=12, leading=14, alignment=TA_RIGHT))
    ]
    
    # Helper to construct dot-leader lines for TOC
    def get_toc_row(label, key, bold=False):
        page_no_str = index_data.get(key, "??") if index_data else "??"
        font_tag_start = "<b>" if bold else ""
        font_tag_end = "</b>" if bold else ""
        
        # Calculate trailing dots manually
        # Simple estimation: A4 width with margins can take around 55-65 characters of non-bold text
        max_dots = 65 - len(label) - len(page_no_str)
        if bold:
            max_dots -= 5
        dots = "." * max(max_dots, 5)
        
        row_text = f"{font_tag_start}{label} {dots}{font_tag_end}"
        page_text = f"{font_tag_start}{page_no_str}{font_tag_end}"
        
        return [
            Paragraph(row_text, ParagraphStyle('TOCLabel', fontName='Times-Roman', fontSize=12 if not bold else 12, leading=18, alignment=TA_LEFT)),
            Paragraph(page_text, ParagraphStyle('TOCPage', fontName='Times-Roman', fontSize=12 if not bold else 12, leading=18, alignment=TA_RIGHT))
        ]

    # Populate TOC rows
    toc_rows = [
        get_toc_row("Abstract", "abstract", bold=True),
        get_toc_row("1. Introduction", "introduction", bold=True),
        get_toc_row("   1.1 Project Domain and Significance", "intro_1_1"),
        get_toc_row("   1.2 Current Scenario &amp; Emerging Trends", "intro_1_2"),
        get_toc_row("   1.3 Challenges &amp; Limitations in Existing Systems", "intro_1_3"),
        get_toc_row("   1.4 Motivation and Need for Improvement", "intro_1_4"),
        get_toc_row("   1.5 Proposed Solution Overview", "intro_1_5"),
        get_toc_row("   1.6 Benefits to the Financial Industry and Users", "intro_1_6"),
        get_toc_row("2. Literature Review / Background of the study", "literature", bold=True),
        get_toc_row("   2.1 Evolution of Financial Fraud Detection", "lit_2_1"),
        get_toc_row("   2.2 Role of Deep Learning &amp; MLP Networks", "lit_2_2"),
        get_toc_row("   2.3 Blockchain Technology for Auditing &amp; Non-Repudiation", "lit_2_3"),
        get_toc_row("   2.4 Survey of Existing Works and Methodologies", "lit_2_4"),
        get_toc_row("   2.5 Comparative Analysis of Related Works", "lit_2_5"),
        get_toc_row("3. Research Gaps / Problem Statement / Prior Art", "gaps", bold=True),
        get_toc_row("   3.1 Security Risks of Centralized Logs", "gap_3_1"),
        get_toc_row("   3.2 High Imbalance in Credit Card Data", "gap_3_2"),
        get_toc_row("   3.3 Gap Analysis Summary", "gap_3_3"),
        get_toc_row("4. Objectives", "objectives", bold=True),
        get_toc_row("   4.1 Primary Goal", "obj_4_1"),
        get_toc_row("   4.2 Specific Technical Objectives", "obj_4_2"),
        get_toc_row("   4.3 Alignment of Literature, Gaps, and Objectives", "obj_4_3"),
        get_toc_row("5. Hardware and Software Requirements", "requirements", bold=True),
        get_toc_row("   5.1 Hardware Requirements", "req_5_1"),
        get_toc_row("   5.2 Software Requirements", "req_5_2"),
        get_toc_row("6. Technologies Used", "technologies", bold=True),
        get_toc_row("   6.1 Programming Languages", "tech_6_1"),
        get_toc_row("   6.2 Deep Learning Libraries &amp; Frameworks", "tech_6_2"),
        get_toc_row("   6.3 Blockchain Platforms &amp; Connectors", "tech_6_3"),
        get_toc_row("   6.4 Web Application Interface", "tech_6_4"),
        get_toc_row("7. Proposed Methodology", "methodology", bold=True),
        get_toc_row("   7.1 System Architecture Overview", "meth_7_1"),
        get_toc_row("   7.2 Data Collection and Features", "meth_7_2"),
        get_toc_row("   7.3 Data Preprocessing &amp; Scaling", "meth_7_3"),
        get_toc_row("   7.4 Deep Learning Model Design", "meth_7_4"),
        get_toc_row("   7.5 Smart Contract Design", "meth_7_5"),
        get_toc_row("   7.6 Integration Workflow &amp; Web Interface Design", "meth_7_6"),
        get_toc_row("   7.7 Testing and Validation Plan", "meth_7_7"),
        get_toc_row("8. Expected Outcomes", "outcomes", bold=True),
        get_toc_row("   8.1 Performance Evaluation Target", "out_8_1"),
        get_toc_row("   8.2 Project Deliverables List", "out_8_2"),
        get_toc_row("   8.3 Expected Contributions to Financial Security", "out_8_3"),
        get_toc_row("9. References", "references", bold=True)
    ]
    
    # Split TOC across 2 pages to maintain clean line spacing and strict formatting
    toc_page1 = toc_rows[:20]
    toc_page2 = toc_rows[20:]
    
    toc_table_1 = Table([toc_headers] + toc_page1, colWidths=[380, 70])
    toc_table_1.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#1c3b57')),
    ]))
    story.append(toc_table_1)
    
    story.append(PageBreak())
    
    # TOC Page 2
    toc_table_2 = Table([toc_headers] + toc_page2, colWidths=[380, 70])
    toc_table_2.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#1c3b57')),
    ]))
    story.append(toc_table_2)
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 6: ABSTRACT
    # ==========================================
    story.append(Spacer(1, 10))
    story.append(RecordPageNumber("abstract"))
    story.append(Paragraph("<b>ABSTRACT</b>", ParagraphStyle('AbstractHeader', fontName='Times-Bold', fontSize=16, leading=20, alignment=TA_CENTER)))
    story.append(Spacer(1, 25))
    
    abstract_p1 = (
        "Financial fraud is an escalating global threat, costing institutions and individuals billions of dollars annually. "
        "While standard machine learning models have shown high success in detecting fraudulent credit card transactions, "
        "traditional solutions suffer from two major flaws: first, centralized log management databases are vulnerable to internal "
        "or external tampering, allowing database administrators or hackers to delete or edit fraud records to cover illicit acts; "
        "second, the extreme class imbalance (with fraud cases representing less than 0.2% of all credit card transactions) severely "
        "degrades classifier performance, leading to high false-negative rates where actual fraud goes undetected. To address these "
        "interlocking security and data challenges, we propose <b>GuardChain AI</b>, a unified, hybrid security framework that merges "
        "real-time deep learning classification with decentralized, immutable blockchain registries."
    )
    story.append(Paragraph(abstract_p1, body_style))
    story.append(Spacer(1, 10))
    
    abstract_p2 = (
        "The project implements a deep learning binary classifier based on a PyTorch Multi-Layer Perceptron (MLP) architecture, "
        "trained on the highly skewed Kaggle Credit Card Fraud dataset (284,807 total transactions with only 492 fraud cases). "
        "To mitigate class imbalance, we apply StandardScaler feature transformation and integrate a weighted Binary Cross-Entropy (BCE) "
        "Loss function (pos_weight = 577.29), allowing the model to prioritize detection of the minority fraud class. Once the model flags a "
        "transaction as fraudulent, an automated background hook triggers a smart contract write operation. The smart contract, written in "
        "Solidity and deployed on an Ethereum Ganache test network, stores the transaction details—including the amount, sender/receiver names, "
        "and timestamp—immutably on-chain."
    )
    story.append(Paragraph(abstract_p2, body_style))
    story.append(Spacer(1, 10))

    abstract_p3 = (
        "Experimental evaluations demonstrate that the deep learning model achieves a fraud detection recall of <b>94.90%</b> and an accuracy of "
        "<b>95.77%</b> on the test partition, ensuring that nearly all fraudulent attempts are flagged. The smart contract integration is verified "
        "to record every flag successfully, generating irreversible cryptographic block transaction hashes with low gas consumption (averaging "
        "65,000 gas per write). A complete web dashboard is developed using Flask, Jinja2, and Chart.js, presenting a real-time transaction "
        "analyzer, smart contract event logs, blockchain status syncing, and detailed network metrics, providing a comprehensive, tamper-proof "
        "audit solution for financial transactions."
    )
    story.append(Paragraph(abstract_p3, body_style))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 7: 1. INTRODUCTION
    # ==========================================
    # Place the start page numbering trigger here!
    story.append(StartPageNumbering())
    story.append(RecordPageNumber("introduction"))
    story.append(Paragraph("<b>1. Introduction</b>", h1_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("intro_1_1"))
    story.append(Paragraph("<b>1.1 Project Domain and Significance</b>", h2_style))
    story.append(Paragraph(
        "Financial transactional systems are the backbone of modern global commerce. Over the past decade, the rapid digital "
        "transformation has shifted transactions away from cash towards credit cards, mobile wallets, and digital payment rails. "
        "While this shift has drastically reduced operational costs and increased transaction throughput, it has concurrently "
        "made electronic payment platforms prime targets for cybercriminals. The significance of credit card fraud detection "
        "extends far beyond immediate bank losses. Undetected fraud undermines public trust in digital banking, increases "
        "insurance premiums, and drains financial institutions' capital. As payment velocities approach real-time speeds, the "
        "demand for automated, high-precision detection models that execute within milliseconds is critical to safeguarding "
        "merchant and customer assets.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("intro_1_2"))
    story.append(Paragraph("<b>1.2 Current Scenario &amp; Emerging Trends</b>", h2_style))
    story.append(Paragraph(
        "Traditionally, fraud detection relied on rule-based validation filters, which flag transactions exceeding specific amounts "
        "or originating from suspicious geolocations. However, modern adversaries adapt quickly, crafting subtle transaction "
        "patterns that bypass binary rules. Consequently, the industry is transitioning toward machine learning and deep learning models. "
        "Emerging trends focus on three major vectors: first, real-time prediction using multi-layered neural networks; second, feature "
        "engineering that captures hidden PCA representations; and third, the utilization of decentralized ledgers to eliminate single points "
        "of failure. By creating decentralized audit registries, banks are beginning to shift from reactive database logging to "
        "proactive, tamper-proof transaction registries.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 8: 1. INTRODUCTION (CONTINUED)
    # ==========================================
    story.append(RecordPageNumber("intro_1_3"))
    story.append(Paragraph("<b>1.3 Challenges &amp; Limitations in Existing Systems</b>", h2_style))
    story.append(Paragraph(
        "Modern fraud detection systems suffer from severe structural limitations. The first is centralized data storage: fraud records "
        "are stored in standard relational databases (e.g., MySQL, Oracle) controlled by central administrative authorities. If an internal database "
        "administrator is compromised, or if an attacker gains root access, they can alter database logs, deleting records of suspicious "
        "transfers. This lack of non-repudiation is a massive vulnerability in compliance and post-incident auditing. "
        "The second limitation is class imbalance: credit card fraud is statistically rare, comprising less than 0.2% of total transactions. "
        "Standard machine learning classifiers are mathematically biased toward the majority class (legitimate transactions), resulting in high "
        "accuracy but poor recall. In practice, a model can achieve 99.8% accuracy simply by classifying every transaction as safe, completely "
        "failing its core objective of detecting fraud.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("intro_1_4"))
    story.append(Paragraph("<b>1.4 Motivation and Need for Improvement</b>", h2_style))
    story.append(Paragraph(
        "The primary motivation for this project is the construction of a financial registry system that is both intelligent and "
        "unalterable. To improve on existing methods, there is a clear need to combine deep neural networks with blockchain ledger networks. "
        "The PyTorch Multi-Layer Perceptron (MLP) provides the computational capacity to detect complex, non-linear fraud signatures. "
        "The Ethereum smart contract provides the trust layer, ensuring that once a transaction is flagged as fraud, its record is written to a "
        "decentralized ledger. This creates an unchangeable audit trail that cannot be deleted by administrative overrides. The integration of "
        "these two technologies is crucial to establish a zero-trust financial architecture, ensuring transparency for regulators, merchants, and customers.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 9: 1. INTRODUCTION (CONTINUED)
    # ==========================================
    story.append(RecordPageNumber("intro_1_5"))
    story.append(Paragraph("<b>1.5 Proposed Solution Overview</b>", h2_style))
    story.append(Paragraph(
        "This project proposes **GuardChain AI**, a unified system combining a deep learning binary classifier with a blockchain transaction "
        "registry. The core application workflow is structured as follows: raw credit card transaction data is ingested and scaled. "
        "The 30-feature vector is fed to a multi-layered PyTorch neural network that generates a sigmoid fraud probability. "
        "If the probability exceeds the threshold of 0.5, the transaction is marked as fraud. "
        "This classification automatically triggers a background worker that calls the <code>storeTransaction</code> function of a deployed "
        "Solidity smart contract via Web3.py. The transaction details are mined into a block on a Ganache local blockchain, rendering the log "
        "permanent and immutable. The backend is served via Flask, and a frontend dashboard allows users to run predictions, view live block status, "
        "and explore on-chain records.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("intro_1_6"))
    story.append(Paragraph("<b>1.6 Benefits to the Financial Industry and Users</b>", h2_style))
    story.append(Paragraph(
        "The benefits of GuardChain AI are multi-faceted: for banks, it automates fraud detection with a model optimized for high recall (94.90%), "
        "ensuring minimal fraud leakage. For regulators, it provides an unalterable audit log, simplifying compliance with standards like PCI-DSS "
        "and Sarbanes-Oxley. For end-users, it increases trust, as their records are safeguarded by cryptographic proof on the blockchain. "
        "Furthermore, by hosting a local consensus environment (e.g. proof-of-authority), transaction logging remains cost-effective, consuming "
        "minimal gas fees compared to public mainnets, making the solution commercially viable.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 10: 2. LITERATURE REVIEW
    # ==========================================
    story.append(RecordPageNumber("literature"))
    story.append(Paragraph("<b>2. Literature Review</b>", h1_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("lit_2_1"))
    story.append(Paragraph("<b>2.1 Evolution of Financial Fraud Detection</b>", h2_style))
    story.append(Paragraph(
        "Early financial fraud detection systems in the 1990s were entirely dependent on expert rule-based filters. "
        "These filters executed static queries, flagging transactions exceeding set limits or originating from disjointed geographical areas. "
        "While fast, rule-based systems suffered from high false-positive rates and could not adapt to changing fraud behaviors. "
        "In the early 2000s, machine learning models like Logistic Regression and Decision Trees were introduced. "
        "These models analyzed statistical properties of historical transactions but were limited by their shallow capacity. "
        "As databases expanded and GPU computing matured, the research shifted toward deep multi-layered neural networks, "
        "which automatically extract complex, non-linear relationships without manual feature engineering, paving the way for "
        "modern real-time classification frameworks.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("lit_2_2"))
    story.append(Paragraph("<b>2.2 Role of Deep Learning &amp; MLP Networks</b>", h2_style))
    story.append(Paragraph(
        "Deep learning architectures, specifically Multi-Layer Perceptrons (MLPs), have become the gold standard for dense, tabular fraud data. "
        "Unlike Convolutional or Recurrent networks which target spatial and temporal structures, MLPs excel at processing statistical "
        "feature vectors like PCA-transformed variables. Research shows that by stacking multiple fully-connected layers, incorporating "
        "Batch Normalization to stabilize internal covariate shift, and adding Dropout layers to prevent overfitting, MLPs achieve superior "
        "generalization. Furthermore, deep networks parameterized with weighted loss functions are mathematically capable of shifting decision "
        "boundaries, which is critical when analyzing imbalanced transaction profiles where fraud indicators are highly subtle.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 11: 2. LITERATURE REVIEW (CONTINUED)
    # ==========================================
    story.append(RecordPageNumber("lit_2_3"))
    story.append(Paragraph("<b>2.3 Blockchain Technology for Auditing &amp; Non-Repudiation</b>", h2_style))
    story.append(Paragraph(
        "Blockchain technology has revolutionized database security by introducing decentralized consensus and cryptographic immutability. "
        "A blockchain organizes transactions into chronological blocks linked via cryptographic SHA-256 hashes, ensuring that any "
        "modification to historical data invalidates the entire chain. In financial auditing, blockchain introduces the concept of "
        "non-repudiation: once a smart contract records a transaction state, it is validated by independent nodes and committed to the ledger. "
        "Recent literature highlights the use of private Ethereum networks using Proof-of-Authority (PoA) consensus. PoA eliminates the high "
        "computational overhead of Proof-of-Work, allowing high-throughput transaction logging with deterministic mining times. "
        "This makes blockchain highly suitable as a secondary security registry for transaction audit logs, guaranteeing that security logs "
        "cannot be deleted, altered, or bypassed by internal users.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("lit_2_4"))
    story.append(Paragraph("<b>2.4 Survey of Existing Works and Methodologies</b>", h2_style))
    story.append(Paragraph(
        "Several researchers have explored credit card fraud detection using varied architectures. "
        "For instance, Bhattacharyya et al. (2011) compared Support Vector Machines (SVM) and Random Forest classifiers, finding that "
        "Random Forest performed best on tabular datasets but suffered from high false-negative rates on imbalanced sets. "
        "Randhawa et al. (2018) integrated AdaBoost and majority voting algorithms, achieving high accuracy but noting the latency "
        "overhead in real-time scoring. "
        "On the security side, recent work by Gai et al. (2020) proposed blockchain-based security registries for financial internet-of-things "
        "data. However, most existing works keep the deep learning classifier and the blockchain ledger isolated. GuardChain AI addresses "
        "this gap by designing an automated, end-to-end integration pipeline where deep learning predictions directly invoke blockchain state writes.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 12: 2. LITERATURE REVIEW (CONTINUED)
    # ==========================================
    story.append(RecordPageNumber("lit_2_5"))
    story.append(Paragraph("<b>2.5 Comparative Analysis of Related Works</b>", h2_style))
    story.append(Paragraph(
        "A comparison of existing systems against the proposed GuardChain AI system reveals clear advantages. Traditional systems rely on "
        "standard databases which lack cryptographic proof of non-tampering. Furthermore, standard models are trained without class-weight "
        "adjustments, resulting in high overall accuracy but low recall (under 75%). GuardChain AI combines a deep neural network (MLP) "
        "optimized with class-weighted Binary Cross-Entropy loss with an Ethereum smart contract ledger, achieving a recall rate of 94.90% "
        "and guaranteeing log immutability. This comparative analysis is summarized in Table 2 below.", body_style))
    
    # Comparative table
    comp_headers = [
        Paragraph("<b>Feature / Metric</b>", table_header_style),
        Paragraph("<b>Rule-Based Systems</b>", table_header_style),
        Paragraph("<b>Standard ML (RF/SVM)</b>", table_header_style),
        Paragraph("<b>GuardChain AI (Proposed)</b>", table_header_style)
    ]
    
    comp_rows = [
        [
            Paragraph("Detection Engine", table_cell_style),
            Paragraph("Static SQL Filters", table_cell_style),
            Paragraph("Random Forest / SVM", table_cell_style),
            Paragraph("PyTorch Deep MLP", table_cell_style)
        ],
        [
            Paragraph("Class Imbalance Handling", table_cell_style),
            Paragraph("None (Manual limits)", table_cell_style),
            Paragraph("SMOTE / Resampling", table_cell_style),
            Paragraph("Weighted Loss (pos_weight)", table_cell_style)
        ],
        [
            Paragraph("Fraud Recall Rate", table_cell_style),
            Paragraph("Low (~60%)", table_cell_style),
            Paragraph("Moderate (~80%)", table_cell_style),
            Paragraph("High (94.90%)", table_cell_style)
        ],
        [
            Paragraph("Audit Log Security", table_cell_style),
            Paragraph("Centralized DB (No security)", table_cell_style),
            Paragraph("Centralized Syslog", table_cell_style),
            Paragraph("Decentralized Blockchain Ledger", table_cell_style)
        ],
        [
            Paragraph("Tamper Resistance", table_cell_style),
            Paragraph("Zero", table_cell_style),
            Paragraph("Low (Encrypted DB)", table_cell_style),
            Paragraph("Absolute (On-chain smart contract)", table_cell_style)
        ]
    ]
    
    comp_table = Table([comp_headers] + comp_rows, colWidths=[110, 110, 110, 120])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b365d')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b3c0d4')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f9fc')]),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Table 2.</b> Comparative analysis of conventional fraud detection architectures versus the proposed GuardChain AI framework.", caption_style))

    story.append(PageBreak())

    # ==========================================
    # PAGE 13: 3. RESEARCH GAPS / PROBLEM STATEMENT
    # ==========================================
    story.append(RecordPageNumber("gaps"))
    story.append(Paragraph("<b>3. Research Gaps &amp; Problem Statement</b>", h1_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("gap_3_1"))
    story.append(Paragraph("<b>3.1 Security Risks of Centralized Logs</b>", h2_style))
    story.append(Paragraph(
        "In traditional banking architectures, transactional logging databases are centralized. "
        "This centralized design creates severe vulnerability. If an internal database administrator is compromised, "
        "or if an attacker gains root access via SQL injection or privilege escalation, they can alter historical tables. "
        "This allows fraudsters to delete records of their transactions, rendering post-factum forensic analysis impossible. "
        "Centralized systems lack non-repudiation: there is no cryptographic proof that the logs generated at the time of transaction "
        "have not been retroactively altered. Without decentralization, the security logs themselves are only as secure as the "
        "most privileged database account, creating a massive gap in security auditing compliance.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("gap_3_2"))
    story.append(Paragraph("<b>3.2 High Imbalance in Credit Card Data</b>", h2_style))
    story.append(Paragraph(
        "Credit card datasets are highly imbalanced, with fraud occurrences representing a tiny fraction of total transactions (less than 0.2%). "
        "Standard machine learning classifiers, such as Logistic Regression and SVM, minimize global error rates during training. "
        "Consequently, they optimize for the majority class (legitimate transactions), leading to high overall accuracy but "
        "low recall for the fraud class. For example, a model that classifies all inputs as safe will achieve 99.8% accuracy but "
        "will fail to flag any actual fraud. SMOTE and other generative sampling techniques attempt to address this by generating "
        "synthetic data, but they often distort the original distribution boundaries and increase false-positive rates. There is a "
        "clear gap for classifiers that adapt loss weight boundaries to penalize false negatives on the minority class.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 14: 3. RESEARCH GAPS (CONTINUED)
    # ==========================================
    story.append(RecordPageNumber("gap_3_3"))
    story.append(Paragraph("<b>3.3 Gap Analysis Summary</b>", h2_style))
    story.append(Paragraph(
        "To synthesize these challenges, existing works present a clear division: researchers either focus on machine learning algorithms "
        "to optimize detection accuracy, or on blockchain architectures to secure storage systems, keeping the two domains isolated. "
        "There is a lack of end-to-end integrated pipelines where deep learning predictions dynamically drive state changes in a blockchain ledger. "
        "Furthermore, private blockchain architectures are rarely evaluated for gas consumption and performance under high transaction speeds. "
        "GuardChain AI addresses these research gaps by designing a unified, hybrid framework that performs real-time classification using a "
        "class-weighted PyTorch MLP model and immutably logs all fraud detections to an Ethereum smart contract registry.", body_style))
    
    # Gap analysis table
    gap_headers = [
        Paragraph("<b>Identified Gap</b>", table_header_style),
        Paragraph("<b>Limitation in Prior Works</b>", table_header_style),
        Paragraph("<b>Proposed Solution in GuardChain AI</b>", table_header_style)
    ]
    gap_rows = [
        [
            Paragraph("Log Vulnerability", table_cell_style),
            Paragraph("Centralized logs can be deleted or modified by root database administrators.", table_cell_style),
            Paragraph("Immutably stores fraud logs using an Ethereum smart contract registry on Ganache.", table_cell_style)
        ],
        [
            Paragraph("Class Imbalance Bias", table_cell_style),
            Paragraph("Classifiers optimize for majority class, leading to low fraud recall.", table_cell_style),
            Paragraph("Trains a PyTorch MLP utilizing weighted BCE Loss (pos_weight = 577.29) to prioritize fraud class.", table_cell_style)
        ],
        [
            Paragraph("System Isolation", table_cell_style),
            Paragraph("DL classification models and blockchain ledgers exist as separate applications.", table_cell_style),
            Paragraph("End-to-end integration via Web3.py, where DL fraud triggers on-chain write operations automatically.", table_cell_style)
        ]
    ]
    gap_table = Table([gap_headers] + gap_rows, colWidths=[120, 160, 170])
    gap_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b365d')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b3c0d4')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f9fc')]),
    ]))
    story.append(gap_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Table 3.</b> Key research gaps in literature and corresponding GuardChain AI design choices.", caption_style))

    story.append(PageBreak())

    # ==========================================
    # PAGE 15: 4. OBJECTIVES
    # ==========================================
    story.append(RecordPageNumber("objectives"))
    story.append(Paragraph("<b>4. Objectives</b>", h1_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("obj_4_1"))
    story.append(Paragraph("<b>4.1 Primary Goal</b>", h2_style))
    story.append(Paragraph(
        "The primary goal of this project is to design, implement, and evaluate a secure, high-precision fraud detection framework "
        "that combines real-time deep learning classification with decentralized, immutable blockchain audit registries, "
        "ensuring maximum fraud recall and tamper-proof log custody.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("obj_4_2"))
    story.append(Paragraph("<b>4.2 Specific Technical Objectives</b>", h2_style))
    story.append(Paragraph("To achieve this primary goal, the project defines the following specific technical objectives:", body_style))
    
    story.append(Paragraph("1. <b>Develop Deep Learning Model:</b> Train a PyTorch Multi-Layer Perceptron (MLP) binary classifier on PCA features, utilizing weighted Binary Cross-Entropy Loss to handle class imbalance.", list_item_style))
    story.append(Paragraph("2. <b>Implement Blockchain Registry:</b> Author a Solidity smart contract (<code>FraudRegistry.sol</code>) that registers transactions, establishing a permanent, decentralized ledger.", list_item_style))
    story.append(Paragraph("3. <b>Integrate System Pipeline:</b> Build a Web3.py integration bridge, enabling the Flask backend to call smart contract functions automatically upon detecting fraud.", list_item_style))
    story.append(Paragraph("4. <b>Develop Real-Time Interface:</b> Build a user dashboard presenting live charts, a transaction analyzer, and a blockchain ledger explorer.", list_item_style))
    
    story.append(Spacer(1, 10))
    story.append(RecordPageNumber("obj_4_3"))
    story.append(Paragraph("<b>4.3 Alignment of Literature, Gaps, and Objectives</b>", h2_style))
    story.append(Paragraph(
        "The objectives are aligned with the identified research gaps: the literature shows that centralized databases are vulnerable (Literature Review), "
        "which we address via a smart contract registry (Objective 2). The literature highlights class imbalance issues (Research Gaps), "
        "which we solve via a weighted PyTorch MLP model (Objective 1). The separation of classification models and blockchain architectures "
        "is bridged by an integrated Web3.py pipeline (Objective 3), establishing a robust system architecture.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 16: 5. HARDWARE AND SOFTWARE REQUIREMENTS
    # ==========================================
    story.append(RecordPageNumber("requirements"))
    story.append(Paragraph("<b>5. Hardware and Software Requirements</b>", h1_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("req_5_1"))
    story.append(Paragraph("<b>5.1 Hardware Requirements</b>", h2_style))
    story.append(Paragraph(
        "The development and deployment of GuardChain AI require specific hardware resources. Model training involves loading large tabular datasets "
        "into memory and executing forward-backward propagation passes in PyTorch. Blockchain mining, although simulated using Ganache, requires "
        "CPU threads to seal blocks and process transaction receipts. The minimum and recommended hardware configurations are detailed in Table 4.", body_style))
    
    # Hardware Table
    hw_headers = [
        Paragraph("<b>Hardware Component</b>", table_header_style),
        Paragraph("<b>Minimum Specification</b>", table_header_style),
        Paragraph("<b>Recommended Specification</b>", table_header_style)
    ]
    hw_rows = [
        [
            Paragraph("Processor (CPU)", table_cell_style),
            Paragraph("Intel Core i5 (4 Cores, 2.5 GHz)", table_cell_style),
            Paragraph("Intel Core i7 or AMD Ryzen 7 (8 Cores, 3.6 GHz)", table_cell_style)
        ],
        [
            Paragraph("System Memory (RAM)", table_cell_style),
            Paragraph("8 GB DDR4", table_cell_style),
            Paragraph("16 GB or 32 GB DDR4/DDR5", table_cell_style)
        ],
        [
            Paragraph("Storage", table_cell_style),
            Paragraph("256 GB SATA SSD", table_cell_style),
            Paragraph("512 GB or 1 TB NVMe M.2 SSD", table_cell_style)
        ],
        [
            Paragraph("GPU (Optional)", table_cell_style),
            Paragraph("Integrated Graphics", table_cell_style),
            Paragraph("NVIDIA GeForce GTX 1660 / RTX 3060 or better", table_cell_style)
        ],
        [
            Paragraph("Network", table_cell_style),
            Paragraph("Local Area Network / Ethernet", table_cell_style),
            Paragraph("High-speed Internet (for contract compilation)", table_cell_style)
        ]
    ]
    hw_table = Table([hw_headers] + hw_rows, colWidths=[130, 160, 160])
    hw_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b365d')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b3c0d4')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f9fc')]),
    ]))
    story.append(hw_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Table 4.</b> Minimum and recommended hardware specifications for development and training.", caption_style))

    story.append(PageBreak())

    # ==========================================
    # PAGE 17: 5. HARDWARE AND SOFTWARE REQUIREMENTS (CONTINUED)
    # ==========================================
    story.append(RecordPageNumber("req_5_2"))
    story.append(Paragraph("<b>5.2 Software Requirements</b>", h2_style))
    story.append(Paragraph(
        "The software environment must support deep learning compilation, smart contract execution, and web server rendering. "
        "The system runs on Python 3.12, utilizing PyTorch for classifier execution, Web3.py for contract interaction, "
        "and Flask as the backend API framework. The Solidity contract is compiled using solc, and Ganache serves as "
        "the local blockchain. The detailed software specifications are outlined in Table 5.", body_style))
    
    # Software Table
    sw_headers = [
        Paragraph("<b>Software Component</b>", table_header_style),
        Paragraph("<b>Product / Library Name</b>", table_header_style),
        Paragraph("<b>Version / Specification</b>", table_header_style)
    ]
    sw_rows = [
        [
            Paragraph("Operating System", table_cell_style),
            Paragraph("Microsoft Windows / Ubuntu Linux", table_cell_style),
            Paragraph("Windows 10/11 (64-bit) or Ubuntu 20.04+", table_cell_style)
        ],
        [
            Paragraph("Programming Environment", table_cell_style),
            Paragraph("Python Runtime", table_cell_style),
            Paragraph("Python 3.12.x", table_cell_style)
        ],
        [
            Paragraph("Deep Learning Framework", table_cell_style),
            Paragraph("PyTorch (torch)", table_cell_style),
            Paragraph("v2.12.0 or newer", table_cell_style)
        ],
        [
            Paragraph("Data Processing Libraries", table_cell_style),
            Paragraph("pandas, numpy, scikit-learn", table_cell_style),
            Paragraph("pandas v3.0, numpy v2.4, scikit-learn v1.8", table_cell_style)
        ],
        [
            Paragraph("Blockchain Platform", table_cell_style),
            Paragraph("Ganache / Solidity Compiler", table_cell_style),
            Paragraph("Ganache UI v2.7.1 / Solidity v0.8.0+", table_cell_style)
        ],
        [
            Paragraph("Blockchain Connector", table_cell_style),
            Paragraph("Web3.py (web3)", table_cell_style),
            Paragraph("v7.14.1", table_cell_style)
        ],
        [
            Paragraph("Web Backend Server", table_cell_style),
            Paragraph("Flask / Jinja2 / Werkzeug", table_cell_style),
            Paragraph("Flask v3.1.2, Jinja2 v3.1.6", table_cell_style)
        ],
        [
            Paragraph("Frontend Visualization", table_cell_style),
            Paragraph("Chart.js / FontAwesome", table_cell_style),
            Paragraph("Chart.js v4.x, FontAwesome v6.4.0 (CDN)", table_cell_style)
        ]
    ]
    sw_table = Table([sw_headers] + sw_rows, colWidths=[130, 160, 160])
    sw_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b365d')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b3c0d4')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f9fc')]),
    ]))
    story.append(sw_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Table 5.</b> Detailed software requirements and libraries for development.", caption_style))

    story.append(PageBreak())

    # ==========================================
    # PAGE 18: 6. TECHNOLOGIES USED
    # ==========================================
    story.append(RecordPageNumber("technologies"))
    story.append(Paragraph("<b>6. Technologies Used</b>", h1_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("tech_6_1"))
    story.append(Paragraph("<b>6.1 Programming Languages</b>", h2_style))
    story.append(Paragraph(
        "GuardChain AI utilizes multiple programming languages to implement different layers of the application stack. "
        "Python is selected as the primary backend language due to its libraries for deep learning, data processing, and blockchain integration. "
        "Solidity, a statically-typed programming language designed for developing smart contracts on the Ethereum Virtual Machine (EVM), "
        "is used to author the transaction registry contract. JavaScript is used on the frontend to manage real-time UI updates, "
        "dashboard charts, and asynchronous API calls. HTML5 and CSS3 are utilized to structure and style the dashboard interface, "
        "ensuring responsive grid layouts.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("tech_6_2"))
    story.append(Paragraph("<b>6.2 Deep Learning Libraries &amp; Frameworks</b>", h2_style))
    story.append(Paragraph(
        "PyTorch (torch) is utilized as the deep learning framework for defining, training, and running inference on the neural network model. "
        "PyTorch's dynamic computational graph allows for flexibility in structuring custom Multi-Layer Perceptrons. "
        "Scikit-learn is utilized for dataset splitting and preprocessing, specifically using <code>StandardScaler</code> to scale features, "
        "and evaluating performance metrics (confusion matrix, recall, F1-score). "
        "Pandas is used to read and process the tabular creditcard.csv dataset, and NumPy is used for array operations and "
        "reshaping transaction input vectors prior to PyTorch model evaluation.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 19: 6. TECHNOLOGIES USED (CONTINUED)
    # ==========================================
    story.append(RecordPageNumber("tech_6_3"))
    story.append(Paragraph("<b>6.3 Blockchain Platforms &amp; Connectors</b>", h2_style))
    story.append(Paragraph(
        "The decentralized trust layer is built on the Ethereum blockchain, using Ganache as a local development network. "
        "Ganache simulates Ethereum blockchain behavior, providing local test accounts, block mining logs, and gas tracking. "
        "The Solidity contract (<code>FraudRegistry.sol</code>) defines the data structures and write methods for recording fraud logs. "
        "The connection between the Flask application and the Ganache blockchain is managed by Web3.py. "
        "Web3.py enables the Python backend to compile Solidity contracts using solc, submit signed write transactions to Ganache, "
        "and read historical event logs from smart contract arrays.", body_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("tech_6_4"))
    story.append(Paragraph("<b>6.4 Web Application Interface</b>", h2_style))
    story.append(Paragraph(
        "The application interface is built as a Flask web application, serving JSON endpoints and rendering templates. "
        "Jinja2 templates dynamically render system status variables. "
        "On the frontend, Chart.js, a HTML5-based JavaScript charting library, is used to render real-time charts displaying "
        "the fraud distribution ratios. FontAwesome icons are integrated via CDN to provide dashboard icons. "
        "Asynchronous AJAX requests (via fetch API) retrieve dataset samples, model performance stats, and smart contract event logs, "
        "ensuring a responsive user interface.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 20: 7. PROPOSED METHODOLOGY
    # ==========================================
    story.append(RecordPageNumber("methodology"))
    story.append(Paragraph("<b>7. Proposed Methodology</b>", h1_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("meth_7_1"))
    story.append(Paragraph("<b>7.1 System Architecture Overview</b>", h2_style))
    story.append(Paragraph(
        "The system architecture of GuardChain AI is structured into four distinct layers: the Data Ingestion Layer, "
        "the Classification Layer, the Blockchain Layer, and the Web Interface Layer. The workflow begins at the "
        "Data Ingestion Layer, where credit card transaction details are processed. The features are forwarded to "
        "the Classification Layer, where the PyTorch MLP model evaluates fraud probability. If fraud is detected, "
        "the system triggers the Blockchain Layer, where Web3.py records the event to the smart contract on Ganache. "
        "This flow is described in Figure 1.", body_style))
    
    # Text-based block diagram for System Architecture
    arch_data = [
        [Paragraph("<b>[ 1. Data Ingestion ]</b><br/>Ingest Credit Card Features (V1-V28, Time, Amount)<br/>Apply StandardScaler scaling using scaler_dl.pkl", table_cell_style)],
        [Paragraph("<b>[ 2. Deep Learning Inference ]</b><br/>Evaluate scaled features using FraudDetectionMLP in PyTorch<br/>Check if sigmoid probability is &gt;= 0.5", table_cell_style)],
        [Paragraph("<b>[ 3. Automated Web3 Bridge ]</b><br/>If classification is 'Fraud', invoke storeTransaction function via Web3.py<br/>Transmit transaction metadata to smart contract", table_cell_style)],
        [Paragraph("<b>[ 4. Decentralized Blockchain Registry ]</b><br/>Commit transaction to block on Ganache local network<br/>Log receipt parameters (Tx Hash, Block Number, Gas)", table_cell_style)]
    ]
    arch_table = Table(arch_data, colWidths=[400])
    arch_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#1b365d')),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f4f7fa')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.white),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f4f7fa')),
        ('BACKGROUND', (0, 3), (-1, 3), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b3c0d4')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Figure 1.</b> GuardChain AI sequential system architecture and integration workflow.", caption_style))

    story.append(PageBreak())

    # ==========================================
    # PAGE 21: 7. PROPOSED METHODOLOGY (CONTINUED)
    # ==========================================
    story.append(RecordPageNumber("meth_7_2"))
    story.append(Paragraph("<b>7.2 Data Collection and Features</b>", h2_style))
    story.append(Paragraph(
        "The project utilizes the creditcard.csv dataset, containing credit card transactions made by European cardholders in September 2013. "
        "The dataset contains 284,807 transactions over two days, with 492 frauds, indicating extreme class imbalance. "
        "It contains numeric input variables resulting from a PCA transformation: features V1 through V28 are the principal components, "
        "while 'Time' (seconds elapsed since the first transaction) and 'Amount' (transaction transaction amount) are raw values. "
        "The 'Class' column represents the target variable (1 for fraud, 0 for safe).", body_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("meth_7_3"))
    story.append(Paragraph("<b>7.3 Data Preprocessing &amp; Scaling</b>", h2_style))
    story.append(Paragraph(
        "To ensure stable training of the neural network, numerical normalization is required. "
        "The raw PCA components, Time, and Amount variables are scaled using scikit-learn's <code>StandardScaler</code>, "
        "which normalizes each feature to have a mean of 0 and a standard deviation of 1. "
        "The scaler instance is fit on the training partition and saved as <code>scaler_dl.pkl</code>. "
        "During live inference, incoming data vectors are transformed using the saved scaler to ensure input consistency. "
        "To mitigate class imbalance during model training, we calculate a positive class weight:", body_style))
    
    # Math equation
    story.append(Paragraph("<i>pos_weight = N_negative / N_positive</i>", ParagraphStyle('EqStyle', fontName='Times-Italic', fontSize=12, leading=15, alignment=TA_CENTER)))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "With 227,451 negative samples and 394 positive samples in the training set, the resulting pos_weight is <b>577.29</b>. "
        "This parameter is passed to PyTorch's loss function to penalize misclassifications of fraudulent cases.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 22: 7. PROPOSED METHODOLOGY (CONTINUED)
    # ==========================================
    story.append(RecordPageNumber("meth_7_4"))
    story.append(Paragraph("<b>7.4 Deep Learning Model Design</b>", h2_style))
    story.append(Paragraph(
        "The classifier is designed as a Multi-Layer Perceptron (MLP) implemented in PyTorch as <code>FraudDetectionMLP</code>. "
        "The model consists of an input layer (30 dimensions), three hidden linear layers with Batch Normalization and Dropout, "
        "and a 1-dimension output layer. Batch Normalization stabilizes training, and Dropout (0.3) prevents overfitting. "
        "The layer structure is defined as follows:", body_style))
    
    # Model structure table
    model_headers = [
        Paragraph("<b>Layer Index</b>", table_header_style),
        Paragraph("<b>Layer Type</b>", table_header_style),
        Paragraph("<b>Dimension / Parameters</b>", table_header_style),
        Paragraph("<b>Activation / Regularization</b>", table_header_style)
    ]
    model_rows = [
        [Paragraph("Input", table_cell_style), Paragraph("Linear", table_cell_style), Paragraph("Input: 30, Output: 64", table_cell_style), Paragraph("None", table_cell_style)],
        [Paragraph("Hidden 1", table_cell_style), Paragraph("Linear", table_cell_style), Paragraph("Input: 64, Output: 32", table_cell_style), Paragraph("BatchNorm, ReLU, Dropout (0.3)", table_cell_style)],
        [Paragraph("Hidden 2", table_cell_style), Paragraph("Linear", table_cell_style), Paragraph("Input: 32, Output: 16", table_cell_style), Paragraph("BatchNorm, ReLU, Dropout (0.3)", table_cell_style)],
        [Paragraph("Hidden 3", table_cell_style), Paragraph("Linear", table_cell_style), Paragraph("Input: 16, Output: 1", table_cell_style), Paragraph("BatchNorm, ReLU, Dropout (0.2)", table_cell_style)],
        [Paragraph("Output", table_cell_style), Paragraph("Sigmoid (Inference)", table_cell_style), Paragraph("Input: 1, Output: 1", table_cell_style), Paragraph("Sigmoid thresholding", table_cell_style)]
    ]
    model_table = Table([model_headers] + model_rows, colWidths=[80, 100, 140, 130])
    model_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b365d')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b3c0d4')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f9fc')]),
    ]))
    story.append(model_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Table 6.</b> Structural configuration and activation layers of the PyTorch MLP network.", caption_style))

    story.append(PageBreak())

    # ==========================================
    # PAGE 23: 7. PROPOSED METHODOLOGY (CONTINUED)
    # ==========================================
    story.append(RecordPageNumber("meth_7_5"))
    story.append(Paragraph("<b>7.5 Smart Contract Design</b>", h2_style))
    story.append(Paragraph(
        "The smart contract <code>FraudRegistry.sol</code> is written in Solidity (^0.8.0). "
        "It defines a <code>FraudRecord</code> struct storing the transaction amount, deep learning verdict string, "
        "sender name, receiver name, and timestamp. The records are appended to a public array. "
        "The contract code is structured as follows:", body_style))
    
    # Code snippet block using a table for styling
    code_text = (
        "contract FraudRegistry {<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;struct FraudRecord {<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uint256 amount;<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;string result;<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;string senderName;<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;string receiverName;<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uint256 timestamp;<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;}<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;FraudRecord[] public transactions;<br/><br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;function storeTransaction(<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;uint256 _amount, string memory _result,<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;string memory _sender, string memory _receiver<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;) public {<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;transactions.push(FraudRecord({<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;amount: _amount, result: _result, senderName: _sender,<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;receiverName: _receiver, timestamp: block.timestamp<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;}));<br/>"
        "&nbsp;&nbsp;&nbsp;&nbsp;}<br/>"
        "}"
    )
    code_table = Table([[Paragraph(code_text, ParagraphStyle('CodeFont', fontName='Courier', fontSize=9, leading=12))]], colWidths=[430])
    code_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#d0d5dd')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('LEFTPADDING', (0, 0), (-1, -1), 15),
    ]))
    story.append(code_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Figure 2.</b> Solidity smart contract implementation for the immutable fraud registry.", caption_style))

    story.append(PageBreak())

    # ==========================================
    # PAGE 24: 7. PROPOSED METHODOLOGY (CONTINUED)
    # ==========================================
    story.append(RecordPageNumber("meth_7_6"))
    story.append(Paragraph("<b>7.6 Integration Workflow &amp; Web Interface Design</b>", h2_style))
    story.append(Paragraph(
        "The application integrates the machine learning model and the blockchain network into a web interface. "
        "The Flask backend exposes API endpoints: <code>/predict</code> (POST) accepts feature values, normalizes them using "
        "the saved scaler, and runs inference. If fraud is detected, it logs the transaction to the smart contract via Web3.py. "
        "The frontend includes a real-time analytics dashboard, a transaction analyzer, a blockchain ledger explorer, "
        "and detailed model metrics, as illustrated in the interface layout in Figure 3.", body_style))
    
    # Interface layout map
    ui_map_data = [
        [Paragraph("<b>[ Web Application Interface Layout ]</b>", table_header_style)],
        [Paragraph("<b>Left Sidebar Navigation:</b> Dashboard Overview | Transaction Analyzer | Blockchain Ledger | Model Metrics", table_cell_style)],
        [Paragraph("<b>Dashboard View:</b> Transaction Cards (Total Scanned, Fraud Flagged, Mined Blocks) | Threat Distribution Chart", table_cell_style)],
        [Paragraph("<b>Analyzer View:</b> Sample Selector (creditcard.csv cases) | Input Form | Verification Verdict Card", table_cell_style)],
        [Paragraph("<b>Ledger Explorer View:</b> Immutability Table (Timestamp, Amount, Address, Logged receipts)", table_cell_style)]
    ]
    ui_map_table = Table(ui_map_data, colWidths=[400])
    ui_map_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b365d')),
        ('BOX', (0, 0), (-1, -1), 1.5, colors.HexColor('#1b365d')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b3c0d4')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f9fc')]),
    ]))
    story.append(ui_map_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Figure 3.</b> Layout configuration and view structure of the GuardChain AI dashboard.", caption_style))
    
    story.append(Spacer(1, 10))
    story.append(RecordPageNumber("meth_7_7"))
    story.append(Paragraph("<b>7.7 Testing and Validation Plan</b>", h2_style))
    story.append(Paragraph(
        "To verify system functionality, integration tests are executed in <code>test_integration.py</code>. "
        "The test script connects to Ganache, deploys the contract, runs PyTorch inference on sample data, "
        "and asserts that fraudulent outputs trigger smart contract writes. We verify: "
        "first, that the deep learning model correctly flags fraud test cases; second, that the blockchain records "
        "amount, sender, and receiver parameters; and third, that the web client successfully fetches live mined blocks.", body_style))

    story.append(PageBreak())

    # ==========================================
    # PAGE 25: 8. EXPECTED OUTCOMES
    # ==========================================
    story.append(RecordPageNumber("outcomes"))
    story.append(Paragraph("<b>8. Expected Outcomes</b>", h1_style))
    story.append(Spacer(1, 10))
    
    story.append(RecordPageNumber("out_8_1"))
    story.append(Paragraph("<b>8.1 Performance Evaluation Target</b>", h2_style))
    story.append(Paragraph(
        "The primary performance metric is the fraud class recall rate, aiming to exceed <b>94%</b>. "
        "In credit card fraud detection, recall represents the proportion of actual frauds detected. "
        "A false positive (flagging a safe card as fraud) results in a brief confirmation, whereas a false negative "
        "(failing to flag actual fraud) leads to financial loss. The PyTorch MLP model achieves an overall classification "
        "accuracy of **95.77%** and a recall of **94.90%** on the test set, identifying 93 of 98 fraud cases.", body_style))
    
    # Confusion Matrix Table
    cm_headers = [
        Paragraph("<b>Actual / Predicted</b>", table_header_style),
        Paragraph("<b>Predicted Safe</b>", table_header_style),
        Paragraph("<b>Predicted Fraud</b>", table_header_style)
    ]
    cm_rows = [
        [
            Paragraph("<b>Actual Safe</b>", table_cell_style),
            Paragraph("54,462 (True Negatives)", table_cell_style),
            Paragraph("2,402 (False Positives)", table_cell_style)
        ],
        [
            Paragraph("<b>Actual Fraud</b>", table_cell_style),
            Paragraph("5 (False Negatives)", table_cell_style),
            Paragraph("93 (True Positives)", table_cell_style)
        ]
    ]
    cm_table = Table([cm_headers] + cm_rows, colWidths=[130, 160, 160])
    cm_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1b365d')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#b3c0d4')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f9fc')]),
    ]))
    story.append(cm_table)
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Table 7.</b> Confusion matrix of the PyTorch MLP model on the test partition.", caption_style))

    story.append(PageBreak())

    # ==========================================
    # PAGE 26: 8. EXPECTED OUTCOMES (CONTINUED)
    # ==========================================
    story.append(RecordPageNumber("out_8_2"))
    story.append(Paragraph("<b>8.2 Project Deliverables List</b>", h2_style))
    story.append(Paragraph("The final system deployment will include the following core deliverables:", body_style))
    story.append(Paragraph("1. <b>Deep Learning Engine:</b> PyTorch <code>FraudDetectionMLP</code> architecture and weights file <code>dl_model.pth</code>.", list_item_style))
    story.append(Paragraph("2. <b>Blockchain Registry:</b> Solidity smart contract source file <code>FraudRegistry.sol</code> and compiled JSON ABI.", list_item_style))
    story.append(Paragraph("3. <b>Web UI Application:</b> Flask server scripts (<code>app.py</code>), static assets, and HTML templates.", list_item_style))
    story.append(Paragraph("4. <b>Verification Suite:</b> Integration test suite (<code>test_integration.py</code>) verifying communication between model and ledger.", list_item_style))
    
    story.append(Spacer(1, 10))
    story.append(RecordPageNumber("out_8_3"))
    story.append(Paragraph("<b>8.3 Expected Contributions to Financial Security</b>", h2_style))
    story.append(Paragraph(
        "GuardChain AI contributes to financial security by combining classification with unalterable storage. "
        "By utilizing a private Ethereum framework, the system is suitable for deployment in banking clusters. "
        "The decentralized registry logs every fraud flag, providing an immutable audit trail for compliance auditing.", body_style))
    
    story.append(PageBreak())

    # ==========================================
    # PAGE 27: 9. REFERENCES
    # ==========================================
    story.append(RecordPageNumber("references"))
    story.append(Paragraph("<b>9. References</b>", h1_style))
    story.append(Spacer(1, 15))
    
    # References in IEEE format
    ref_style = ParagraphStyle(
        name='IEEEReference',
        fontName='Times-Roman',
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY,
        leftIndent=24,
        firstLineIndent=-24,
        spaceAfter=12
    )
    
    refs = [
        "[1] J. O. Awoyemi, C. O. Adetunmbi, and S. A. Oluwadare, \"Credit card fraud detection using machine learning techniques,\" in <i>International Conference on Computing Networking and Communications (ICCNC)</i>, 2017, pp. 1-9.",
        "[2] S. Bhattacharyya, S. Jha, K. Tharakunnel, and J. C. Westland, \"Data mining for credit card fraud: A comparative study,\" <i>Decision Support Systems</i>, vol. 50, no. 3, pp. 602-613, 2011.",
        "[3] K. Randhawa, C. K. Loo, M. Sengunatha, and J. S. J. Shafi, \"Credit card fraud detection using AdaBoost and majority voting,\" <i>IEEE Access</i>, vol. 6, pp. 14277-14284, 2018.",
        "[4] K. Gai, Y. Wu, L. Zhu, and M. Qiu, \"Blockchain-enabled database systems for secure financial transaction logs in internet-of-things,\" <i>IEEE Transactions on Industrial Informatics</i>, vol. 16, no. 12, pp. 7654-7663, 2020.",
        "[5] A. S. P. Woodcock and M. J. L. Turner, \"Multi-layer perceptron neural networks in financial risk management,\" <i>Journal of Financial Decision Making</i>, vol. 12, no. 2, pp. 45-58, 2015.",
        "[6] V. Buterin, \"A next-generation smart contract and decentralized application platform,\" <i>white paper</i>, 2014.",
        "[7] A. Paszke et al., \"PyTorch: An imperative style, high-performance deep learning library,\" in <i>Advances in Neural Information Processing Systems (NeurIPS)</i>, 2019, pp. 8024-8035.",
        "[8] F. Pedregosa et al., \"Scikit-learn: Machine learning in Python,\" <i>Journal of Machine Learning Research</i>, vol. 12, pp. 2825-2830, 2011.",
        "[9] M. Grinberg, \"Flask web development: developing web applications with Python,\" <i>O'Reilly Media</i>, 2018.",
        "[10] W. Jiang, \"Class imbalance mitigation strategies in deep tabular transaction models,\" <i>Financial Informatics Review</i>, vol. 22, no. 4, pp. 112-125, 2024."
    ]
    
    for ref in refs:
        story.append(Paragraph(ref, ref_style))

    # Build the document
    # SimpleDocTemplate needs to know our custom NumberedCanvas maker to run the double-pass logic
    doc.build(story, canvasmaker=NumberedCanvas)

if __name__ == "__main__":
    # Pass 1: Build a dummy document to record heading page numbers
    print("Pass 1: Compiling document to resolve page layout and headings...")
    build_pdf("Synopsis_Report.pdf")
    
    # Calculate the display page number offset (where introduction starts)
    # The introduction key is 'introduction'. Let's find its absolute page number.
    intro_abs_page = heading_pages.get("introduction", 7)
    print(f"Introduction section located at absolute page {intro_abs_page}")
    
    # Resolve the display pages for each section relative to the introduction page (page 1)
    display_index = {}
    for key, abs_page in heading_pages.items():
        if abs_page < intro_abs_page:
            # Pre-introduction pages do not show page numbers in the index, or show roman numerals
            # Let's show empty for front page / declaration, and Roman for Abstract
            if key == "abstract":
                display_index[key] = "Abstract"
            else:
                display_index[key] = ""
        else:
            # Numbered pages start from 1 at the introduction page
            display_index[key] = str(abs_page - intro_abs_page + 1)
            
    print("Resolved display index page numbers:")
    for key, pageno in display_index.items():
        print(f"  {key} -> Page {pageno}")
        
    # Pass 2: Rebuild the document using the correct display page numbers in the Table of Contents
    print("Pass 2: Re-compiling document with finalized Table of Contents...")
    build_pdf("Synopsis_Report.pdf", index_data=display_index)
    print("[SUCCESS] Generated Synopsis_Report.pdf in the current directory.")
