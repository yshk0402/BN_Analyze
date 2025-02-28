# PDF抽出システム

複数のPDFファイルから特定座標のテキストを抽出し、表形式で出力するWebアプリケーションです。

## 機能

- 複数のPDFファイルを同時にアップロード可能
- ドラッグ操作で抽出したい文字領域を視覚的に指定
- 各PDFの1ページ目から指定領域のテキストを抽出
- 結果を表形式で表示・CSVダウンロード

## 使い方

1. **PDFアップロード**: 複数のPDFファイルをアップロードします
2. **座標指定**: 表示された最初のPDFで、抽出したいテキスト領域を赤い四角形で囲みます
3. **テキスト抽出**: 「抽出開始」ボタンをクリックして処理を実行します
4. **結果表示**: 抽出結果を表形式で確認し、CSVでダウンロードできます

## インストール方法

### ローカル環境での実行

```bash
# リポジトリのクローン
git clone https://github.com/your-username/pdf-extractor.git
cd pdf-extractor

# 必要なライブラリのインストール
pip install -r requirements.txt

# アプリケーションの実行
streamlit run app.py
```

### デプロイ方法

このリポジトリは[Streamlit Cloud](https://streamlit.io/cloud)で簡単にデプロイできます。
Streamlit Cloudアカウントを作成し、このリポジトリを連携するだけです。

## 技術仕様

- **フレームワーク**: Streamlit
- **PDF処理**: PyMuPDF (fitz)
- **画像処理**: pdf2image, Pillow
- **データ処理**: pandas, numpy
- **UI操作**: streamlit-drawable-canvas

## 注意事項

- PDFによってはテキスト抽出が難しい場合があります（画像ベースのPDFなど）
- 大量のPDFを処理する場合は処理時間がかかる場合があります
