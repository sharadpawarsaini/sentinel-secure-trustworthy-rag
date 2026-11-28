"""Generate a concise 1-page SENTINEL Team Work Distribution & Folder Ownership PDF."""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)

OUTPUT_DIR = Path("docs/reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_PATH = OUTPUT_DIR / "SENTINEL_Team_Work_Distribution.pdf"

PRIMARY = colors.HexColor("#0F172A")
SECONDARY = colors.HexColor("#1E3A8A")
TEXT_DARK = colors.HexColor("#0F172A")
TEXT_MUTED = colors.HexColor("#475569")
BG_CARD = colors.HexColor("#F1F5F9")
BORDER = colors.HexColor("#CBD5E1")


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=34,
        rightMargin=34,
        topMargin=32,
        bottomMargin=32,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom", parent=styles["Heading1"],
        fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=PRIMARY, spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        "SubCustom", parent=styles["Normal"],
        fontName="Helvetica", fontSize=9.5, leading=13, textColor=TEXT_MUTED, spaceAfter=8,
    )
    h1_style = ParagraphStyle(
        "H1Custom", parent=styles["Heading2"],
        fontName="Helvetica-Bold", fontSize=11.5, leading=15, textColor=SECONDARY, spaceBefore=8, spaceAfter=5,
    )
    body_style = ParagraphStyle(
        "BodyCustom", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=TEXT_DARK, spaceAfter=3,
    )
    cell_style = ParagraphStyle(
        "CellCustom", parent=styles["Normal"],
        fontName="Helvetica", fontSize=8, leading=11, textColor=TEXT_DARK,
    )

    story = []
    story.append(Paragraph("SENTINEL — Team Work Distribution & Folder Ownership", title_style))
    story.append(Paragraph(
        "Brief Architecture & Module Ownership Reference for Sharad, Bhumika, Adhya & Anwesha (v0.4.0)",
        subtitle_style,
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=0, spaceAfter=8))

    story.append(Paragraph("1. Four-Member Module & Folder Ownership Matrix", h1_style))

    team_data = [
        [
            Paragraph("<b>Member &amp; Role</b>", cell_style),
            Paragraph("<b>Owned Folders &amp; Files</b>", cell_style),
            Paragraph("<b>Key Code Responsibilities</b>", cell_style),
        ],
        [
            Paragraph("<b>1. Bhumika</b><br/><i>RAG Foundation</i><br/><code>feature/rag</code>", cell_style),
            Paragraph(
                "<b>Core:</b> <code>sentinel/rag/</code><br/>"
                "• <code>document_loader.py</code><br/>"
                "• <code>chunker.py</code><br/>"
                "• <code>embedder.py</code><br/>"
                "• <code>vector_store.py</code><br/>"
                "• <code>generator.py</code><br/>"
                "<b>Tests:</b> <code>test_{document_loader, chunker, embedder, vector_store, generator, rag}.py</code>",
                cell_style,
            ),
            Paragraph(
                "• PDF, DOCX &amp; TXT text extraction and cleaning<br/>"
                "• Deterministic SHA-256 recursive chunking<br/>"
                "• Dense embeddings (<code>all-MiniLM-L6-v2</code> &amp; 384-d low-memory NumPy fallback)<br/>"
                "• Persistent ChromaDB HNSW cosine retrieval<br/>"
                "• Multi-LLM adapter (Gemini, Ollama, MockLLM)",
                cell_style,
            ),
        ],
        [
            Paragraph("<b>2. Adhya</b><br/><i>AI Security Engine</i><br/><code>feature/security</code>", cell_style),
            Paragraph(
                "<b>Core:</b> <code>sentinel/security/</code><br/>"
                "• <code>normalizer.py</code><br/>"
                "• <code>input_scanner.py</code><br/>"
                "• <code>document_scanner.py</code><br/>"
                "• <code>context_scanner.py</code><br/>"
                "• <code>egress_scanner.py</code><br/>"
                "<b>Tests:</b> <code>test_security_{input, poison, egress}.py</code>, <code>test_pipeline_security.py</code>",
                cell_style,
            ),
            Paragraph(
                "• Unicode NFKD, zero-width &amp; Base64/Hex de-obfuscation<br/>"
                "• <b>Barrier 1:</b> Direct prompt injection &amp; jailbreak blocker<br/>"
                "• Document upload poisoning scanner<br/>"
                "• <b>Barrier 3:</b> Indirect injection context quarantine<br/>"
                "• <b>Barrier 6:</b> API key, prompt leak &amp; beacon redactor",
                cell_style,
            ),
        ],
        [
            Paragraph("<b>3. Anwesha</b><br/><i>Trust, Hallucination &amp; NLI</i><br/><code>feature/trust</code>", cell_style),
            Paragraph(
                "<b>Core:</b> <code>sentinel/trust/</code><br/>"
                "• <code>claim_extractor.py</code><br/>"
                "• <code>confidence_scorer.py</code><br/>"
                "• <code>nli_verifier.py</code><br/>"
                "• <code>composite_scorer.py</code><br/>"
                "<b>Tests:</b> <code>test_trust_{nli, scorer}.py</code>, <code>test_pipeline_trust.py</code>",
                cell_style,
            ),
            Paragraph(
                "• Atomic propositional claim decomposition<br/>"
                "• Exponential-decay retrieval confidence scoring<br/>"
                "• Cross-encoder NLI (<code>nli-deberta-v3-small</code>) &amp; heuristic entailment/contradiction verification<br/>"
                "• <b>Barrier 5:</b> Weighted Composite Trust Score &amp; High/Med/Low decision gate",
                cell_style,
            ),
        ],
        [
            Paragraph("<b>4. Sharad</b><br/><i>Architecture, Mitigation, API &amp; UI</i><br/><code>feature/mitigation</code><br/><code>feature/integration</code>", cell_style),
            Paragraph(
                "<b>Core:</b> <code>sentinel/pipeline.py</code>, <code>config.py</code><br/>"
                "• <code>sentinel/mitigation/</code> (<code>reformulator.py</code>, <code>abstention.py</code>)<br/>"
                "• <code>sentinel/backend/</code> (<code>api.py</code>, <code>schemas.py</code>, <code>audit.py</code>)<br/>"
                "• <code>frontend/src/app/</code> (<code>page.tsx</code>, <code>admin/page.tsx</code>)<br/>"
                "• <code>scripts/</code>, <code>test_{api, mitigation, edge_cases}.py</code>",
                cell_style,
            ),
            Paragraph(
                "• Master 6-barrier closed-loop pipeline orchestrator<br/>"
                "• Adaptive query reformulation &amp; Principled Abstention<br/>"
                "• FastAPI REST endpoints &amp; circular audit logger<br/>"
                "• Next.js cyber-security portal, 6-barrier radar, claim matrix, sandbox &amp; Admin Console (<code>/admin</code>)<br/>"
                "• Render + Vercel deployment &amp; PDF reporting",
                cell_style,
            ),
        ],
    ]

    t_team = Table(team_data, colWidths=[105, 195, 244])
    t_team.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BG_CARD),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_team)
    story.append(Spacer(1, 10))

    story.append(Paragraph("2. End-to-End Flow Across Team Modules", h1_style))
    flow_text = (
        "<b>User Query</b> &rarr; "
        "<b>Adhya</b> (<code>input_scanner</code>) &rarr; "
        "<b>Bhumika</b> (<code>vector_store</code>) &rarr; "
        "<b>Adhya</b> (<code>context_scanner</code>) &rarr; "
        "<b>Bhumika</b> (<code>generator</code>) &rarr; "
        "<b>Anwesha</b> (<code>composite_scorer</code>) &rarr; "
        "<b>Sharad</b> (<code>mitigation</code> / <code>abstention</code>) &rarr; "
        "<b>Adhya</b> (<code>egress_scanner</code>) &rarr; "
        "<b>Sharad</b> (FastAPI + Next.js UI)"
    )
    story.append(Paragraph(flow_text, body_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "<b>SENTINEL Research Project</b> • 56 / 56 Automated Tests Passing • github.com/sharadpawarsaini/sentinel-secure-trustworthy-rag",
        ParagraphStyle("Footer", parent=body_style, alignment=1, textColor=TEXT_MUTED, fontSize=7.5),
    ))

    doc.build(story)
    print(f"Generated PDF: {PDF_PATH.resolve()}")


if __name__ == "__main__":
    build_pdf()
