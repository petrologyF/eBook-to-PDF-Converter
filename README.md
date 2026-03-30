# eBook to PDF Universal Toolset 📚✨

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg?logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-Ready-blue.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/License-Private_Use-orange.svg)](LICENSE)

電子書籍の閲覧画面を自動でキャプチャし、高品質なPDFへと変換するための統合ツールセットです。
デスクトップGUI、軽量CLI、そしてブラウザ完結型のPWAの3つのエディションを提供します。

---

## 🚀 選べる3つのエディション

| エディション | ファイル/ディレクトリ | 推奨ユーザー | 特徴 |
| :--- | :--- | :--- | :--- |
| **💻 Desktop GUI** | `ebook_gui.py` | 初心者〜一般 | 直感的な範囲選択、ページプレビュー、DPI補正 |
| **🌐 Web PWA** | `ebook-pwa/` | インストール不要 | ブラウザの画面共有APIを利用、OSを問わず動作 |
| **📜 CLI (Legacy)** | `ebook.py` | 上級者 | スクリプトによる細かい制御、軽量動作 |

---

## 💻 Desktop GUI (推奨)

最も多機能で使いやすい標準版です。

### 主な機能
- **直感的な範囲選択**: 画面上をドラッグしてキャプチャ範囲をシ覚的に指定。
- **マルチモニター・DPI対応**: Windowsの表示倍率（150%等）や複数画面環境でも座標がズレません。
- **キャプチャ後のプレビュー**: 保存前に全ページを確認。不要なページがあれば削除（破棄）可能。
- **自動ページめくり**: `Right`キーエミュレーションによる全自動キャプチャ。

### 使い方
1. 依存ライブラリをインストール:
   ```bash
   pip install customtkinter pyautogui pillow
   ```
2. アプリを起動:
   ```bash
   python ebook_gui.py
   ```
3. 「Select Region」で範囲を指定し、「Start Capture」で開始。

---

## 🌐 Web PWA Edition

Next.jsで構築された最新のブラウザ版です。

### 特徴
- **インストール不要**: ブラウザ上で動作するため、環境構築の手間が最小限。
- **Screen Capture API**: ブラウザ標準の画面共有機能を利用して特定のウィンドウをキャプチャ。
- **レスポンシブ**: モバイルデバイス等からの操作も考慮した設計。

### 開発・実行
```bash
cd ebook-pwa
npm install
npm run dev
```

---

## 📜 CLI Edition (Legacy)

最小限の構成で動作するスクリプト版です。

### 使い方
1. `ebookmouse.py` で座標を確認。
2. `ebook.py` のソース冒頭の設定値（座標、ページ数、保存先）を書き換え。
3. `python ebook.py` を実行。

---

## ⚠️ 重要事項・トラブルシューティング

### 🚨 緊急停止 (Fail-Safe)
デスクトップ版（GUI/CLI）でプログラムが予期せぬ動きをした場合は、**マウスカーソルを画面の四隅（特に左上）に素早く移動**させてください。ライブラリの安全装置が働き、即座に停止します。

### 🛠️ キャプチャがうまくいかない場合
*   **ページめくり速度**: `Interval`（待機時間）を少し長め（1.5s〜2.5s）に設定してください。
*   **ウィンドウのフォーカス**: カウントダウン中に必ず電子書籍ビューアーを最前面にしてください。
*   **DPI設定**: GUI版では自動補正されますが、CLI版では座標がズレることがあります。その場合はGUI版の使用を推奨します。

---

## ⚖️ 免責事項 (Disclaimer)

*   **著作権**: 本ツールは個人のバックアップおよび私的利用（著作権法第30条）を目的に作成されています。作成したPDFの配布・共有、商用利用は厳禁です。
*   **自己責任**: 本ツールの利用により生じたいかなる損害についても、作者は一切の責任を負いません。

---

## 🛠️ 技術スタック
- **Python**: `CustomTkinter` (Modern UI), `Pillow` (Image Processing), `pyautogui` (Automation)
- **Web**: `Next.js`, `Tailwind CSS`, `Lucide React`, `hooks`
- **Build**: `PyInstaller` 対応済み (`ebook_gui.spec`)