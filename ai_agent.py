import os
import json
import tempfile
import streamlit as st
import google.generativeai as genai

# APIキーの設定
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def generate_weekly_summary(entries):
    """直近の日記データからハイライトと感情の傾向を分析"""
    text_data = "\n\n".join([f"【{e.get('createdAt')}】: {e.get('content')}" for e in entries])
    
    prompt = f"""
    以下のテキストは、私の直近1週間の日記です。この内容から、以下の2点を出力してください。
    1. 今週のハイライト（主な出来事や達成したこと）
    2. 感情の傾向（どのような感情が多く見られたか、全体的な調子について）
    
    出力は、箇条書きなどを使い分かりやすいMarkdown形式で装飾してください。

    【日記データ】
    {text_data}
    """
    
    # ユーザーが指定したモデル (gemini-2.5-flash) に更新
    model = genai.GenerativeModel("gemini-2.5-flash") 
    res = model.generate_content(prompt)
    return res.text

def extract_relationship_graph(entries, mode="recent_1_month"):
    """日記データからキーワードを抽出し、JSONのグラフ構造(nodes, edges)で返す"""
    if not entries:
        return {"nodes": [], "edges": []}
        
    text_data = ""
    for i, e in enumerate(entries):
        created_at = e.get("createdAt")
        date_str = created_at.strftime("%Y-%m-%d %H:%M") if hasattr(created_at, 'strftime') else "日時不明"
        tags_str = ", ".join(e.get("tags", []))
        text_data += f"[{i}] 日付: {date_str} | タグ: {tags_str} | 内容: {e.get('content')}\n\n"
        
    # 一時ファイルに書き出す
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt", encoding="utf-8") as f:
        f.write(text_data)
        temp_path = f.name
        
    # ファイルをGeminiにアップロード
    try:
        uploaded_file = genai.upload_file(temp_path, mime_type="text/plain")
        
        if mode == "focus_today":
            latest_entry = entries[0]
            latest_content = latest_entry.get("content", "")
            prompt = f"""
            アップロードされたテキストファイルには、過去の全日記データが含まれています。
            以下のテキストは「今日の最新の日記内容」です。
            
            【今日の日記】
            {latest_content}
            
            この「今日の日記」のエッセンス・キーワードを中心軸とし、対象ファイル内の過去の出来事・思考・出来事とどのようにリンクしているか、文脈の繋がりや思考の変遷を抽出し、JSON形式のネットワークグラフ構造で出力してください。
            """
        else:
            prompt = """
            アップロードされたテキストファイルには、対象期間（直近1ヶ月等）の日記データが含まれています。
            このデータ全体から、主要なキーワード（出来事、人名、感情、概念、趣味など）を抽出し、それらのキーワード間の関連性をJSON形式のネットワークグラフ構造で出力してください。
            """
            
        prompt += """
        スキーマは必ず以下のものを使用し、**それ以外のテキスト（Markdown記法を含む）は絶対に含めないでください。**
        ノード(nodes)の数は最大で70個程度とし、エッジ(edges)は意味のある強い繋がりに厳選してください。

        {
            "nodes": [
                {"id": "キーワード1", "label": "キーワード1"},
                {"id": "キーワード2", "label": "キーワード2"}
            ],
            "edges": [
                {"source": "キーワード1", "target": "キーワード2"}
            ]
        }
        """
        
        # JSON構造を出力させるコンフィグと最新モデルを使用
        model = genai.GenerativeModel("gemini-2.5-flash", generation_config={"response_mime_type": "application/json"})
        res = model.generate_content([uploaded_file, prompt])
        
    finally:
        # クリーンアップ処理
        try:
            if 'uploaded_file' in locals():
                genai.delete_file(uploaded_file.name)
        except Exception as e:
            print(f"Failed to delete Gemini file: {e}")
        try:
            os.remove(temp_path)
        except Exception as e:
            print(f"Failed to delete local temp file: {e}")
            
    res_text = res.text.strip()
    if res_text.startswith("```json"):
         res_text = res_text[7:-3].strip()
    elif res_text.startswith("```"):
         res_text = res_text[3:-3].strip()
         
    return json.loads(res_text)
