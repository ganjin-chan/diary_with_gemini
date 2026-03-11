import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Streamlit Cloud (st.secrets) or Local (.env)
def get_admin_password():
    if hasattr(st, "secrets"):
        if "ADMIN_PASSWORD" in st.secrets:
            return str(st.secrets["ADMIN_PASSWORD"]).strip()
        # [firebase] セクション内に誤って入れてしまった場合も考慮
        if "firebase" in st.secrets and "ADMIN_PASSWORD" in st.secrets["firebase"]:
            return str(st.secrets["firebase"]["ADMIN_PASSWORD"]).strip()
    
    return os.getenv("ADMIN_PASSWORD", "secret").strip()

ADMIN_PASSWORD = get_admin_password()

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
