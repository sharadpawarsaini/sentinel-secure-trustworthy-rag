"""Generate professional Deployment Guide PDF for Vercel and Render for SENTINEL."""

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
    KeepTogether,
    HRFlowable,
    PageBreak,
)

OUTPUT_DIR = Path("docs/reports")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_PATH = OUTPUT_DIR / "sentinel_deployment_guide_vercel_render.pdf"

# Color Palette: Cyber Security Slate & Blue & Emerald
PRIMARY = colors.HexColor("#0F172A")       # Slate 900
SECONDARY = colors.HexColor("#1E3A8A")     # Navy Blue
ACCENT_CYAN = colors.HexColor("#0284C7")   # Sky Blue
ACCENT_EMERALD = colors.HexColor("#059669")# Emerald Green
ACCENT_AMBER = colors.HexColor("#D97706")  # Amber
TEXT_DARK = colors.HexColor("#0F172A")
TEXT_MUTED = colors.HexColor("#475569")
BG_LIGHT = colors.HexColor("#F8FAFC")
BG_CARD = colors.HexColor("#F1F5F9")
CODE_BG = colors.HexColor("#1E293B")
CODE_FG = colors.HexColor("#38BDF8")
BORDER = colors.HexColor("#CBD5E1")


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        alignment=0,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor=TEXT_MUTED,
        spaceAfter=12,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=SECONDARY,
        spaceBefore=10,
        spaceAfter=6,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=6,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=TEXT_DARK,
        spaceAfter=4,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=3,
    )

    code_style = ParagraphStyle(
        "Code_Custom",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7.5,
        leading=10,
        textColor=CODE_FG,
        backColor=CODE_BG,
        borderColor=PRIMARY,
        borderWidth=0.5,
        borderPadding=5,
        spaceBefore=3,
        spaceAfter=5,
    )

    callout_style = ParagraphStyle(
        "Callout_Custom",
        parent=body_style,
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=PRIMARY,
    )

    story = []

    # Title Banner
    story.append(Paragraph("SENTINEL Deployment Guide", title_style))
    story.append(Paragraph("Production Cloud Architecture: Vercel (Next.js Frontend) + Render (FastAPI & PyTorch Backend)", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=0, spaceAfter=8))

    # Architecture Overview Table
    arch_summary_data = [
        [
            Paragraph("<b>Component</b>", body_style),
            Paragraph("<b>Hosting Platform</b>", body_style),
            Paragraph("<b>Runtime / Tech Stack</b>", body_style),
            Paragraph("<b>Role & Purpose</b>", body_style)
        ],
        [
            Paragraph("<b>Frontend Portal</b>", body_style),
            Paragraph("<b>Vercel</b> (Edge/Serverless)", body_style),
            Paragraph("Next.js 16 + React 19 + Tailwind CSS v4", body_style),
            Paragraph("Cybersecurity UI, 6-barrier radar, claim entailment matrix, audit viewer.", body_style)
        ],
        [
            Paragraph("<b>Backend API & Models</b>", body_style),
            Paragraph("<b>Render</b> (Web Service)", body_style),
            Paragraph("Python 3.12 + FastAPI + ChromaDB + PyTorch", body_style),
            Paragraph("Input guard, semantic vector retrieval, NLI DeBERTa verification, Gemini LLM.", body_style)
        ]
    ]
    t_arch = Table(arch_summary_data, colWidths=[105, 115, 155, 165])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_CARD),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 8))

    # Part 1: Render Deployment
    story.append(Paragraph("PART 1: Deploying the FastAPI Backend on Render", h1_style))
    story.append(Paragraph(
        "Render hosts the stateful Python engine, vector database, and neural models with persistent disk options.",
        body_style
    ))

    story.append(Paragraph("<b>Step 1.1: Create Render Web Service</b>", h2_style))
    story.append(Paragraph("1. Log in to <font color='#0284C7'>render.com</font> and click <b>New +</b> &gt; <b>Web Service</b>.", bullet_style))
    story.append(Paragraph("2. Connect your GitHub repository: <code>sharadpawarsaini/sentinel-secure-trustworthy-rag</code>.", bullet_style))
    story.append(Paragraph("3. Configure basic settings:", bullet_style))

    render_settings_data = [
        [Paragraph("<b>Setting</b>", body_style), Paragraph("<b>Value to Enter</b>", body_style)],
        [Paragraph("<b>Name</b>", body_style), Paragraph("<code>sentinel-backend-api</code>", body_style)],
        [Paragraph("<b>Region</b>", body_style), Paragraph("Oregon (US West) or Singapore / Frankfurt", body_style)],
        [Paragraph("<b>Branch</b>", body_style), Paragraph("<code>main</code>", body_style)],
        [Paragraph("<b>Root Directory</b>", body_style), Paragraph("<i>(Leave empty / repository root)</i>", body_style)],
        [Paragraph("<b>Runtime</b>", body_style), Paragraph("<b>Python 3</b>", body_style)],
        [Paragraph("<b>Build Command</b>", body_style), Paragraph("<code>pip install -r requirements.txt</code>", body_style)],
        [Paragraph("<b>Start Command</b>", body_style), Paragraph("<code>uvicorn sentinel.backend.api:app --host 0.0.0.0 --port $PORT</code>", body_style)],
        [Paragraph("<b>Instance Type</b>", body_style), Paragraph("Starter (512MB) or Standard (2GB recommended for PyTorch/NLI)", body_style)]
    ]
    t_render = Table(render_settings_data, colWidths=[140, 400])
    t_render.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_CARD),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_render)
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>Step 1.2: Configure Environment Variables on Render</b>", h2_style))
    story.append(Paragraph("In the Render Dashboard under <b>Environment</b>, add:", body_style))
    render_env_code = (
        "LLM_PROVIDER=gemini\n"
        "LLM_MODEL=gemini-2.5-flash\n"
        "GEMINI_API_KEY=AIzaSy...YourGeminiApiKeyHere\n"
        "VECTOR_STORE_DIR=/data/vectorstore\n"
        "TRUST_THRESHOLD_HIGH=0.75\n"
        "TRUST_THRESHOLD_LOW=0.50\n"
        "SECURITY_RISK_THRESHOLD=0.70"
    )
    story.append(Paragraph(render_env_code.replace("\n", "<br/>"), code_style))

    story.append(Paragraph("<b>Step 1.3: Add Persistent Disk (Optional for Corpus Persistence)</b>", h2_style))
    story.append(Paragraph(
        "To retain ChromaDB vector collections across redeployments, click <b>Disks</b> &gt; <b>Add Disk</b>: Name <code>sentinel-data</code>, Mount Path <code>/data</code>, Size <code>1 GB</code>.",
        body_style
    ))
    story.append(Paragraph("Once deployed, your backend will be live at: <code>https://sentinel-backend-api.onrender.com</code>.", callout_style))

    story.append(Spacer(1, 10))

    # Part 2: Vercel Deployment
    story.append(Paragraph("PART 2: Deploying the Next.js Frontend on Vercel", h1_style))
    story.append(Paragraph(
        "Vercel serves the Next.js glassmorphic user portal and proxies API requests seamlessly to your Render backend.",
        body_style
    ))

    story.append(Paragraph("<b>Step 2.1: Import Project to Vercel</b>", h2_style))
    story.append(Paragraph("1. Log in to <font color='#0284C7'>vercel.com</font> and click <b>Add New...</b> &gt; <b>Project</b>.", bullet_style))
    story.append(Paragraph("2. Select your repository <code>sentinel-secure-trustworthy-rag</code>.", bullet_style))
    story.append(Paragraph("3. Under <b>Root Directory</b>, click <b>Edit</b> and select <code>frontend</code>. <i>(Crucial Step!)</i>", bullet_style))
    story.append(Paragraph("4. Framework Preset will auto-detect as <b>Next.js</b>.", bullet_style))

    story.append(Paragraph("<b>Step 2.2: Configure Environment Variables on Vercel</b>", h2_style))
    story.append(Paragraph("Add the following environment variable pointing to your deployed Render URL:", body_style))
    vercel_env_code = (
        "BACKEND_API_URL=https://sentinel-backend-api.onrender.com\n"
        "NEXT_PUBLIC_BACKEND_URL=https://sentinel-backend-api.onrender.com"
    )
    story.append(Paragraph(vercel_env_code.replace("\n", "<br/>"), code_style))

    story.append(Paragraph("<b>Step 2.3: Production API Rewrites (next.config.ts)</b>", h2_style))
    story.append(Paragraph(
        "Ensure <code>frontend/next.config.ts</code> dynamically routes <code>/api/:path*</code> to the Render backend in production:",
        body_style
    ))
    next_cfg_code = (
        "const backendUrl = process.env.BACKEND_API_URL || 'http://127.0.0.1:8000';\n"
        "async rewrites() {\n"
        "  return [\n"
        "    { source: '/api/:path*', destination: `${backendUrl}/api/:path*` }\n"
        "  ];\n"
        "}"
    )
    story.append(Paragraph(next_cfg_code.replace("\n", "<br/>"), code_style))

    story.append(PageBreak())

    # Page 2: Testing, CORS, Pre-flight Checklist, Troubleshooting
    story.append(Paragraph("PART 3: Connecting & Securing the Full Pipeline", h1_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=0, spaceAfter=8))

    story.append(Paragraph("<b>3.1: Cross-Origin Resource Sharing (CORS) Verification</b>", h2_style))
    story.append(Paragraph(
        "FastAPI in <code>sentinel/backend/api.py</code> already includes permissive CORS middleware:",
        body_style
    ))
    cors_code = (
        "app.add_middleware(\n"
        "    CORSMiddleware,\n"
        "    allow_origins=['*'],  # Or specify: ['https://sentinel-rag.vercel.app']\n"
        "    allow_credentials=True,\n"
        "    allow_methods=['*'],\n"
        "    allow_headers=['*'],\n"
        ")"
    )
    story.append(Paragraph(cors_code.replace("\n", "<br/>"), code_style))

    story.append(Paragraph("<b>3.2: Automated Health Verification & Pre-flight Checklist</b>", h2_style))
    
    checklist_data = [
        [Paragraph("<b>Step / Verification</b>", body_style), Paragraph("<b>Command / Target URL</b>", body_style), Paragraph("<b>Expected Response</b>", body_style)],
        [
            Paragraph("1. Backend Health Check", body_style),
            Paragraph("<code>curl https://...onrender.com/api/health</code>", body_style),
            Paragraph("<code>{\"status\": \"healthy\", \"version\": \"0.4.0\"}</code>", body_style)
        ],
        [
            Paragraph("2. Document Upload Test", body_style),
            Paragraph("<code>curl -F file=@policy.pdf .../upload</code>", body_style),
            Paragraph("<code>{\"status\": \"indexed\", \"chunks_created\": 12}</code>", body_style)
        ],
        [
            Paragraph("3. Closed-Loop Query", body_style),
            Paragraph("<code>curl -X POST .../rag/query -d '{\"query\":\"...\"}'</code>", body_style),
            Paragraph("<code>{\"answer\": \"...\", \"trust_verdict\": \"HIGH_TRUST\"}</code>", body_style)
        ],
        [
            Paragraph("4. Frontend UI Access", body_style),
            Paragraph("Open <code>https://sentinel-*.vercel.app</code>", body_style),
            Paragraph("Glassmorphic cybersecurity UI with live status indicator.", body_style)
        ],
        [
            Paragraph("5. Admin Observability", body_style),
            Paragraph("Open <code>https://sentinel-*.vercel.app/admin</code>", body_style),
            Paragraph("Admin panel with telemetry KPI dials and chunk browser.", body_style)
        ]
    ]
    t_check = Table(checklist_data, colWidths=[120, 240, 180])
    t_check.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_CARD),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_check)
    story.append(Spacer(1, 8))

    story.append(Paragraph("PART 4: Production Troubleshooting & Optimization", h1_style))
    troubleshoot_data = [
        [Paragraph("<b>Symptom / Issue</b>", body_style), Paragraph("<b>Root Cause</b>", body_style), Paragraph("<b>Resolution</b>", body_style)],
        [
            Paragraph("<b>Render Cold Start Delay</b>", body_style),
            Paragraph("Render Free tier spins down web services after 15 minutes of inactivity.", body_style),
            Paragraph("Upgrade to Starter tier ($7/mo) or use a free uptime monitor (e.g., UptimeRobot) pinging <code>/api/health</code> every 10 min.", body_style)
        ],
        [
            Paragraph("<b>PyTorch / Memory Limit</b>", body_style),
            Paragraph("Cross-encoder NLI and SentenceTransformers can exceed 512MB RAM during initial weight downloads.", body_style),
            Paragraph("Select <b>Standard (2GB RAM)</b> on Render, or set <code>USE_MOCK_NLI=true</code> for lightweight testing tiers.", body_style)
        ],
        [
            Paragraph("<b>Vercel Rewrite 404 / 502</b>", body_style),
            Paragraph("<code>BACKEND_API_URL</code> environment variable missing or points to wrong protocol.", body_style),
            Paragraph("Ensure Vercel environment variable is set to full HTTPS url (e.g., <code>https://sentinel-backend.onrender.com</code>).", body_style)
        ],
        [
            Paragraph("<b>ChromaDB Data Loss</b>", body_style),
            Paragraph("Ephemeral containers erase local files on new git deploys.", body_style),
            Paragraph("Attach a Render Persistent Disk mounted at <code>/data</code> with <code>VECTOR_STORE_DIR=/data/vectorstore</code>.", body_style)
        ]
    ]
    t_trouble = Table(troubleshoot_data, colWidths=[120, 200, 220])
    t_trouble.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BG_CARD),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t_trouble)
    story.append(Spacer(1, 10))

    # Footer Note
    footer_text = (
        "<b>SENTINEL Research Project</b> • Engineering Architecture: Next.js + FastAPI + ChromaDB + Gemini / Ollama<br/>"
        "Lead System Architect: Sharad Pawar Saini • Repository: github.com/sharadpawarsaini/sentinel-secure-trustworthy-rag"
    )
    story.append(Paragraph(footer_text, ParagraphStyle("Footer", parent=body_style, alignment=1, textColor=TEXT_MUTED, fontSize=7.5)))

    doc.build(story)
    print(f"Generated PDF: {PDF_PATH.resolve()}")


if __name__ == "__main__":
    build_pdf()
