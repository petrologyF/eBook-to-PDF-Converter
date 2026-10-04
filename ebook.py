import pyautogui
import time
import os
import sys
from PIL import Image

# --- 設定項目 ---

CHAPTER = "4"

# スクリーンショット(PNG)の保存先フォルダ
# 例: r"C:\Users\YourUser\Desktop\MyBook_PNGs"
PNG_SAVE_DIR = os.path.join(r"C:\Users\climb\OneDrive - 信州大学\デスクトップ\UE", CHAPTER)

# 出力するPDFのフルパス (フォルダ + ファイル名)
# 例: r"C:\Users\YourUser\Desktop\MyBook.pdf"
PDF_SAVE_PATH = os.path.join(r"C:\Users\climb\OneDrive - 信州大学\ドキュメント\TextBook\Understanding Earth", f"UE_{CHAPTER}.pdf")

# スクリーンショットを撮影する枚数
NUM_PAGES = 18

# 1ページ撮影してから次のページへ移動するまでの待機時間（秒）
# ページの読み込みが遅い場合は、この時間を長くしてください
INTERVAL = 1.5

# スクリーンショットを撮影する範囲 (左上のX座標, 左上のY座標, 幅, 高さ)
# 事前に撮影したい電子書籍のウィンドウ範囲を確認し、設定してください。
# X1, Y1: 範囲の左上隅の座標
# X2, Y2: 範囲の右下隅の座標
X1 = 220
Y1 = 124
X2 = 2342
Y2 = 1481
CAPTURE_REGION = (X1, Y1, X2 - X1, Y2 - Y1)

# 出力するPDFの解像度(DPI)。一般的な印刷品質は300.0です。
RESOLUTION_DPI = 500.0

# --- PDF表示・綴じ設定 ---
# 綴じ方向: "l2r" (左綴じ/横書き) または "r2l" (右綴じ/縦書き・漫画)
DIRECTION = "l2r"

# ページレイアウト: "single" (1ページ表示) または "tworight" (見開き・右綴じ用) または "twoleft" (見開き・左綴じ用)
PAGE_LAYOUT = "single"

# -----------------

def take_screenshots(save_dir, num_pages, interval, region):
    """
    指定された範囲のスクリーンショットを連続で撮影する関数
    """
    # 保存先ディレクトリがなければ作成
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # 開始前のカウントダウン
    for i in range(5, 0, -1):
        print(f"撮影開始まで {i} 秒...", end="\r")
        time.sleep(1)
    # カウントダウン表示をクリア
    print(" " * 30, end="\r")

    try:
        for i in range(num_pages):
            page_num = i + 1
            filename = f"page_{page_num:03d}.png"
            save_path = os.path.join(save_dir, filename)

            # スクリーンショットを撮影
            screenshot = pyautogui.screenshot(region=region)
            
            # ファイルに保存
            screenshot.save(save_path)

            # 最後のページでなければ、ページをめくる
            if i < num_pages - 1:
                pyautogui.press('right')
                time.sleep(interval)

    except pyautogui.FailSafeException:
        print("\n**緊急停止**")
        print("マウスカーソルが画面の隅に移動したため、処理を中断しました。")
        sys.exit()
    except Exception as e:
        print(f"\nエラーが発生したため、処理を中断しました: {e}")
        sys.exit()

def convert_png_to_pdf(png_folder_path, pdf_file_path, resolution_dpi):
    """
    指定されたフォルダ内のPNG画像を1つのPDFファイルに変換する関数
    """
    try:
        files = [f for f in os.listdir(png_folder_path) if f.lower().endswith('.png')]
        files.sort()
        
        if not files:
            print(f"\n指定されたフォルダにPNGファイルが見つかりませんでした: {png_folder_path}")
            return

    except FileNotFoundError:
        print(f"\nエラー: 指定されたフォルダが見つかりません: {png_folder_path}")
        return

    image_list = []
    
    try:
        # 最初の画像を開き、RGBに変換
        first_image_path = os.path.join(png_folder_path, files[0])
        img1 = Image.open(first_image_path)
        if img1.mode == 'RGBA':
            img1 = img1.convert('RGB')
        
        # 残りの画像を処理
        for i in range(1, len(files)):
            file_path = os.path.join(png_folder_path, files[i])
            img = Image.open(file_path)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            image_list.append(img)

    except Exception as e:
        print(f"画像の処理中にエラーが発生しました: {e}")
        return

    try:
        # PDF出力先のフォルダが存在しない場合は作成
        pdf_folder = os.path.dirname(pdf_file_path)
        if not os.path.exists(pdf_folder):
            os.makedirs(pdf_folder)
            
        img1.save(pdf_file_path, "PDF", resolution=resolution_dpi, save_all=True, append_images=image_list)
        
    except Exception as e:
        print(f"PDFの保存中にエラーが発生しました: {e}")

def optimize_pdf_layout(pdf_file_path, direction="l2r", layout="single"):
    """
    pypdfを使って、PDFの表示設定（1ページ表示/フィット表示/綴じ方向）を最適化する
    """
    try:
        from pypdf import PdfReader, PdfWriter
        
        reader = PdfReader(pdf_file_path)
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
            
        writer.create_viewer_preferences()
        writer.viewer_preferences.fit_window = True
        
        if direction == "r2l":
            writer.viewer_preferences.direction = "/R2L"
            if layout == "tworight":
                writer.page_layout = "/TwoPageRight"
            else:
                writer.page_layout = "/SinglePage"
        else:
            writer.viewer_preferences.direction = "/L2R"
            if layout == "twoleft":
                writer.page_layout = "/TwoPageLeft"
            else:
                writer.page_layout = "/SinglePage"
                
        with open(pdf_file_path, "wb") as f:
            writer.write(f)
            
        print("PDFの表示設定（綴じ方向・レイアウト）を最適化しました。")
    except Exception as e:
        print(f"PDF表示設定の最適化中にエラーが発生しました: {e}")

def main():
    """
    メイン処理
    """
    pyautogui.FAILSAFE = True
    
    take_screenshots(
        save_dir=PNG_SAVE_DIR,
        num_pages=NUM_PAGES,
        interval=INTERVAL,
        region=CAPTURE_REGION
    )

    convert_png_to_pdf(
        png_folder_path=PNG_SAVE_DIR,
        pdf_file_path=PDF_SAVE_PATH,
        resolution_dpi=RESOLUTION_DPI
    )
    
    # PDF表示・綴じ設定の適用
    optimize_pdf_layout(
        pdf_file_path=PDF_SAVE_PATH,
        direction=DIRECTION,
        layout=PAGE_LAYOUT
    )

if __name__ == "__main__":
    main()

