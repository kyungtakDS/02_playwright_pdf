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
CHAPTER_LABEL_RE = re.compile(r"^(CH\d+)\s*\xb7\s*(.+)$")


def chapter_id_from_url(chapter_url):
    return chapter_url.rstrip("/").split("/")[-1]


def get_chapter_label(slide_box):
    """슬라이드 영역 텍스트에서 'CH00 · AI 네이티브' 형태의 배지를 찾아 (id, title)을 반환."""
    for line in slide_box.inner_text().splitlines():
        m = CHAPTER_LABEL_RE.match(line.strip())
        if m:
            return m.group(1), m.group(2)
    return None, None


def slugify(text):
    text = re.sub(r"\s+", "_", text.strip())
    return re.sub(r'[\\/:*?"<>|]', "", text)


def unlock_chapter_if_needed(page, password, log=print):
    """'수강생 전용' 비밀번호 입력 폼이 보이면 비밀번호를 입력해 잠금을 해제한다."""
    unlock_input = page.get_by_placeholder("비밀번호")
    if unlock_input.count() == 0:
        return

    if not password:
        raise RuntimeError("이 챕터는 비밀번호가 필요합니다. password를 전달해주세요.")

    log("  Unlocking with password...")
    unlock_input.fill(password)
    page.get_by_role("button", name="잠금 해제").click()
    page.wait_for_load_state("networkidle")


def capture_chapter(page, chapter_url, temp_dir, password=None, log=print):
    """챕터 페이지 하나를 열어 '다음 슬라이드'를 끝까지 클릭하며 각 슬라이드를 PNG로 저장."""
    page.goto(chapter_url)
    page.wait_for_load_state("networkidle")
    page.add_style_tag(content="header { display: none !important; }")

    unlock_chapter_if_needed(page, password, log)

    slide_box = page.locator(".group\\/slides")
    next_btn = page.get_by_label("Next slide")
    counter = page.locator("text=/\\d+\\s*\\/\\s*\\d+/").first

    chapter_id, chapter_title = get_chapter_label(slide_box)
    chapter_id = chapter_id or chapter_id_from_url(chapter_url)

    m = COUNTER_RE.match(counter.inner_text())
    total = int(m.group(2)) if m else None

    page.mouse.move(0, 0)  # 호버 상태로 다음/이전 화살표 아이콘이 캡처에 남지 않도록 마우스를 치워둔다

    image_files = []
    idx = 0
    while True:
        idx += 1
        out_file = temp_dir / f"slide_{idx:03d}.png"
        slide_box.screenshot(path=str(out_file))
        image_files.append(out_file)
        log(f"  Captured slide {idx}/{total or '?'}")

        if next_btn.is_disabled():
            break
        next_btn.click()
        page.wait_for_timeout(300)
        page.mouse.move(0, 0)
        page.wait_for_timeout(150)

    return chapter_id, chapter_title, image_files


def images_to_pdf(image_files, out_path):
    images = [Image.open(f).convert("RGB") for f in image_files]
    images[0].save(out_path, save_all=True, append_images=images[1:])


def convert_chapter_to_pdf(chapter_url, password=None, log=print):
    """챕터 URL 하나를 받아 모든 슬라이드를 캡처/병합하고 결과 PDF 경로를 반환."""
    temp_dir = Path(TEMP_DIR_NAME)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    OUTPUT_DIR.mkdir(exist_ok=True)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport=VIEWPORT)

            chapter_id, chapter_title, image_files = capture_chapter(page, chapter_url, temp_dir, password, log)

            browser.close()

        total = len(image_files)
        name_parts = [chapter_id]
        if chapter_title:
            name_parts.append(slugify(chapter_title))
        name_parts.append(f"slides_{total}")
        final_pdf = OUTPUT_DIR / f"{'_'.join(name_parts)}.pdf"

        images_to_pdf(image_files, final_pdf)

        log(f"Done: {final_pdf}")
        log(f"Total slides: {total}")
        return final_pdf
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def convert_course_to_pdfs(chapter_urls, password=None, log=print):
    """챕터 URL 목록을 순서대로 처리해 챕터별 PDF를 생성."""
    results = []
    for chapter_url in chapter_urls:
        log(f"=== {chapter_url} ===")
        results.append(convert_chapter_to_pdf(chapter_url, password, log))
    return results


if __name__ == "__main__":
    BASE = "https://www.careerhackeralex.com/lectures/ai-native"
    urls = [f"{BASE}/ch{n:02d}" for n in range(3, 12)]
    password = os.environ["CAREERHACKER_PASSWORD"]
    convert_course_to_pdfs(urls, password=password)
