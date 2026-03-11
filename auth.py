import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Streamlit Cloud (st.secrets) or Local (.env)
if hasattr(st, "secrets") and "ADMIN_PASSWORD" in st.secrets:
    ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
else:
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secret")

def authenticate():
    """環境変数を用いた簡易パスワード認証"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("## 🔒 Login")
        st.write("日記アプリにアクセスするためにパスワードを入力してください。")
        pwd = st.text_input("管理者パスワード", type="password")
        if st.button("ログイン", use_container_width=True):
            if pwd == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("パスワードが一致しません")
        st.stop()
