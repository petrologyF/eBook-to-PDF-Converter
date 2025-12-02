import pyautogui
import time

print("マウスの現在座標を取得します。")
print("カーソルを動かすとリアルタイムで座標が表示されます。")
print("スクリーンショットを撮りたい領域の「左上」と「右下」に")
print("それぞれカーソルを合わせて座標をメモしてください。")
print("（Ctrl + C でプログラムを終了します）")
print("-" * 30)

try:
    while True:
        # 現在のマウスのX座標とY座標を取得
        x, y = pyautogui.position()
        
        # 座標を整形して表示
        # .ljust()で文字列の長さを固定し、表示のガタつきを防ぐ
        position_str = f"X: {x}  Y: {y}".ljust(20)
        print(position_str, end='\r') # \rで行の先頭に戻り、上書き表示する
        
        # 待機時間を0.1秒に短縮し、よりスムーズに更新
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nプログラムを終了しました。")