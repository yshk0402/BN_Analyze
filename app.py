import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import base64
import tempfile
import os
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
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

# サイドバーの設定
st.sidebar.header("操作パネル")
step = st.sidebar.radio(
    "ステップ",
    ["1. PDFアップロード", "2. 座標指定", "3. テキスト抽出", "4. 結果表示"]
)

# PDFの最初のページ情報を取得する関数
def get_pdf_first_page_info(pdf_file):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(pdf_file.getvalue())
            tmp_path = tmp.name
        
        doc = fitz.open(tmp_path)
        if doc.page_count > 0:
            page = doc[0]  # 1ページ目を取得
            width = page.rect.width
            height = page.rect.height
            # 一時ファイルを削除
            doc.close()
            os.unlink(tmp_path)
            return True, width, height
        else:
            return False, 0, 0
    except Exception as e:
        return False, 0, 0

# PDFファイルから座標に基づいてテキストを抽出する関数
def extract_text_from_pdf(pdf_file, coords):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            tmp.write(pdf_file.getvalue())
            tmp_path = tmp.name
        
        doc = fitz.open(tmp_path)
        if doc.page_count > 0:
            page = doc[0]  # 1ページ目を取得
            
            # 指定された領域からテキストを抽出
            x1, y1, x2, y2 = coords
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
        
        # 最初のPDFの情報を取得して表示
        success, width, height = get_pdf_first_page_info(uploaded_files[0])
        if success:
            st.info(f"最初のPDFの1ページ目サイズ: 幅={width:.1f}pt, 高さ={height:.1f}pt")
            st.session_state.pdf_dimensions = (width, height)
        else:
            st.error("PDFの情報取得に失敗しました")
    
    if st.session_state.pdf_files:
        if st.button("次へ: 座標指定"):
            st.rerun()

# ステップ2: 座標の指定
elif step == "2. 座標指定":
    st.header("テキスト抽出の座標を指定")
    
    if st.session_state.pdf_files is None:
        st.warning("PDFファイルがアップロードされていません。ステップ1に戻ってください。")
    else:
        st.write("テキストを抽出したい座標を入力してください (PDFの座標系を使用)")
        
        # PDFのサイズ情報があれば表示
        if 'pdf_dimensions' in st.session_state:
            width, height = st.session_state.pdf_dimensions
            st.info(f"PDFサイズ参考情報: 幅={width:.1f}pt, 高さ={height:.1f}pt")
        
        col1, col2 = st.columns(2)
        with col1:
            x1 = st.number_input("左上 X座標", value=100.0, step=10.0)
            y1 = st.number_input("左上 Y座標", value=100.0, step=10.0)
        
        with col2:
            x2 = st.number_input("右下 X座標", value=300.0, step=10.0)
            y2 = st.number_input("右下 Y座標", value=150.0, step=10.0)
        
        st.info("ヒント: PDFの座標は左上が原点(0,0)で、右下に向かって値が大きくなります。")
        st.write(f"指定座標: 左上=({x1}, {y1}), 右下=({x2}, {y2})")
        
        if st.button("次へ: テキスト抽出"):
            # 座標を保存して次へ
            st.session_state.coords = (x1, y1, x2, y2)
            st.rerun()

# ステップ3: テキスト抽出処理
elif step == "3. テキスト抽出":
    st.header("テキスト抽出処理")
    
    if st.session_state.pdf_files is None:
        st.warning("PDFファイルがアップロードされていません。ステップ1に戻ってください。")
    elif 'coords' not in st.session_state:
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
                st.rerun()
        else:
            st.success("テキスト抽出が完了しています")
            if st.button("結果を表示"):
                st.rerun()

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
            st.rerun()
