import os
import re
import shutil
from pathlib import Path

from PIL import Image, JpegImagePlugin  # noqa: F401  (registers JPEG save handler for PDF export)
from playwright.sync_api import sync_playwright

TEMP_DIR_NAME = "temp_slides"
OUTPUT_DIR = Path("output")

VIEWPORT = {"width": 1536, "height": 864}

COUNTER_RE = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")

VISIBLE_COUNTER_JS = """() => {
    const els = [...document.querySelectorAll('*')].filter(e =>
        /^\\s*\\d+\\s*\\/\\s*\\d+\\s*$/.test(e.textContent) && e.children.length === 0
    );
    const visible = els.filter(e => e.offsetParent !== null || e.getClientRects().length > 0);
    return visible.map(e => e.textContent.trim());
}"""

MAX_SLIDES_SAFETY_CAP = 60


def ensure_unlocked(page, password, log=print):
    """잠금 해제 상태(localStorage 'aisc-gate-ok')를 보장한다.
    하위 Part 페이지를 직접 열면 사이트가 Part1로 강제 리다이렉트하는 버그가 있어,
    먼저 Part1에서 풀어 플래그를 site-wide로 세팅해둔다."""
    gate = page.evaluate("() => localStorage.getItem('aisc-gate-ok')") if page.url != "about:blank" else None
    if gate == "1":
        return

    page.goto("https://aisyncclub-fastcampus-claude.vercel.app/Part1/index.html")
    page.wait_for_load_state("networkidle")

    pw_input = page.locator("#pw")
    if pw_input.count():
        log("  Unlocking with password...")
        pw_input.fill(password)
        page.get_by_role("button", name="입장 →").click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(500)


def part_name_from_url(part_index_url):
    for part in part_index_url.rstrip("/").split("/"):
        if re.match(r"^Part\d+$", part):
            return part
    return "Part"


def get_slide_deck_links(page):
    """현재(잠금 해제된) 페이지에서 'NN_슬라이드.html' 링크들을 (deck_id, url) 목록으로 반환."""
    pairs = page.eval_on_selector_all(
        "a[href]",
        "els => els.map(e => [e.getAttribute('href'), e.href])",
    )
    links = []
    for raw, href in pairs:
        if "슬라이드.html" in raw:
            deck_id = raw.split("/")[0]
            links.append((deck_id, href))
    return links


def visible_counter(page):
    vals = page.evaluate(VISIBLE_COUNTER_JS)
    return vals[0] if vals else None


def capture_deck(page, deck_url, temp_dir, log=print):
    page.goto(deck_url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)

    next_btn = page.locator("button:has-text('다음')").first

    image_files = []
    idx = 0
    while True:
        idx += 1
        c = visible_counter(page)
        m = COUNTER_RE.match(c) if c else None
        total = int(m.group(2)) if m else None

        out_file = temp_dir / f"slide_{idx:03d}.png"
        page.screenshot(path=str(out_file))
        image_files.append(out_file)
        log(f"  Captured slide {idx}/{total or '?'}")

        if m and int(m.group(1)) >= int(m.group(2)):
            break
        if idx >= MAX_SLIDES_SAFETY_CAP:
            raise RuntimeError(f"Safety cap ({MAX_SLIDES_SAFETY_CAP}) reached without finding end of deck: {deck_url}")
        next_btn.click()
        page.wait_for_timeout(300)

    return image_files


def images_to_pdf(image_files, out_path):
    images = [Image.open(f).convert("RGB") for f in image_files]
    images[0].save(out_path, save_all=True, append_images=images[1:])


def convert_deck_to_pdf(page, part_name, deck_id, deck_url, log=print):
    existing = list(OUTPUT_DIR.glob(f"{part_name}_{deck_id}_slides_*.pdf"))
    if existing:
        log(f"  Skipping (already exists): {existing[0]}")
        return existing[0]

    temp_dir = Path(TEMP_DIR_NAME)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    OUTPUT_DIR.mkdir(exist_ok=True)

    try:
        image_files = capture_deck(page, deck_url, temp_dir, log)
        total = len(image_files)
        final_pdf = OUTPUT_DIR / f"{part_name}_{deck_id}_slides_{total}.pdf"
        images_to_pdf(image_files, final_pdf)
        log(f"Done: {final_pdf}")
        return final_pdf
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def convert_part_to_pdfs(page, part_index_url, password, log=print):
    """Part 인덱스 URL 하나를 잠금 해제하고, 그 안의 모든 강의 슬라이드 덱을 PDF로 변환."""
    part_name = part_name_from_url(part_index_url)
    results = []

    ensure_unlocked(page, password, log)
    page.goto(part_index_url)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(300)

    deck_links = get_slide_deck_links(page)
    log(f"Found {len(deck_links)} slide decks.")

    for deck_id, deck_url in deck_links:
        log(f"=== {part_name}/{deck_id} ===")
        results.append(convert_deck_to_pdf(page, part_name, deck_id, deck_url, log))

    return results


def convert_parts_to_pdfs(part_index_urls, password, log=print):
    """여러 Part 인덱스 URL을 하나의 브라우저 세션에서 순서대로 처리."""
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport=VIEWPORT)
        for part_index_url in part_index_urls:
            log(f"##### {part_name_from_url(part_index_url)} #####")
            results.extend(convert_part_to_pdfs(page, part_index_url, password, log))
        browser.close()
    return results


if __name__ == "__main__":
    BASE = "https://aisyncclub-fastcampus-claude.vercel.app"
    urls = [f"{BASE}/Part{n}/index.html" for n in range(1, 8)]
    password = os.environ["AISYNCCLUB_PASSWORD"]
    convert_parts_to_pdfs(urls, password=password)
