import streamlit as st
import json
from datetime import timezone, timedelta

JST = timezone(timedelta(hours=9), 'JST')

def get_jst_string(dt):
    if not dt or not hasattr(dt, 'strftime'):
        return "日時不明"
    if dt.tzinfo is not None:
        return dt.astimezone(JST).strftime("%Y-%m-%d %H:%M")
    return (dt + timedelta(hours=9)).strftime("%Y-%m-%d %H:%M")

try:
    from streamlit_agraph import agraph, Node, Edge, Config
except ImportError:
    pass

from database import add_entry, delete_entry
from ai_agent import generate_weekly_summary, extract_relationship_graph

def write_diary_ui(entries):
    st.subheader("📝 日記を書く")
    
    content = st.text_area("今日の出来事や思考、感情を記録しましょう。", height=150)
    
    all_tags = set()
    for e in entries:
        all_tags.update(e.get("tags", []))
    
    selected_tags = st.multiselect("🏷 既存のタグを選択", list(all_tags))
    new_tags_input = st.text_input("➕ 新しいタグ（カンマ \",\" 区切りで複数入力可）")
    
    if st.button("保存する", type="primary", use_container_width=True):
        if not content.strip():
            st.warning("本文を入力してください。")
            return
            
        tags = list(selected_tags)
        if new_tags_input.strip():
            new_tags = [t.strip() for t in new_tags_input.split(",") if t.strip()]
            tags.extend(new_tags)
            
        tags = list(set(tags))
        add_entry(content, tags)
        st.success("日記を保存しました！")
        st.rerun()

def list_diaries_ui(entries):
    st.subheader("📚 日記一覧")
    
    if not entries:
        st.info("まだ日記がありません。最初の記録を書いてみましょう。")
        return

    all_tags = set()
    for e in entries:
        all_tags.update(e.get("tags", []))
        
    filter_tags = st.multiselect("🔍 タグで絞り込み", list(all_tags))
    
    for entry in entries:
        tags = entry.get("tags", [])
        if filter_tags and not any(t in filter_tags for t in tags):
            continue
            
        with st.container(border=True):
            created_at = entry.get("createdAt")
            date_str = get_jst_string(created_at)
            
            st.caption(f"🗓 {date_str}")
            st.markdown(entry.get("content", ""))
            
            if tags:
                html_tags = " ".join([f"<span style='background-color:#F0F2F6; padding:4px 8px; border-radius:12px; font-size:12px; color:#31333F;'>#{t}</span>" for t in tags])
                st.markdown(html_tags, unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("🗑 削除", key=f"del_{entry['id']}", use_container_width=True):
                    delete_entry(entry["id"])
                    st.rerun()

def weekly_summary_ui(recent_entries, has_api_key):
    st.subheader("📊 一週間のまとめ")
    st.write("直近7日間の日記データを元に、AIがハイライトと感情の傾向を分析します。")
    
    if st.button("✨ サマリーを生成する", use_container_width=True):
        if not has_api_key:
            st.error("環境変数 `GEMINI_API_KEY` が設定されていません。")
            return

        if not recent_entries:
            st.warning("直近7日間の日記データがありません。")
            return

        with st.spinner("AIが分析中です...（数秒かかります）"):
            try:
                summary = generate_weekly_summary(recent_entries)
                st.markdown("### 💡 AIレスポンス")
                st.info(summary)
            except Exception as e:
                st.error(f"分析中にエラーが発生しました: {e}")

def relationship_tree_ui(entries, has_api_key):
    st.subheader("🕸 思考・関係性ツリー")
    st.write("これまでの日記から話題のつながりやキーワード間の関係を抽出し、ネットワークとして描画します。")
    
    mode_label = st.radio(
        "抽出モードを選択",
        options=["今日の記録と似たトピックの繋がり (全期間)", "直近1ヶ月の全体ツリー"],
        index=0
    )
    
    if st.button("🌐 ツリーを構築する", use_container_width=True):
        if not has_api_key:
            st.error("環境変数 `GEMINI_API_KEY` が設定されていません。")
            return
            
        if not entries:
            st.warning("日記データがありません。")
            return
            
        # モードに応じたフィルタリングと引数設定
        if mode_label == "今日の記録と似たトピックの繋がり (全期間)":
            target_entries = entries # 全件渡す
            mode_arg = "focus_today"
        else:
            # 直近30日のデータを抽出
            from datetime import datetime, timedelta, timezone
            dt_30_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            target_entries = [e for e in entries if e.get("createdAt") and e.get("createdAt") >= dt_30_days_ago]
            if not target_entries:
                st.warning("直近1ヶ月の日記データがありません。")
                return
            mode_arg = "recent_1_month"
            
        with st.spinner("キーワードの抽出と関係性分析を行っています...（長期間のデータの場合少し時間がかかります）"):
            try:
                data = extract_relationship_graph(target_entries, mode=mode_arg)
                nodes = []
                edges = []
                
                # 視認性向上のためのノード色・文字色の指定
                # 背景色を明るいアイボリー (#FDF5E6)、文字色を黒に指定し太字のように扱うことで可読性を向上
                for n in data.get("nodes", []):
                    label = n["label"][:15] + ".." if len(n["label"]) > 15 else n["label"]
                    nodes.append(Node(
                        id=n["id"], 
                        label=label, 
                        size=20, # ノード数が増えるため少し小さめに変更
                        color="#1F4E79",  # 白文字が映えるネイビー系の背景色
                        font={'color': 'white', 'size': 14, 'face': 'sans-serif'} # 文字を白で固定
                    ))
                    
                for e in data.get("edges", []):
                    edges.append(Edge(
                        source=e["source"], 
                        target=e["target"], 
                        type="CURVE_SMOOTH", 
                        color="#B0C4DE" # エッジの色を指定（LightSteelBlue）
                    ))
                    
                config = Config(width="100%", height=600, directed=False, physics=True, hierarchical=False)
                st.success("関係性ツリーの生成が完了しました！")
                agraph(nodes=nodes, edges=edges, config=config)
                
            except json.JSONDecodeError:
                st.error("AIが予期しない形式のデータを返しました。もう一度試してください。")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
