import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote

from playwright.sync_api import sync_playwright
from pypdf import PdfWriter

TEMP_DIR = Path("temp_slides")
OUTPUT_DIR = Path("output")

VIEWPORT = {"width": 1536, "height": 864}

SLIDE_FILENAME_RE = re.compile(r"^(\d+)-.+\.html$")


def get_slide_files(page, slides_dir_url):
    """index.html을 열어 같은 폴더 안의 슬라이드 파일 목록을 번호 순으로 가져온다."""
    page.goto(slides_dir_url + "index.html")
    page.wait_for_load_state("networkidle")

    hrefs = page.eval_on_selector_all(
        "a[href$='.html']",
        "els => els.map(e => e.getAttribute('href'))",
    )

    seen = set()
    slide_files = []
    for href in hrefs:
        name = href.split("/")[-1]
        if name in seen or not SLIDE_FILENAME_RE.match(name):
            continue
        seen.add(name)
        slide_files.append(name)

    slide_files.sort(key=lambda n: int(SLIDE_FILENAME_RE.match(n).group(1)))
    return slide_files


def deck_name_from_url(start_url):
    """.../<deck>/slides/xx.html 형태에서 <deck> 이름을 추출해 파일명으로 사용."""
    parts = start_url.rstrip("/").split("/")
    deck = unquote(parts[-3])
    return re.sub(r'[\\/:*?"<>|]', "_", deck)


def save_current_page_as_pdf(page, out_dir, idx):
    out_file = out_dir / f"slide_{idx:02d}.pdf"

    content_height = page.evaluate("document.body.getBoundingClientRect().height")
    page_height = max(content_height, VIEWPORT["height"]) + 5

    page.pdf(
        path=str(out_file),
        width=f"{VIEWPORT['width']}px",
        height=f"{page_height}px",
        print_background=True,
        margin={"top": "0mm", "right": "0mm", "bottom": "0mm", "left": "0mm"},
    )

    print(f"Saved: {out_file}")
    return out_file


def main():
    if len(sys.argv) < 2:
        print("Usage: python playwright_pdf_download.py <slide_url>")
        sys.exit(1)

    start_url = sys.argv[1]
    slides_dir_url = start_url.rsplit("/", 1)[0] + "/"

    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
    TEMP_DIR.mkdir()
    OUTPUT_DIR.mkdir(exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT)

        slide_files = get_slide_files(page, slides_dir_url)
        total = len(slide_files)
        print(f"Found {total} slides.")

        pdf_files = []
        for idx, filename in enumerate(slide_files, start=1):
            page.goto(slides_dir_url + filename)
            page.wait_for_load_state("networkidle")
            pdf_files.append(save_current_page_as_pdf(page, TEMP_DIR, idx))

        browser.close()

    deck_name = deck_name_from_url(start_url)
    final_pdf = OUTPUT_DIR / f"{deck_name}_slides_{total}.pdf"

    writer = PdfWriter()
    for pdf in pdf_files:
        writer.append(str(pdf))
    with open(final_pdf, "wb") as f:
        writer.write(f)

    shutil.rmtree(TEMP_DIR)

    print(f"\nDone: {final_pdf}")
    print(f"Total slides: {total}")


if __name__ == "__main__":
    main()
