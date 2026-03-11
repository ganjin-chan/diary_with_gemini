import os
import firebase_admin
from firebase_admin import credentials, firestore
import streamlit as st
from datetime import datetime, timedelta, timezone

@st.cache_resource
def get_db():
    """Firestoreの初期化とクライアント取得"""
    if not firebase_admin._apps:
        # Streamlit Deploy (st.secrets)
        if hasattr(st, "secrets") and "firebase" in st.secrets:
            import json
            # st.secrets("firebase") is an AttrDict, we can convert it to a dict
            cert_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cert_dict)
            firebase_admin.initialize_app(cred)
        else:
            # Local deployment (.env)
            cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
            if cred_path and os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            else:
                firebase_admin.initialize_app()
    return firestore.client()

try:
    db = get_db()
except Exception as e:
    st.error(f"データベースの初期化に失敗しました: {e}")
    st.stop()

def add_entry(content, tags):
    """日記をFirestoreへ保存"""
    db.collection("entries").add({
        "content": content,
        "tags": tags,
        "createdAt": firestore.SERVER_TIMESTAMP
    })

def get_all_entries():
    """すべての日記を日付の降順で取得"""
    docs = db.collection("entries").order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def get_recent_entries(days=7):
    """直近指定日数の日記を取得"""
    dt = datetime.now(timezone.utc) - timedelta(days=days)
    docs = db.collection("entries").where(filter=firestore.FieldFilter("createdAt", ">=", dt)) \
                                   .order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def delete_entry(doc_id):
    """指定した日記を削除"""
    db.collection("entries").document(doc_id).delete()
