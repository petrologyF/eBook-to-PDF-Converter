import customtkinter as ctk
import pyautogui
import time
import os
import threading
from PIL import Image

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")
pyautogui.FAILSAFE = True

class RegionSelectorOverlay(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        
        self.attributes('-fullscreen', True)
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
        x = min(self.start_x, end_x)
        y = min(self.start_y, end_y)
        w = abs(end_x - self.start_x)
        h = abs(end_y - self.start_y)
        
        self.destroy()
        
        if w > 10 and h > 10:
            self.callback((x, y, w, h))


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
        
        self._build_ui()
        
    def _build_ui(self):
        # 1. Title
        title_lbl = ctk.CTkLabel(self, text="eBook to PDF Converter", font=ctk.CTkFont(size=20, weight="bold"))
        title_lbl.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 20), sticky="ew")
        
        # 2. File Name
        ctk.CTkLabel(self, text="File Name:", anchor="w").grid(row=1, column=0, padx=(20, 10), pady=10, sticky="ew")
        self.entry_filename = ctk.CTkEntry(self, placeholder_text="e.g. bookname")
        self.entry_filename.grid(row=1, column=1, padx=(10, 20), pady=10, sticky="ew")
        self.entry_filename.insert(0, "book")
        
        # 3. Chapter
        ctk.CTkLabel(self, text="Chapter:", anchor="w").grid(row=2, column=0, padx=(20, 10), pady=10, sticky="ew")
        self.entry_chapter = ctk.CTkEntry(self, placeholder_text="e.g. 01")
        self.entry_chapter.grid(row=2, column=1, padx=(10, 20), pady=10, sticky="ew")
        self.entry_chapter.insert(0, "01")
        
        # 4. Total Pages
        ctk.CTkLabel(self, text="Total Pages:", anchor="w").grid(row=3, column=0, padx=(20, 10), pady=10, sticky="ew")
        self.entry_pages = ctk.CTkEntry(self, placeholder_text="e.g. 50")
        self.entry_pages.grid(row=3, column=1, padx=(10, 20), pady=10, sticky="ew")
        
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
                
                img = pyautogui.screenshot(region=region)
                img_path = os.path.join(temp_dir, f"page_{page:04d}.png")
                img.save(img_path)
                image_paths.append(img_path)
                
            # PDF結合
            self.after(0, self.auto_update_status, "Compiling PDF...", "#D29922")
            pdf_path = f"{fname}_{chapter}.pdf"
            self.compile_pdf(image_paths, pdf_path)
            
            # クリーンナップ
            for path in image_paths:
                os.remove(path)
            os.rmdir(temp_dir)
            
            self.after(0, self.auto_update_status, f"Done! Saved: {pdf_path}", "#2EA043")
            
        except pyautogui.FailSafeException:
            self.after(0, self.auto_update_status, "Hit Edge! Cancelled by Fail-Safe.", "#F85149")
        except Exception as e:
            self.after(0, self.auto_update_status, f"Error: {str(e)}", "#F85149")
        finally:
            self.is_capturing = False
            self.after(0, self.btn_start.configure, state="normal")
            self.after(0, self.btn_region.configure, state="normal")

    def compile_pdf(self, image_paths, output_pdf):
        if not image_paths:
            return
            
        images = []
        first_image = Image.open(image_paths[0]).convert('RGB')
        
        for path in image_paths[1:]:
            img = Image.open(path).convert('RGB')
            images.append(img)
            
        first_image.save(output_pdf, save_all=True, append_images=images)


if __name__ == "__main__":
    app = EbookCaptureApp()
    app.mainloop()
