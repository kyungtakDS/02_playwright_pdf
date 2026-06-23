# 02_playwright_pdf

Playwright로 웹 슬라이드(https://claudecode-lecture.vercel.app 의 "Part0-실리콘밸리 엔지니어의 하루" 강의 슬라이드 1~43장)를 각각 PDF로 캡처한 뒤 하나의 PDF로 병합하는 스크립트입니다.

## 사용법

```bash
pip install playwright pypdf
python -m playwright install chromium
python playwright_pdf_download.py
```

실행하면 `AI_Native_lecture_slides_43.pdf` 파일이 생성됩니다.
