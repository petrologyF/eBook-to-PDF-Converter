import customtkinter as ctk
import pyautogui
import time
import os
import threading
from PIL import Image, ImageGrab, ImageTk
import ctypes
from tkinter import filedialog
import json

# マルチモニター＆DPIスケーリングによる座標のズレを防ぐ
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
pyautogui.FAILSAFE = True

class RegionSelectorOverlay(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        
        # マルチモニター全画面を覆うための処理 (Windows固有)
        user32 = ctypes.windll.user32
        self.v_x = user32.GetSystemMetrics(76)
        self.v_y = user32.GetSystemMetrics(77)
        v_width = user32.GetSystemMetrics(78)
        v_height = user32.GetSystemMetrics(79)
        
        self.geometry(f"{v_width}x{v_height}+{self.v_x}+{self.v_y}")
        self.overrideredirect(True)
        self.attributes('-alpha', 0.4)
        self.attributes('-topmost', True)
        self.config(cursor="cross")
        
        self.canvas = ctk.CTkCanvas(self, bg='black', highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.start_x = None
        self.start_y = None
        self.rect = None
        
    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, event.x, event.y, outline='red', width=3)
        
    def on_drag(self, event):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)
            
    def on_release(self, event):
        end_x, end_y = event.x, event.y
        
        # マルチモニター上の絶対座標に変換
        abs_x1 = self.start_x + self.v_x
        abs_y1 = self.start_y + self.v_y
        abs_x2 = end_x + self.v_x
        abs_y2 = end_y + self.v_y
        
        x = min(abs_x1, abs_x2)
        y = min(abs_y1, abs_y2)
        w = abs(abs_x2 - abs_x1)
        h = abs(abs_y2 - abs_y1)
        
        self.destroy()
        
        if w > 10 and h > 10:
            self.callback((int(x), int(y), int(w), int(h)))


class PreviewWindow(ctk.CTkToplevel):
    """キャプチャ完了後のプレビュー＆PDF保存ウィンドウ"""
    def __init__(self, parent, image_paths, default_name):
        super().__init__(parent)
        self.image_paths = image_paths
        self.default_name = default_name
        self._thumbs = []  # GC防止用

        self.title("Preview & Save PDF")
        self.geometry("700x520")
        self.minsize(600, 450)
        self.grab_set()  # モーダル化

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- サムネイルスクロールエリア ----
        self.scroll_frame = ctk.CTkScrollableFrame(self, label_text=f"{len(image_paths)} pages captured")
        self.scroll_frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="nsew")

        cols = 4
        for i, path in enumerate(image_paths):
            img = Image.open(path)
            img.thumbnail((140, 140))
            tk_img = ImageTk.PhotoImage(img)
            self._thumbs.append(tk_img)

            frame = ctk.CTkFrame(self.scroll_frame)
            frame.grid(row=i // cols, column=i % cols, padx=6, pady=6)

            lbl_img = ctk.CTkLabel(frame, image=tk_img, text="")
            lbl_img.pack(padx=4, pady=(4, 0))
            lbl_num = ctk.CTkLabel(frame, text=f"p.{i+1}", font=ctk.CTkFont(size=11))
            lbl_num.pack(pady=(0, 4))

        # ---- ボタンエリア ----
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=1, column=0, padx=16, pady=(4, 16), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        self.lbl_info = ctk.CTkLabel(btn_frame, text="内容を確認してから保存場所を指定してください", text_color="gray")
        self.lbl_info.grid(row=0, column=0, columnspan=2, pady=(0, 8))

        btn_cancel = ctk.CTkButton(btn_frame, text="閉じる（破棄）",
                                   fg_color="#3d3d3d", hover_color="#555",
                                   command=self._on_cancel)
        btn_cancel.grid(row=1, column=0, padx=(0, 6), sticky="ew")

        btn_save = ctk.CTkButton(btn_frame, text="💾  保存場所を指定してPDF保存",
                                 fg_color="#2EA043", hover_color="#238636",
                                 command=self._on_save)
        btn_save.grid(row=1, column=1, padx=(6, 0), sticky="ew")

    def _on_save(self):
        save_path = filedialog.asksaveasfilename(
            parent=self,
            title="PDFの保存先を指定",
            initialfile=self.default_name,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not save_path:
            return  # キャンセルされた場合は何もしない

        self.lbl_info.configure(text="PDF生成中...", text_color="#D29922")
        self.update()

        try:
            images = []
            first = Image.open(self.image_paths[0]).convert('RGB')
            for path in self.image_paths[1:]:
                images.append(Image.open(path).convert('RGB'))
            first.save(save_path, save_all=True, append_images=images)
            self.lbl_info.configure(text=f"✅ 保存完了: {os.path.basename(save_path)}", text_color="#2EA043")
        except Exception as e:
            self.lbl_info.configure(text=f"❌ エラー: {e}", text_color="#F85149")

    def _on_cancel(self):
        # 一時ファイルを削除して閉じる
        for path in self.image_paths:
            try:
                os.remove(path)
            except Exception:
                pass
        # 空の一時フォルダも削除
        try:
            parent_dir = os.path.dirname(self.image_paths[0])
            if os.path.isdir(parent_dir) and not os.listdir(parent_dir):
                os.rmdir(parent_dir)
        except Exception:
            pass
        self.destroy()


class EbookCaptureApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("eBook to PDF Converter")
        self.geometry("400x500")
        self.minsize(380, 480)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        
        self.capture_region = None
        self.is_capturing = False
        
        self.settings_file = "settings.json"
        self._load_settings()
        self._build_ui()
        
    def _load_settings(self):
        """前回の設定を読み込む"""
        self.saved_data = {}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    self.saved_data = json.load(f)
                    self.capture_region = self.saved_data.get("region")
            except Exception:
                self.saved_data = {}

    def _save_settings(self):
        """現在の設定を保存する"""
        data = {
            "filename": self.entry_filename.get(),
            "chapter": self.entry_chapter.get(),
            "pages": self.entry_pages.get(),
            "region": self.capture_region
        }
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def _build_ui(self):
        # 1. Title
        title_lbl = ctk.CTkLabel(self, text="eBook to PDF Converter", font=ctk.CTkFont(size=20, weight="bold"))
        title_lbl.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 20), sticky="ew")
        
        # 2. File Name
        ctk.CTkLabel(self, text="File Name:", anchor="w").grid(row=1, column=0, padx=(20, 10), pady=10, sticky="ew")
        self.entry_filename = ctk.CTkEntry(self, placeholder_text="e.g. bookname")
        self.entry_filename.grid(row=1, column=1, padx=(10, 20), pady=10, sticky="ew")
        self.entry_filename.insert(0, self.saved_data.get("filename", "book"))
        
        # 3. Chapter
        ctk.CTkLabel(self, text="Chapter:", anchor="w").grid(row=2, column=0, padx=(20, 10), pady=10, sticky="ew")
        self.entry_chapter = ctk.CTkEntry(self, placeholder_text="e.g. 01")
        self.entry_chapter.grid(row=2, column=1, padx=(10, 20), pady=10, sticky="ew")
        
        last_chapter = self.saved_data.get("chapter", "01")
        if last_chapter.isdigit():
            # 数字の場合は+1する（桁数を維持）
            new_chapter = str(int(last_chapter) + 1).zfill(len(last_chapter))
            self.entry_chapter.insert(0, new_chapter)
        else:
            self.entry_chapter.insert(0, last_chapter)
        
        # 4. Total Pages
        ctk.CTkLabel(self, text="Total Pages:", anchor="w").grid(row=3, column=0, padx=(20, 10), pady=10, sticky="ew")
        self.entry_pages = ctk.CTkEntry(self, placeholder_text="e.g. 50")
        self.entry_pages.grid(row=3, column=1, padx=(10, 20), pady=10, sticky="ew")
        self.entry_pages.insert(0, self.saved_data.get("pages", ""))
        
        # 5. Interval
        ctk.CTkLabel(self, text="Interval (sec):", anchor="w").grid(row=4, column=0, padx=(20, 10), pady=10, sticky="ew")
        self.entry_interval = ctk.CTkEntry(self, placeholder_text="e.g. 1.5")
        self.entry_interval.insert(0, "1.5")
        self.entry_interval.grid(row=4, column=1, padx=(10, 20), pady=10, sticky="ew")
        
        # Buttons Frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        self.btn_region = ctk.CTkButton(btn_frame, text="1. Select Region", command=self.start_region_selection)
        self.btn_region.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        self.btn_start = ctk.CTkButton(btn_frame, text="2. Start Capture", command=self.start_capture_thread, fg_color="#2EA043", hover_color="#238636")
        self.btn_start.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        
        if self.capture_region:
            r = self.capture_region
            self.lbl_region = ctk.CTkLabel(self, text=f"Region: X: {r[0]}, Y: {r[1]}, W: {r[2]}, H: {r[3]}", text_color="#58A6FF")
        else:
            self.lbl_region = ctk.CTkLabel(self, text="Region: Not selected", text_color="gray")
        self.lbl_region.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")
        
        # Progress & Status
        self.lbl_status = ctk.CTkLabel(self, text="Status: Ready", font=ctk.CTkFont(size=14))
        self.lbl_status.grid(row=7, column=0, columnspan=2, padx=20, pady=(10, 5), sticky="ew")
        
        self.progressbar = ctk.CTkProgressBar(self)
        self.progressbar.grid(row=8, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        self.progressbar.set(0)
        
    def start_region_selection(self):
        self.withdraw()
        self.after(200, lambda: RegionSelectorOverlay(self, self.on_region_selected))
        
    def on_region_selected(self, rect):
        self.capture_region = rect
        self.lbl_region.configure(text=f"Region: X: {rect[0]}, Y: {rect[1]}, W: {rect[2]}, H: {rect[3]}")
        self.deiconify()
        
    def start_capture_thread(self):
        if self.is_capturing:
            return
            
        if not self.capture_region:
            self.lbl_status.configure(text="Error: Missing region!", text_color="#F85149")
            return
            
        try:
            pages = int(self.entry_pages.get())
            interval = float(self.entry_interval.get())
            fname = self.entry_filename.get().strip() or "book"
            chapter = self.entry_chapter.get().strip() or "01"
            if pages <= 0 or interval < 0:
                raise ValueError
        except ValueError:
            self.lbl_status.configure(text="Error: Invalid Numbers!", text_color="#F85149")
            return
            
        self.is_capturing = True
        self.btn_start.configure(state="disabled")
        self.btn_region.configure(state="disabled")
        
        # 設定を保存
        self._save_settings()
        
        thread = threading.Thread(target=self.capture_loop, args=(pages, interval, fname, chapter, self.capture_region))
        thread.daemon = True
        thread.start()
        
    def auto_update_status(self, msg, color=None):
        if color:
            self.lbl_status.configure(text=msg, text_color=color)
        else:
            self.lbl_status.configure(text=msg, text_color=("black", "white"))
            
    def capture_loop(self, total_pages, interval, fname, chapter, region):
        temp_dir = f"temp_{fname}_{chapter}"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        image_paths = []
            
        try:
            # カウントダウン
            for i in range(5, 0, -1):
                self.after(0, self.auto_update_status, f"Starting in {i}... Focus eBook!", "#D29922")
                time.sleep(1)
                
            self.after(0, self.auto_update_status, "Capturing...", "#2EA043")
            
            for page in range(1, total_pages + 1):
                self.after(0, self.auto_update_status, f"Capturing page {page}/{total_pages}...", "#58A6FF")
                self.after(0, self.progressbar.set, page / total_pages)
                
                # 最初はすぐに撮る、以降はめくってから撮る
                if page > 1:
                    pyautogui.press('right')
                    time.sleep(interval)
                else:
                    time.sleep(0.5)
                
                # pyautoguiの代わりにマルチモニター対応のPillowを使用
                bbox = (region[0], region[1], region[0] + region[2], region[1] + region[3])
                img = ImageGrab.grab(bbox=bbox, all_screens=True)
                
                img_path = os.path.join(temp_dir, f"page_{page:04d}.png")
                img.save(img_path)
                image_paths.append(img_path)
                
            # プレビューウィンドウを開く（PDF即時保存はやめる）
            default_pdf_name = f"{fname}_{chapter}.pdf"
            self.after(0, self.auto_update_status, "Done! Opening preview...", "#2EA043")
            self.after(100, lambda: PreviewWindow(self, image_paths, default_pdf_name))
            
        except pyautogui.FailSafeException:
            self.after(0, self.auto_update_status, "Hit Edge! Cancelled by Fail-Safe.", "#F85149")
        except Exception as e:
            self.after(0, self.auto_update_status, f"Error: {str(e)}", "#F85149")
        finally:
            self.is_capturing = False
            self.after(0, lambda: self.btn_start.configure(state="normal"))
            self.after(0, lambda: self.btn_region.configure(state="normal"))

    def compile_pdf(self, image_paths, output_pdf):
        if not image_paths:
            return
        images = []
        first_image = Image.open(image_paths[0]).convert('RGB')
        for path in image_paths[1:]:
            images.append(Image.open(path).convert('RGB'))
        first_image.save(output_pdf, save_all=True, append_images=images)


if __name__ == "__main__":
    app = EbookCaptureApp()
    app.mainloop()
