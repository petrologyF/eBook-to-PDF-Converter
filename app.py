import ctypes
import sys
import os

# マルチモニター＆DPIスケーリングによる座標のズレを防ぐ（GUI・画面キャプチャ系ライブラリ読み込み前に実行）
if sys.platform == "win32":
    try:
        # Process_Per_Monitor_DPI_Aware (2) - CustomTkinter内部のスケーリング仕様と一致させる
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

import json
import re
import shutil
import threading
import time
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import pyautogui
from PIL import Image, ImageGrab, PdfParser

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
pyautogui.FAILSAFE = True

# 実行ファイルまたはスクリプトの基準ディレクトリ
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_PDF_LOCK = threading.Lock()


def sanitize_filename(name: str, fallback: str = "book") -> str:
    """Windowsのファイル名として使用できない文字を安全な文字に置換する"""
    cleaned = re.sub(r'[\\/:*?"<>|\r\n\t]+', "_", name.strip()).strip(". ")
    return cleaned if cleaned else fallback


def save_pdf_with_preferences(
    image_paths: list[str],
    save_path: str,
    is_r2l: bool = False,
    is_spread: bool = False,
) -> None:
    """画像リストからPDFを生成し、綴じ方向とページレイアウト設定をCatalogに直接書き込む"""
    if not image_paths:
        raise ValueError("保存する画像がありません。")

    direction = b"R2L" if is_r2l else b"L2R"
    if is_spread:
        page_layout = b"TwoPageRight" if is_r2l else b"TwoPageLeft"
    else:
        page_layout = b"SinglePage"

    rgb_images: list[Image.Image] = []
    try:
        for path in image_paths:
            with Image.open(path) as img:
                rgb_images.append(img.convert("RGB"))

        first_img = rgb_images[0]
        rest_imgs = rgb_images[1:]

        with _PDF_LOCK:
            orig_write_catalog = PdfParser.PdfParser.write_catalog

            def custom_write_catalog(parser_self):
                assert parser_self.f is not None
                parser_self.del_root()
                parser_self.root_ref = parser_self.next_object_id(parser_self.f.tell())
                parser_self.pages_ref = parser_self.next_object_id(0)
                parser_self.rewrite_pages()
                parser_self.write_obj(
                    parser_self.root_ref,
                    Type=PdfParser.PdfName(b"Catalog"),
                    Pages=parser_self.pages_ref,
                    PageLayout=PdfParser.PdfName(page_layout),
                    ViewerPreferences=PdfParser.PdfDict(
                        {
                            b"Direction": PdfParser.PdfName(direction),
                            b"FitWindow": True,
                        }
                    ),
                )
                parser_self.write_obj(
                    parser_self.pages_ref,
                    Type=PdfParser.PdfName(b"Pages"),
                    Count=len(parser_self.pages),
                    Kids=parser_self.pages,
                )
                return parser_self.root_ref

            PdfParser.PdfParser.write_catalog = custom_write_catalog
            try:
                first_img.save(
                    save_path,
                    format="PDF",
                    save_all=True,
                    append_images=rest_imgs,
                )
            finally:
                PdfParser.PdfParser.write_catalog = orig_write_catalog
    finally:
        for im in rgb_images:
            try:
                im.close()
            except Exception:
                pass


def cleanup_temp_files(image_paths: list[str], temp_dir: str | None = None) -> None:
    """一時画像ファイルおよび空になった一時ディレクトリを安全に削除する"""
    for path in image_paths:
        try:
            if os.path.isfile(path):
                os.remove(path)
        except Exception:
            pass

    target_dir = temp_dir
    if not target_dir and image_paths:
        target_dir = os.path.dirname(image_paths[0])

    if target_dir and os.path.isdir(target_dir):
        try:
            if not os.listdir(target_dir):
                os.rmdir(target_dir)
        except Exception:
            pass


class RegionSelectorOverlay(tk.Toplevel):
    """マルチモニター全体を覆い、ドラッグで物理ピクセル領域を選択するオーバーレイ"""

    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self._finished = False

        # マルチモニター全画面の物理座標・サイズを取得 (Windows固有)
        if sys.platform == "win32":
            user32 = ctypes.windll.user32
            self.v_x = user32.GetSystemMetrics(76)  # SM_XVIRTUALSCREEN
            self.v_y = user32.GetSystemMetrics(77)  # SM_YVIRTUALSCREEN
            v_width = user32.GetSystemMetrics(78)   # SM_CXVIRTUALSCREEN
            v_height = user32.GetSystemMetrics(79)  # SM_CYVIRTUALSCREEN
        else:
            self.v_x = 0
            self.v_y = 0
            v_width = self.winfo_screenwidth()
            v_height = self.winfo_screenheight()

        if v_width <= 0 or v_height <= 0:
            self.v_x = 0
            self.v_y = 0
            v_width = self.winfo_screenwidth()
            v_height = self.winfo_screenheight()

        self.overrideredirect(True)
        # 負の座標（左・上配置のサブモニター）でも有効なTcl/Tkジオメトリ形式にする
        self.geometry(f"{v_width}x{v_height}{self.v_x:+d}{self.v_y:+d}")
        self.attributes("-alpha", 0.4)
        self.attributes("-topmost", True)
        self.config(cursor="cross")

        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<ButtonPress-3>", self.on_cancel)
        self.bind("<Escape>", self.on_cancel)
        self.canvas.bind("<Escape>", self.on_cancel)
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)

        self.start_x = None
        self.start_y = None
        self.start_root_x = None
        self.start_root_y = None
        self.rect = None

        self.lift()
        self.focus_force()
        self.canvas.focus_set()

    def _finish(self, result):
        if self._finished:
            return
        self._finished = True
        try:
            self.destroy()
        finally:
            self.callback(result)

    def on_cancel(self, event=None):
        self._finish(None)

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.start_root_x = event.x_root
        self.start_root_y = event.y_root
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, event.x, event.y, outline="red", width=3
        )

    def on_drag(self, event):
        if self.rect and self.start_x is not None and self.start_y is not None:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        if self.start_root_x is None or self.start_root_y is None:
            self._finish(None)
            return

        end_root_x = event.x_root
        end_root_y = event.y_root

        x = min(self.start_root_x, end_root_x)
        y = min(self.start_root_y, end_root_y)
        w = abs(end_root_x - self.start_root_x)
        h = abs(end_root_y - self.start_root_y)

        if w > 10 and h > 10:
            self._finish((int(x), int(y), int(w), int(h)))
        else:
            self._finish(None)


class PreviewWindow(ctk.CTkToplevel):
    """キャプチャ完了後のプレビュー＆PDF保存ウィンドウ"""

    DIR_OPTIONS = ["左綴じ (L2R) - 横書き用", "右綴じ (R2L) - 縦書き・漫画用"]
    LAYOUT_OPTIONS = ["単一ページ (Single)", "見開き表示 (Spread)"]

    def __init__(
        self,
        parent,
        image_paths: list[str],
        temp_dir: str,
        default_name: str,
        initial_dir: str | None = None,
        initial_layout: str | None = None,
        on_saved_callback=None,
    ):
        super().__init__(parent)
        self.image_paths = image_paths
        self.temp_dir = temp_dir
        self.default_name = default_name
        self.on_saved_callback = on_saved_callback
        self._thumbs = []  # GC防止用
        self._closed = False

        self.title("Preview & Save PDF")
        self.geometry("700x580")
        self.minsize(600, 500)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ---- サムネイルスクロールエリア ----
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, label_text=f"{len(image_paths)} pages captured"
        )
        self.scroll_frame.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="nsew")

        cols = 4
        for i, path in enumerate(image_paths):
            frame = ctk.CTkFrame(self.scroll_frame)
            frame.grid(row=i // cols, column=i % cols, padx=6, pady=6)

            try:
                # with文でファイルハンドルを即座に閉じ、Windowsでの削除ロックを防ぐ
                with Image.open(path) as raw_img:
                    thumb_img = raw_img.copy()
                    thumb_img.thumbnail((140, 140))
                ctk_img = ctk.CTkImage(
                    light_image=thumb_img,
                    dark_image=thumb_img,
                    size=thumb_img.size,
                )
                self._thumbs.append(ctk_img)
                lbl_img = ctk.CTkLabel(frame, image=ctk_img, text="")
            except Exception:
                lbl_img = ctk.CTkLabel(frame, text="[読込エラー]", width=100, height=100)

            lbl_img.pack(padx=4, pady=(4, 0))
            lbl_num = ctk.CTkLabel(frame, text=f"p.{i+1}", font=ctk.CTkFont(size=11))
            lbl_num.pack(pady=(0, 4))

        # ---- オプションエリア (PDF表示・綴じ設定) ----
        opts_frame = ctk.CTkFrame(self, fg_color="transparent")
        opts_frame.grid(row=1, column=0, padx=16, pady=(4, 4), sticky="ew")
        opts_frame.grid_columnconfigure(1, weight=1)
        opts_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(opts_frame, text="綴じ方向 (Direction):").grid(
            row=0, column=0, padx=(0, 10), pady=5, sticky="w"
        )
        self.combo_dir = ctk.CTkComboBox(
            opts_frame, values=self.DIR_OPTIONS, state="readonly"
        )
        self.combo_dir.grid(row=0, column=1, padx=(0, 20), pady=5, sticky="ew")
        if initial_dir in self.DIR_OPTIONS:
            self.combo_dir.set(initial_dir)
        else:
            self.combo_dir.set(self.DIR_OPTIONS[0])

        ctk.CTkLabel(opts_frame, text="表示レイアウト (Layout):").grid(
            row=0, column=2, padx=(0, 10), pady=5, sticky="w"
        )
        self.combo_layout = ctk.CTkComboBox(
            opts_frame, values=self.LAYOUT_OPTIONS, state="readonly"
        )
        self.combo_layout.grid(row=0, column=3, pady=5, sticky="ew")
        if initial_layout in self.LAYOUT_OPTIONS:
            self.combo_layout.set(initial_layout)
        else:
            self.combo_layout.set(self.LAYOUT_OPTIONS[0])

        # ---- ボタンエリア ----
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, padx=16, pady=(4, 16), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        self.lbl_info = ctk.CTkLabel(
            btn_frame, text="内容を確認してから保存場所を指定してください", text_color="gray"
        )
        self.lbl_info.grid(row=0, column=0, columnspan=2, pady=(0, 8))

        self.btn_cancel = ctk.CTkButton(
            btn_frame,
            text="閉じる（破棄）",
            fg_color="#3d3d3d",
            hover_color="#555",
            command=self._on_close,
        )
        self.btn_cancel.grid(row=1, column=0, padx=(0, 6), sticky="ew")

        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="保存場所を指定してPDF保存",
            fg_color="#2EA043",
            hover_color="#238636",
            command=self._on_save,
        )
        self.btn_save.grid(row=1, column=1, padx=(6, 0), sticky="ew")

        # モーダル化および最前面表示（CTkToplevelの遅延初期化対策込み）
        self.after(50, self._bring_to_front)
        self.after(250, self._bring_to_front)

    def _bring_to_front(self):
        if not self._closed and self.winfo_exists():
            try:
                self.grab_set()
                self.lift()
                self.focus_force()
            except Exception:
                pass

    def _on_save(self):
        if not self.image_paths:
            self.lbl_info.configure(text="エラー: 保存する画像がありません", text_color="#F85149")
            return

        save_path = filedialog.asksaveasfilename(
            parent=self,
            title="PDFの保存先を指定",
            initialfile=self.default_name,
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not save_path:
            return  # キャンセルされた場合は何もしない

        self.btn_save.configure(state="disabled")
        self.btn_cancel.configure(state="disabled")
        self.lbl_info.configure(text="PDF生成中...", text_color="#D29922")
        self.update_idletasks()

        dir_sel = self.combo_dir.get()
        layout_sel = self.combo_layout.get()
        is_r2l = "右綴じ" in dir_sel
        is_spread = "見開き" in layout_sel

        try:
            save_pdf_with_preferences(
                self.image_paths,
                save_path,
                is_r2l=is_r2l,
                is_spread=is_spread,
            )
            self.lbl_info.configure(
                text=f"保存完了: {os.path.basename(save_path)}", text_color="#2EA043"
            )
            self.btn_cancel.configure(text="閉じる")
            if self.on_saved_callback:
                self.on_saved_callback(save_path, dir_sel, layout_sel)
        except Exception as e:
            self.lbl_info.configure(text=f"エラー: {e}", text_color="#F85149")
        finally:
            if not self._closed and self.winfo_exists():
                self.btn_save.configure(state="normal")
                self.btn_cancel.configure(state="normal")

    def _on_close(self):
        if self._closed:
            return
        self._closed = True
        self._thumbs.clear()
        cleanup_temp_files(self.image_paths, self.temp_dir)
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()


class EbookCaptureApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("eBook to PDF Converter")
        self.geometry("400x500")
        self.minsize(380, 480)
        self.protocol("WM_DELETE_WINDOW", self._on_app_close)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)

        self.capture_region: tuple[int, int, int, int] | None = None
        self.is_capturing = False
        self.cancel_requested = False
        self._is_closing = False

        self.settings_file = os.path.join(BASE_DIR, "config.json")
        self._load_settings()
        self._build_ui()

    def _load_settings(self):
        """前回の設定を読み込む（不正なデータ形式に対するバリデーション付き）"""
        self.saved_data = {}
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    self.saved_data = loaded
            except Exception:
                self.saved_data = {}

        reg = self.saved_data.get("region")
        if (
            isinstance(reg, (list, tuple))
            and len(reg) == 4
            and all(isinstance(v, (int, float)) for v in reg)
            and reg[2] > 10
            and reg[3] > 10
        ):
            self.capture_region = (int(reg[0]), int(reg[1]), int(reg[2]), int(reg[3]))
        else:
            self.capture_region = None

    def _save_settings(
        self,
        direction: str | None = None,
        layout: str | None = None,
    ):
        """現在の設定をconfig.jsonに保存する"""
        data = {
            "filename": self.entry_filename.get().strip() or "book",
            "chapter": self.entry_chapter.get().strip() or "01",
            "pages": self.entry_pages.get().strip(),
            "interval": self.entry_interval.get().strip() or "1.5",
            "region": list(self.capture_region) if self.capture_region else None,
            "direction": direction or self.saved_data.get("direction", PreviewWindow.DIR_OPTIONS[0]),
            "layout": layout or self.saved_data.get("layout", PreviewWindow.LAYOUT_OPTIONS[0]),
        }
        self.saved_data = data
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to save settings: {e}")

    def _build_ui(self):
        # 1. Title
        title_lbl = ctk.CTkLabel(
            self, text="eBook to PDF Converter", font=ctk.CTkFont(size=20, weight="bold")
        )
        title_lbl.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 20), sticky="ew")

        # 2. File Name
        ctk.CTkLabel(self, text="File Name:", anchor="w").grid(
            row=1, column=0, padx=(20, 10), pady=10, sticky="ew"
        )
        self.entry_filename = ctk.CTkEntry(self, placeholder_text="e.g. bookname")
        self.entry_filename.grid(row=1, column=1, padx=(10, 20), pady=10, sticky="ew")
        self.entry_filename.insert(0, str(self.saved_data.get("filename", "book")))

        # 3. Chapter
        ctk.CTkLabel(self, text="Chapter:", anchor="w").grid(
            row=2, column=0, padx=(20, 10), pady=10, sticky="ew"
        )
        self.entry_chapter = ctk.CTkEntry(self, placeholder_text="e.g. 01")
        self.entry_chapter.grid(row=2, column=1, padx=(10, 20), pady=10, sticky="ew")
        self.entry_chapter.insert(0, str(self.saved_data.get("chapter", "01")))

        # 4. Total Pages
        ctk.CTkLabel(self, text="Total Pages:", anchor="w").grid(
            row=3, column=0, padx=(20, 10), pady=10, sticky="ew"
        )
        self.entry_pages = ctk.CTkEntry(self, placeholder_text="e.g. 50")
        self.entry_pages.grid(row=3, column=1, padx=(10, 20), pady=10, sticky="ew")
        self.entry_pages.insert(0, str(self.saved_data.get("pages", "")))

        # 5. Interval
        ctk.CTkLabel(self, text="Interval (sec):", anchor="w").grid(
            row=4, column=0, padx=(20, 10), pady=10, sticky="ew"
        )
        self.entry_interval = ctk.CTkEntry(self, placeholder_text="e.g. 1.5")
        self.entry_interval.insert(0, str(self.saved_data.get("interval", "1.5")))
        self.entry_interval.grid(row=4, column=1, padx=(10, 20), pady=10, sticky="ew")

        # Buttons Frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        self.btn_region = ctk.CTkButton(
            btn_frame, text="1. Select Region", command=self.start_region_selection
        )
        self.btn_region.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.btn_start = ctk.CTkButton(
            btn_frame,
            text="2. Start Capture",
            command=self.on_start_or_stop_button,
            fg_color="#2EA043",
            hover_color="#238636",
        )
        self.btn_start.grid(row=0, column=1, padx=(5, 0), sticky="ew")

        if self.capture_region:
            r = self.capture_region
            self.lbl_region = ctk.CTkLabel(
                self,
                text=f"Region: X: {r[0]}, Y: {r[1]}, W: {r[2]}, H: {r[3]}",
                text_color="#58A6FF",
            )
        else:
            self.lbl_region = ctk.CTkLabel(
                self, text="Region: Not selected", text_color="gray"
            )
        self.lbl_region.grid(row=6, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")

        # Progress & Status
        self.lbl_status = ctk.CTkLabel(
            self, text="Status: Ready", font=ctk.CTkFont(size=14)
        )
        self.lbl_status.grid(row=7, column=0, columnspan=2, padx=20, pady=(10, 5), sticky="ew")

        self.progressbar = ctk.CTkProgressBar(self)
        self.progressbar.grid(row=8, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        self.progressbar.set(0)

    def _safe_after(self, delay_ms: int, callback, *args):
        """ウィンドウ破棄後のTclErrorを防ぐ安全なafterラッパー"""
        if not self._is_closing and self.winfo_exists():
            try:
                self.after(delay_ms, callback, *args)
            except Exception:
                pass

    def _on_app_close(self):
        self._is_closing = True
        self.cancel_requested = True
        try:
            self._save_settings()
        except Exception:
            pass
        self.destroy()

    def start_region_selection(self):
        if self.is_capturing:
            return
        self.withdraw()
        self._safe_after(150, lambda: RegionSelectorOverlay(self, self.on_region_selected))

    def on_region_selected(self, rect):
        if self._is_closing:
            return
        if rect is not None:
            self.capture_region = rect
            self.lbl_region.configure(
                text=f"Region: X: {rect[0]}, Y: {rect[1]}, W: {rect[2]}, H: {rect[3]}",
                text_color="#58A6FF",
            )
            self._save_settings()
        self.deiconify()
        self.lift()
        self.focus_force()

    def on_start_or_stop_button(self):
        if self.is_capturing:
            self.cancel_requested = True
            self.auto_update_status("Stopping...", "#D29922")
        else:
            self.start_capture_thread()

    def start_capture_thread(self):
        if self.is_capturing:
            return

        if not self.capture_region:
            self.lbl_status.configure(text="Error: Missing region!", text_color="#F85149")
            return

        try:
            pages = int(self.entry_pages.get().strip())
            interval = float(self.entry_interval.get().strip())
            fname = sanitize_filename(self.entry_filename.get(), fallback="book")
            chapter = sanitize_filename(self.entry_chapter.get(), fallback="01")
            if pages <= 0 or interval < 0:
                raise ValueError
        except ValueError:
            self.lbl_status.configure(text="Error: Invalid Numbers!", text_color="#F85149")
            return

        self.is_capturing = True
        self.cancel_requested = False
        self.btn_region.configure(state="disabled")
        self.btn_start.configure(
            text="Stop Capture", fg_color="#D9383A", hover_color="#B62324"
        )
        self.progressbar.set(0)

        # 現在の設定を保存（章番号の自動加算はPDF保存完了時に行う）
        self._save_settings()

        thread = threading.Thread(
            target=self.capture_loop,
            args=(pages, interval, fname, chapter, self.capture_region),
            daemon=True,
        )
        thread.start()

    def auto_update_status(self, msg, color=None):
        if self._is_closing or not self.winfo_exists():
            return
        if color:
            self.lbl_status.configure(text=msg, text_color=color)
        else:
            self.lbl_status.configure(text=msg, text_color=("black", "white"))

    def _interruptible_sleep(self, duration: float):
        """待機中もFail-Safe（画面四隅へのマウス移動）と停止ボタンを50ms単位で監視する"""
        end_time = time.perf_counter() + duration
        while time.perf_counter() < end_time:
            if self.cancel_requested or self._is_closing:
                raise InterruptedError("Cancelled by user.")
            pyautogui.failSafeCheck()
            remaining = end_time - time.perf_counter()
            if remaining > 0:
                time.sleep(min(0.05, remaining))

    def _on_pdf_saved(self, save_path: str, direction: str, layout: str):
        """プレビュー画面でPDFが正常に保存された際、章番号を+1して設定を保存する"""
        if self._is_closing or not self.winfo_exists():
            return
        current_chapter = self.entry_chapter.get().strip()
        if current_chapter.isdigit():
            next_chapter = str(int(current_chapter) + 1).zfill(len(current_chapter))
            self.entry_chapter.delete(0, "end")
            self.entry_chapter.insert(0, next_chapter)
        self._save_settings(direction=direction, layout=layout)
        self.auto_update_status(
            f"Saved: {os.path.basename(save_path)}", "#2EA043"
        )

    def capture_loop(self, total_pages: int, interval: float, fname: str, chapter: str, region: tuple[int, int, int, int]):
        temp_dir = os.path.join(BASE_DIR, f"temp_{fname}_{chapter}")
        # 過去の中断ファイルが残っている場合は初期化して混入を防ぐ
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        os.makedirs(temp_dir, exist_ok=True)

        image_paths: list[str] = []
        preview_opened = False

        try:
            # カウントダウン（待機中もFail-Safeと停止ボタンが即座に効く）
            for i in range(5, 0, -1):
                self._safe_after(
                    0,
                    self.auto_update_status,
                    f"Starting in {i}... Focus eBook!",
                    "#D29922",
                )
                self._interruptible_sleep(1.0)

            self._safe_after(0, self.auto_update_status, "Capturing...", "#2EA043")

            for page in range(1, total_pages + 1):
                if self.cancel_requested or self._is_closing:
                    raise InterruptedError("Cancelled by user.")
                pyautogui.failSafeCheck()

                self._safe_after(
                    0,
                    self.auto_update_status,
                    f"Capturing page {page}/{total_pages}...",
                    "#58A6FF",
                )
                self._safe_after(0, self.progressbar.set, page / total_pages)

                # 最初は0.5秒待機して撮影、2ページ目以降は右矢印キーでめくってから待機
                if page > 1:
                    pyautogui.press("right")
                    self._interruptible_sleep(interval)
                else:
                    self._interruptible_sleep(0.5)

                pyautogui.failSafeCheck()
                bbox = (
                    region[0],
                    region[1],
                    region[0] + region[2],
                    region[1] + region[3],
                )
                img = ImageGrab.grab(bbox=bbox, all_screens=True)

                img_path = os.path.join(temp_dir, f"page_{page:04d}.png")
                img.save(img_path)
                img.close()
                image_paths.append(img_path)

            default_pdf_name = f"{fname}_{chapter}.pdf"
            preview_opened = True
            self._safe_after(
                0, self.auto_update_status, "Done! Opening preview...", "#2EA043"
            )
            self._safe_after(
                100,
                lambda: PreviewWindow(
                    self,
                    image_paths,
                    temp_dir,
                    default_pdf_name,
                    initial_dir=self.saved_data.get("direction"),
                    initial_layout=self.saved_data.get("layout"),
                    on_saved_callback=self._on_pdf_saved,
                ),
            )

        except pyautogui.FailSafeException:
            self._safe_after(
                0,
                self.auto_update_status,
                "Hit Edge! Cancelled by Fail-Safe.",
                "#F85149",
            )
        except InterruptedError:
            self._safe_after(
                0,
                self.auto_update_status,
                "Capture stopped by user.",
                "#D29922",
            )
        except Exception as e:
            self._safe_after(
                0, self.auto_update_status, f"Error: {str(e)}", "#F85149"
            )
        finally:
            if not preview_opened:
                cleanup_temp_files(image_paths, temp_dir)
            self.is_capturing = False
            self.cancel_requested = False
            self._safe_after(0, self._restore_buttons)

    def _restore_buttons(self):
        if self._is_closing or not self.winfo_exists():
            return
        self.btn_start.configure(
            state="normal",
            text="2. Start Capture",
            fg_color="#2EA043",
            hover_color="#238636",
        )
        self.btn_region.configure(state="normal")


if __name__ == "__main__":
    app = EbookCaptureApp()
    app.mainloop()
