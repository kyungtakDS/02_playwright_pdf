import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, scrolledtext

from slides_to_pdf import convert_slides_to_pdf


class App:
    def __init__(self, root):
        self.root = root
        root.title("슬라이드 → PDF 변환기")
        root.geometry("720x480")

        tk.Label(root, text="슬라이드 HTML 주소:").pack(anchor="w", padx=10, pady=(10, 0))

        url_frame = tk.Frame(root)
        url_frame.pack(fill="x", padx=10)

        self.url_entry = tk.Entry(url_frame)
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda e: self.start_conversion())

        self.convert_btn = tk.Button(url_frame, text="PDF로 변환", command=self.start_conversion)
        self.convert_btn.pack(side="left", padx=(8, 0))

        self.log_box = scrolledtext.ScrolledText(root, state="disabled", wrap="word")
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

        self.log_queue = queue.Queue()
        self.root.after(100, self._drain_log_queue)

    def _log(self, message):
        self.log_queue.put(str(message))

    def _drain_log_queue(self):
        while not self.log_queue.empty():
            message = self.log_queue.get_nowait()
            self.log_box.configure(state="normal")
            self.log_box.insert("end", message + "\n")
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        self.root.after(100, self._drain_log_queue)

    def start_conversion(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("입력 필요", "슬라이드 HTML 주소를 입력하세요.")
            return

        self.convert_btn.config(state="disabled")
        self._log(f"\n변환 시작: {url}")

        thread = threading.Thread(target=self._run_conversion, args=(url,), daemon=True)
        thread.start()

    def _run_conversion(self, url):
        try:
            final_pdf = convert_slides_to_pdf(url, log=self._log)
            self._log(f"\n완료! 저장 위치: {Path(final_pdf).resolve()}")
        except Exception as exc:
            self._log(f"\n오류 발생: {exc}")
        finally:
            self.root.after(0, lambda: self.convert_btn.config(state="normal"))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
