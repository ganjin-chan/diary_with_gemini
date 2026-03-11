import streamlit as st
import os

from auth import authenticate
from database import get_all_entries, get_recent_entries
from views import write_diary_ui, list_diaries_ui, weekly_summary_ui, relationship_tree_ui

# Streamlitのページ設定
st.set_page_config(page_title="My Diary", page_icon="📓", layout="centered")

def main():
    # パスワード認証
    authenticate()
    
    st.title("My Diary 📱")
    
    # データを一括で取得
    entries = get_all_entries()
    
    # APIキーの有無確認
    has_api_key = False
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        has_api_key = True
    elif os.getenv("GEMINI_API_KEY"):
        has_api_key = True
    
    # モバイル向けの1カラムナビゲーション
    nav_options = ["✏️ 日記を書く", "📚 日記一覧", "📊 一週間のまとめ", "🕸 関係性ツリー"]
    current_nav = st.selectbox("メニュー", nav_options)
    st.divider()
    
    if current_nav == "✏️ 日記を書く":
        write_diary_ui(entries)
    elif current_nav == "📚 日記一覧":
        list_diaries_ui(entries)
    elif current_nav == "📊 一週間のまとめ":
        recent_entries = get_recent_entries(days=7)
        weekly_summary_ui(recent_entries, has_api_key)
    elif current_nav == "🕸 関係性ツリー":
        relationship_tree_ui(entries, has_api_key)

if __name__ == "__main__":
    main()
