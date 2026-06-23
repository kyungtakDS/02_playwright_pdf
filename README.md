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

## GUI 앱으로 실행하기

명령줄 대신 창에 URL을 입력하고 버튼만 누르는 방식으로도 쓸 수 있습니다.

- `run_app.vbs`를 더블클릭하면 콘솔 창 없이 GUI(`gui_app.py`)가 바로 뜹니다.
- 창에 슬라이드 URL을 입력하고 "PDF로 변환" 버튼을 누르면 진행 상황이 로그창에 표시되고,
  완료되면 `output/` 폴더에 PDF가 저장됩니다.

`run_app.vbs`는 `pythonw.exe` 경로가 하드코딩되어 있으므로, 다른 PC에서 쓰려면
해당 경로(`C:\miniconda3\envs\flood_risk311\pythonw.exe`)를 자신의 Python 환경 경로로 바꿔주세요.

내부적으로 `slides_to_pdf.py`의 변환 로직을 GUI와 CLI(`playwright_pdf_download.py`)가 함께 사용합니다.

## 특정 강의 사이트 전용 스크립트

슬라이드 구조가 달라 범용 스크립트로 캡처하기 어려운 강의 사이트는 별도 스크립트로 처리합니다.
두 사이트 모두 비밀번호로 잠긴 수강생 전용 콘텐츠이므로, 비밀번호는 코드에 넣지 않고
환경변수로 전달합니다.

- `AiSyncClub_slides_to_pdf.py`: `aisyncclub-fastcampus-claude.vercel.app` 강의
  - 환경변수: `AISYNCCLUB_PASSWORD`
- `careerhacker_slides_to_pdf.py`: `careerhackeralex.com` AI 네이티브 강의
  - 환경변수: `CAREERHACKER_PASSWORD`

```bash
# PowerShell
$env:AISYNCCLUB_PASSWORD = "..."
python AiSyncClub_slides_to_pdf.py

$env:CAREERHACKER_PASSWORD = "..."
python careerhacker_slides_to_pdf.py
```

결과 PDF는 `output/` 폴더에 저장되며, 큰 바이너리 파일이라 git에는 커밋하지 않습니다(`.gitignore` 참고).
