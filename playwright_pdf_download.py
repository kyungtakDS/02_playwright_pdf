from playwright.sync_api import sync_playwright
from pypdf import PdfWriter
from pathlib import Path

BASE_URL = "https://claudecode-lecture.vercel.app/Part0-%ec%8b%a4%eb%a6%ac%ec%bd%98%eb%b0%b8%eb%a6%ac_%ec%97%94%ec%a7%80%eb%8b%88%ec%96%b4%ec%9d%98_%ed%95%98%eb%a3%a8/slides"

SLIDE_FILES = [
    "01-intro-hook.html",
    "02-instructor.html",
    "03-ai-turning-point.html",
    "04-why-share-now.html",
    "05-course-differentiators.html",
    "06-course-structure.html",
    "07-learning-arc.html",
    "08-three-keywords.html",
    "09-outcome-20h.html",
    "10-ai-tool-landscape.html",
    "11-claude-code-edges.html",
    "12-tool-comparison.html",
    "13-methodology-over-tools.html",
    "14-three-core-tools.html",
    "15-role-division.html",
    "16-supporting-tools.html",
    "17-tool-timeline-cost.html",
    "18-day-overview.html",
    "19-morning-briefing.html",
    "20-briefing-example.html",
    "21-delegate-morning.html",
    "22-afternoon-review.html",
    "23-eod-autoreport.html",
    "24-daily-principle.html",
    "25-step1-briefing-demo.html",
    "26-step2-status-priority.html",
    "27-step3-delegate.html",
    "28-collect-judge-execute.html",
    "29-habit1-focused-session.html",
    "30-habit2-claude-md.html",
    "31-habit3-plan-review.html",
    "32-habit4-verify-output.html",
    "33-habit5-memory.html",
    "34-five-habits-summary.html",
    "35-team-consistency-problem.html",
    "36-claude-md-team-share.html",
    "37-rules-directory.html",
    "38-team-hooks.html",
    "39-team-rollout-tips.html",
    "40-senior-without-context.html",
    "41-role-shift.html",
    "42-three-principles.html",
    "43-part0-summary.html",
]

OUT_DIR = Path("slides_pdf")
OUT_DIR.mkdir(exist_ok=True)

FINAL_PDF = "AI_Native_lecture_slides_43.pdf"


def save_current_page_as_pdf(page, idx):
    out_file = OUT_DIR / f"slide_{idx:02d}.pdf"

    content_height = page.evaluate("document.body.getBoundingClientRect().height")
    page_height = max(content_height, 864) + 5

    page.pdf(
        path=str(out_file),
        width="1536px",
        height=f"{page_height}px",
        print_background=True,
        margin={
            "top": "0mm",
            "right": "0mm",
            "bottom": "0mm",
            "left": "0mm",
        },
    )

    print(f"Saved: {out_file}")
    return out_file


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page(
        viewport={
            "width": 1536,
            "height": 864,
        }
    )

    pdf_files = []

    for idx, filename in enumerate(SLIDE_FILES, start=1):
        url = f"{BASE_URL}/{filename}"
        page.goto(url)
        page.wait_for_load_state("networkidle")
        pdf_files.append(save_current_page_as_pdf(page, idx))

    browser.close()

# PDF 병합
writer = PdfWriter()

for pdf in pdf_files:
    writer.append(str(pdf))

with open(FINAL_PDF, "wb") as f:
    writer.write(f)

print(f"\nDone: {FINAL_PDF}")
print(f"Total slides: {len(pdf_files)}")
