import streamlit as st
from tavily import TavilyClient
from google import genai
import time
import random
from datetime import datetime

# ================== 安全讀取 API Key ==================
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

tavily = TavilyClient(api_key=TAVILY_API_KEY)
client = genai.Client(api_key=GEMINI_API_KEY)

st.set_page_config(page_title="日本自由行 AI 規劃師", page_icon="🇯🇵", layout="centered")

st.title("🇯🇵 日本自由行 AI 規劃師")
st.markdown("**用 NT$30,000 左右的預算，輕鬆規劃高品質日本行程**")

# ================== 使用者輸入表單 ==================
with st.form("trip_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        departure = st.text_input("出發地", value="高雄")
        days = st.number_input("旅遊天數", min_value=3, max_value=10, value=5)
        budget = st.number_input("每人總預算 (NT$)", min_value=15000, max_value=100000, value=30000, step=1000)
    
    with col2:
        destination = st.text_input("目的地（可多個，例如：大阪、京都）", value="大阪")
        flight_dates = st.text_input("飛行日期範圍（例如：4/15 - 4/20）", value="4/15 - 4/20")
        transport = st.selectbox("交通偏好", ["大眾運輸", "混搭", "租車"])

    attitude = st.selectbox(
        "旅遊態度",
        ["混合", "Chill（輕鬆慢活）", "什麼都要玩到（高強度）", "文化深度"]
    )

    submitted = st.form_submit_button("🚀 生成 3 筆推薦行程")

if submitted:
    user_input = {
        "departure": departure,
        "destination": destination,
        "days": days,
        "budget": budget,
        "transport": transport,
        "attitude": attitude,
        "flight_dates": flight_dates
    }

    with st.spinner("正在搜尋最新資訊並生成 3 筆行程... 請稍候"):
        try:
            search_results = tavily.search(
                query=f"2026 日本 {destination} {days}天 自由行 台灣旅客 {attitude} {transport} 攻略 航班 {flight_dates}",
                search_depth="advanced",
                max_results=8,
                include_answer=True,
                topic="general",
                time_range="month"
            )

            markdown_content = generate_itineraries_with_gemini(user_input, search_results)

            st.success("✅ 3 筆推薦行程已生成！")
            st.markdown(markdown_content, unsafe_allow_html=True)

            st.download_button(
                label="📥 下載 Markdown 檔案",
                data=markdown_content,
                file_name=f"日本行程_{destination}_{days}天_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown"
            )

        except Exception as e:
            st.error(f"生成失敗：{str(e)}")

# ================== 生成函數（使用你提供的完整 Prompt） ==================
def generate_itineraries_with_gemini(user_input, search_results):
    # 組合 context
    context = "## 參考資料來源\n\n"
    for i, result in enumerate(search_results.get("results", []), 1):
        context += f"**來源 {i}**：{result.get('title')}\n"
        context += f"- 摘要：{result.get('content', '')[:500]}...\n\n"

    # 使用你提供的完整 Prompt
    prompt = f"""你是一位資深日本自由行規劃師，擅長為台灣旅客設計符合預算、符合偏好的行程。

## 使用者需求
- **出發地**：{user_input['departure']}
- **目的地**：{user_input['destination']}
- **旅遊天數**：{user_input['days']} 天
- **總預算**：NT${user_input['budget']}（±10% 以內，包含機票、住宿、交通、餐飲、景點門票）
- **飛行日期**：{user_input['flight_dates']}
- **交通方式**：{user_input['transport']}
- **旅遊態度**：{user_input['attitude']}

## 旅遊態度詳細指導
根據使用者選擇的態度調整行程節奏和內容：

**Chill（輕鬆慢活）**：
  - 每天 1-2 個主要景點
  - 多留咖啡館、散步、拍照時間
  - 強調放鬆和親近當地生活
  - 建議安排「無計劃」的自由活動時段

**什麼都要玩到（高強度）**：
  - 每天 4-5 個景點
  - 最大化景點覆蓋率
  - 提供詳細的時間規劃和移動路線
  - 包含隱藏景點和在地小店

**混合**：
  - 每天 2-3 個景點
  - 早上文化體驗（寺廟、美術館）
  - 午後購物或美食探索
  - 晚上當地體驗（居酒屋、夜市）

**文化深度**：
  - 優先推薦歷史寺廟、美術館、老街區
  - 深入介紹每個景點的文化背景
  - 包含在地美食文化和傳統體驗
  - 建議參加小型文化工作坊

## 任務要求
請為這位旅客**產生完整 3 筆明顯不同風格**的行程推薦，每一筆都要有強烈特色，不要重複。

1. **行程標題 + 特色描述**（附 2-3 個 Hashtag）
2. **航班建議**（放在開頭或 Day 1）
3. **Day-by-Day 詳細日程**
4. **花費明細表**
5. **推薦住宿**
6. **台灣人專屬建議**
7. **進階省錢技巧**

## 輸出格式要求
- 使用繁體中文，語氣親切、專業、像老司機在分享經驗
- 使用 Markdown 格式（標題、表格、列表、emoji）
- 所有金額以 NT$ 表示，並標註「2026年4月參考價格」
- 強調「用這個預算真的可以玩得很舒服、很有收穫」
- 3 筆行程要有明顯不同的風格和重點，不要重複

## 參考資料
{context}

開始生成 3 筆行程方案："""

    # 重試機制
    max_retries = 6
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            return response.text
        except Exception as e:
            if any(x in str(e).lower() for x in ["503", "unavailable", "rate"]):
                wait_time = min((2 ** attempt) * 3 + random.uniform(3, 10), 120)
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("多次重試後仍失敗")

st.caption("日本自由行 AI 規劃師 | 第一版測試")