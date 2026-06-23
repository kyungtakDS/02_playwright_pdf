# 02_playwright_pdf

Playwright로 웹 슬라이드(예: https://claudecode-lecture.vercel.app 의 강의 슬라이드)를
캡처해 하나의 PDF로 병합하는 스크립트입니다.

슬라이드 중 하나의 URL만 주면, 같은 폴더의 `index.html`에서 전체 슬라이드 목록을
자동으로 찾아 모두 PDF로 캡처한 뒤 하나로 병합해 `output/` 폴더에 저장합니다.
캡처에 쓰인 슬라이드별 임시 PDF(`temp_slides/`)는 작업이 끝나면 자동으로 삭제됩니다.

## 사용법

```bash
pip install playwright pypdf
python -m playwright install chromium
python playwright_pdf_download.py "<슬라이드 URL>"
```

예:

```bash
python playwright_pdf_download.py "https://claudecode-lecture.vercel.app/Part0-.../slides/01-intro-hook.html"
```

실행하면 `output/<강의 폴더명>_slides_<총 장수>.pdf` 파일이 생성됩니다.
