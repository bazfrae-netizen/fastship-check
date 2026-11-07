import streamlit as st
import pandas as pd

st.set_page_config(page_title="FastShip Check", page_icon="📦", layout="wide")

st.markdown("<h1 style='color: #FF5722;'>📦 FastShip Check</h1>", unsafe_allow_html=True)
st.subheader("ระบบวิเคราะห์เงื่อนไขการส่งออกอัจฉริยะ")

# โหลดฐานข้อมูล
@st.cache_data
def load_data():
    try:
        return pd.read_csv("master_database.csv")
    except Exception as e:
        return pd.DataFrame(columns=["Keyword", "Category", "Restriction_Level", "Country", "Note"])

df = load_data()

# ส่วนเลือกประเทศและช่องค้นหา
col1, col2 = st.columns(2)

with col1:
    extra_countries = [
        "Cambodia", "Laos", "Myanmar", "Vietnam", "Malaysia", "Singapore",
        "Indonesia", "Philippines", "Brunei", "Japan", "South Korea", "China",
        "Taiwan", "Hong Kong", "India", "Australia", "New Zealand", "USA",
        "Canada", "UK", "France", "Germany", "Italy", "Spain", "Netherlands"
    ]
    db_countries = [str(x) for x in df['Country'].unique() if str(x) not in ['-', 'nan', '0', ' ']] if 'Country' in df.columns else []
    all_countries = sorted(list(set(extra_countries + db_countries)))
    countries = ["- กรุณาเลือกประเทศ -"] + all_countries
    target_country = st.selectbox("🌍 ประเทศปลายทาง", countries)

    agents = ["ทั้งหมด", "UPS", "FedEx", "Aramex", "EMS World / Epacket 2kg", "All In"]
    selected_agent = st.selectbox("🚚 เอเยนต์ (Agent)", agents)

with col2:
    # ดึงรายการสินค้าจากคอลัมน์ Keyword ใน CSV มาแสดงแบบจัดเต็มอัตโนมัติ
    db_items = [str(x) for x in df['Keyword'].unique() if str(x) not in ['-', 'nan', '0', ' ']] if 'Keyword' in df.columns else []
    item_options = ["- เลือกสินค้าจากรายการ -"] + sorted(db_items)
    
    selected_item_dropdown = st.selectbox("📦 เลือกสินค้าจากฐานข้อมูล", item_options)
    custom_item = st.text_input("✍️ หรือพิมพ์ชื่อสินค้าที่ต้องการตรวจสอบ", placeholder="เช่น เสื้อผ้า, พัดลม, แบต
