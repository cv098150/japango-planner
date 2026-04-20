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

# ================== 生成函數（使用你的 Prompt） ==================
def generate_itineraries_with_gemini(user_input, search_results):
    context = "## 參考資料來源\n\n"
    for i, result in enumerate(search_results.get("results", []), 1):
        context += f"**來源 {i}**：{result.get('title')}\n"
        context += f"- 摘要：{result.get('content', '')[:500]}...\n\n"

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
請為這位旅客**產生完整 3 筆明顯不同風格**的行程推薦，每一筆都要有強烈特色，不要重複：


1. **行程標題 + 特色描述**
   - 例如：「米其林美食×古寺深度遊」、「動漫迷必踩景點大滿足」等
   - 包含 2-3 個相關的 Hashtag

2. **航班建議**（放在開頭或 Day 1）
   - 根據飛行日期 {user_input['flight_dates']}，具體建議去程與回程航班（包含航空公司、建議時間、預估價格、早鳥提醒）
   - 包含：航空公司、去程和回程時間、預估價格（NT$）
   - 提供早鳥票價的預期範圍
   - 說明機票佔總預算的比例

3. **Day-by-Day 詳細日程**
   - **時間框架**：每一天都要有具體時間安排（例如 09:00-11:30）、景點名稱、停留時間、交通方式、餐食建議、雨天備案
   - **景點/活動**：景點名稱、停留時間、必看重點
   - **交通方式**：具體的車種（JR、地鐵、巴士等）和預估時間
   - **餐飲建議**：早午晚三餐的預估價格和建議類型（便當、餐廳、夜市等）
   - **雨天備案**：提供室內替代方案
   - **休息提醒**：適度的休息時段

4. **花費明細表**
   - 表格格式：使用 Markdown 表格，按天列出交通、餐飲、門票、住宿等，最後給總計（必須控制在預算內）。
   - 分類：機票、住宿、交通、餐飲、門票、購物雜費
   - 備註欄位：特別省錢秘訣或值得花費項目
   - 總計必須嚴格控制在 NT${user_input['budget']} ±10% 以內

5. **推薦住宿**
   - 列出 2-3 個經濟型選項（青年旅館、膠囊、經濟商務旅館），附每晚台幣價格範圍與推薦理由。
   - 每晚台幣價格範圍
   - 推薦理由（地理位置、CP值、設施等）
   - 優先推薦青年旅館、膠囊旅館、民宿（符合預算）

6. **台灣人專屬建議**
   - JR Pass 購買指南（是否划算、購買地點）
   - IC 卡（Suica/Pasmo）使用提醒
   - 常見「踩雷」項目（過度商業化景點、遊客多的季節提醒）
   - 台灣人常犯的錯誤和改善建議
   - 包含 ICOCA 卡使用、常見雷點、省錢技巧、實用提醒

7. **進階省錢技巧**
   - 免費景點推薦
   - 便宜美食地點（便利商店、大眾食堂、夜市）
   - 優惠券和折扣資訊
   - 搭乘通勤列車看在地風景等

## 輸出格式要求
- **語言**：繁使用繁體中文，語氣親切、專業、像老司機在分享經驗
- **格式**：使用 Markdown 格式（標題、表格、列表、emoji）
- **長度**：所有金額以 NT$ 表示，並標註使用者「{user_input['flight_dates']}參考價格」
- **可讀性**：使用 emoji、顏色標記（如果 Markdown 支援）、清晰的分隔線
- **實用性**：強調「用這個預算真的可以玩得很舒服、很有收穫」
- **差異化**：3 筆行程要有明顯不同的風格和重點，不要重複
- **結論**：每個行程最後都要有一段結論，總結行程特色並給出延伸建議（例如：如果喜歡這個行程，可以考慮的其他景點或活動）
- **注意事項**：加入 2026 年最新的旅遊注意事項（例如：新的交通政策、熱門景點的變化、機票價格趨勢等）
- **避免過度推銷**：內容要實用、客觀，不要過度推薦特定產品或服務
- **真實經驗感**：加入一些個人經驗分享的語句，讓內容更有溫度和可信度
- **台灣旅客視角**：特別針對台灣旅客的需求和習慣來設計行程和建議
- **航班建議**：根據使用者提供的飛行日期，具體建議去程和回程的航班選擇，並說明機票在總預算中的比例
- **預算控制**：所有行程的總花費必須嚴格控制在使用者提供的預算範圍內（±10%），並在花費明細表中清晰展示

## 參考資料
{context}

## 最終提醒
- 所有金額必須以台幣 (NT$) 表示
- 行程必須實際可行、時間規劃合理
- 優先考慮大眾運輸的便利性
- 強調「用有限預算玩得很舒服」的感覺
- 3 個行程應該差異明顯，不要重複

開始生成 3 筆行程方案："""

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