import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import numpy as np
from pdf2image import convert_from_bytes
from PIL import Image
import io
import base64
import tempfile
import os
from streamlit_drawable_canvas import st_canvas
import time

# アプリケーションのタイトルと説明
st.set_page_config(page_title="PDF抽出システム", layout="wide")
st.title("PDF抽出システム")
st.markdown("複数のPDFファイルから特定座標のテキストを抽出します")

# セッション状態の初期化
if 'coords' not in st.session_state:
    st.session_state.coords = None
if 'extraction_results' not in st.session_state:
    st.session_state.extraction_results = []
if 'pdf_files' not in st.session_state:
    st.session_state.pdf_files = None
if 'first_pdf_image' not in st.session_state:
    st.session_state.first_pdf_image = None
if 'canvas_result' not in st.session_state:
    st.session_state.canvas_result = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

# サイドバーの設定
st.sidebar.header("操作パネル")
step = st.sidebar.radio(
    "ステップ",
    ["1. PDFアップロード", "2. 座標指定", "3. テキスト抽出", "4. 結果表示"]
)

# PDFファイルから座標に基づいてテキストを抽出する関数
def extract_text_from_pdf(pdf_file, coords):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(pdf_file.getvalue())
            tmp_path = tmp.name
        
        doc = fitz.open(tmp_path)
        if doc.page_count > 0:
            page = doc[0]  # 1ページ目を取得
            
            # 座標変換（キャンバスの座標からPDF座標に）
            # ここではシンプルな例として、画像サイズとPDFサイズの比率で変換
            img_width, img_height = st.session_state.first_pdf_image.size
            pdf_width, pdf_height = page.rect.width, page.rect.height
            
            scale_x = pdf_width / img_width
            scale_y = pdf_height / img_height
            
            x1 = coords["left"] * scale_x
            y1 = coords["top"] * scale_y
            x2 = (coords["left"] + coords["width"]) * scale_x
            y2 = (coords["top"] + coords["height"]) * scale_y
            
            # 指定された領域からテキストを抽出
            rect = fitz.Rect(x1, y1, x2, y2)
            text = page.get_text("text", clip=rect)
            
            # 一時ファイルを削除
            doc.close()
            os.unlink(tmp_path)
            
            return text.strip()
        else:
            return "PDFにページがありません"
    except Exception as e:
        return f"エラー: {str(e)}"

# ステップ1: PDFファイルのアップロード
if step == "1. PDFアップロード":
    st.header("PDFファイルのアップロード")
    
    uploaded_files = st.file_uploader(
        "複数のPDFファイルをアップロードしてください", 
        type="pdf", 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.session_state.pdf_files = uploaded_files
        st.success(f"{len(uploaded_files)}個のPDFファイルがアップロードされました")
        
        # 最初のPDFを画像に変換して表示
        try:
            with st.spinner("最初のPDFを処理中..."):
                images = convert_from_bytes(uploaded_files[0].getvalue(), first_page=1, last_page=1)
                if images:
                    st.session_state.first_pdf_image = images[0]
                    st.image(st.session_state.first_pdf_image, caption="最初のPDF - 1ページ目", use_column_width=True)
                else:
                    st.error("PDFの変換に失敗しました")
        except Exception as e:
            st.error(f"PDFの処理中にエラーが発生しました: {str(e)}")
    
    if st.session_state.pdf_files:
        if st.button("次へ: 座標指定"):
            # 次のステップに移動
            st.experimental_rerun()

# ステップ2: 座標の指定
elif step == "2. 座標指定":
    st.header("テキスト抽出の座標を指定")
    
    if st.session_state.pdf_files is None:
        st.warning("PDFファイルがアップロードされていません。ステップ1に戻ってください。")
    elif st.session_state.first_pdf_image is None:
        st.warning("PDFの画像変換に失敗しました。ステップ1に戻ってください。")
    else:
        st.write("1ページ目に表示されている最初のPDFから、抽出したいテキスト領域を四角形で囲んでください。")
        
        # 画像サイズを取得
        img_width, img_height = st.session_state.first_pdf_image.size
        
        # 描画可能なキャンバスを作成
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=2,
            stroke_color="#FF0000",
            background_image=st.session_state.first_pdf_image,
            update_streamlit=True,
            height=img_height,
            width=img_width,
            drawing_mode="rect",
            key="canvas",
        )
        
        # キャンバスの結果を保存
        if canvas_result.json_data is not None and len(canvas_result.json_data["objects"]) > 0:
            st.session_state.canvas_result = canvas_result.json_data
            # 最後に描画された四角形の座標を取得
            last_rect = canvas_result.json_data["objects"][-1]
            st.session_state.coords = last_rect
            
            st.success("座標が指定されました")
            st.write(f"指定座標: X={last_rect['left']:.1f}, Y={last_rect['top']:.1f}, 幅={last_rect['width']:.1f}, 高さ={last_rect['height']:.1f}")
        
        if st.session_state.coords:
            if st.button("次へ: テキスト抽出"):
                st.experimental_rerun()

# ステップ3: テキスト抽出処理
elif step == "3. テキスト抽出":
    st.header("テキスト抽出処理")
    
    if st.session_state.pdf_files is None:
        st.warning("PDFファイルがアップロードされていません。ステップ1に戻ってください。")
    elif st.session_state.coords is None:
        st.warning("座標が指定されていません。ステップ2に戻ってください。")
    else:
        if not st.session_state.processing_complete:
            # 抽出処理を実行
            if st.button("抽出開始"):
                extraction_results = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, pdf_file in enumerate(st.session_state.pdf_files):
                    # 進捗状況の更新
                    progress = (i + 1) / len(st.session_state.pdf_files)
                    progress_bar.progress(progress)
                    status_text.text(f"処理中: {i+1}/{len(st.session_state.pdf_files)} - {pdf_file.name}")
                    
                    # テキスト抽出
                    text = extract_text_from_pdf(pdf_file, st.session_state.coords)
                    
                    # 結果を追加
                    extraction_results.append({
                        "ファイル名": pdf_file.name,
                        "抽出テキスト": text
                    })
                    
                    # わずかな遅延（UIの更新のため）
                    time.sleep(0.1)
                
                st.session_state.extraction_results = extraction_results
                st.session_state.processing_complete = True
                status_text.text("処理完了!")
                st.success("すべてのPDFからテキスト抽出が完了しました")
                st.experimental_rerun()
        else:
            st.success("テキスト抽出が完了しています")
            if st.button("結果を表示"):
                st.experimental_rerun()

# ステップ4: 結果表示
elif step == "4. 結果表示":
    st.header("抽出結果")
    
    if not st.session_state.extraction_results:
        st.warning("テキストが抽出されていません。ステップ3に戻ってください。")
    else:
        # 結果をデータフレームに変換
        df = pd.DataFrame(st.session_state.extraction_results)
        
        # データフレームの表示
        st.dataframe(df)
        
        # CSVダウンロードボタン
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="extraction_results.csv">CSVファイルをダウンロード</a>'
        st.markdown(href, unsafe_allow_html=True)
        
        # 新しい抽出を開始するオプション
        if st.button("新しい抽出を開始"):
            # セッション状態をリセット
            for key in st.session_state.keys():
                del st.session_state[key]
            st.experimental_rerun()
