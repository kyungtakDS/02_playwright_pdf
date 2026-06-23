import sys

from slides_to_pdf import convert_slides_to_pdf


def main():
    if len(sys.argv) < 2:
        print("Usage: python playwright_pdf_download.py <slide_url>")
        sys.exit(1)

    convert_slides_to_pdf(sys.argv[1])


if __name__ == "__main__":
    main()
