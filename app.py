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
    custom_item = st.text_input("✍️ หรือพิมพ์ชื่อสินค้าที่ต้องการตรวจสอบ", placeholder="เช่น เสื้อผ้า, พัดลม, แบต, กระเป๋า")
    
    selected_item = custom_item if custom_item.strip() != "" else (selected_item_dropdown if selected_item_dropdown != "- เลือกสินค้าจากรายการ -" else "")

# ส่วนถ่ายรูป / อัปโหลดรูปภาพสินค้า
st.markdown("---")
st.subheader("📸 ตรวจสอบสินค้าผ่านรูปภาพ / กล้อง")
uploaded_file = st.file_uploader("อัปโหลดรูปภาพสินค้า", type=["jpg", "jpeg", "png"])
camera_image = st.camera_input("หรือถ่ายภาพสินค้าด้วยกล้อง")

# ส่วนแสดงผลการวิเคราะห์
st.markdown("---")
st.subheader("📌 สรุปผลการจัดส่ง:")
if target_country != "- กรุณาเลือกประเทศ -" and selected_item:
    result = df[df['Keyword'].astype(str).str.contains(selected_item, case=False, na=False)]
    if not result.empty:
        st.success(f"✅ พบข้อมูลเงื่อนไขสำหรับ: {selected_item}")
        for idx, row in result.iterrows():
            st.warning(f"⚠️ **ระดับข้อจำกัด:** {row.get('Restriction_Level', 'N/A')} | **หมวดหมู่:** {row.get('Category', 'N/A')}")
            st.info(f"📝 **หมายเหตุ:** {row.get('Note', 'ไม่มีข้อมูลเพิ่มเติม')}")
    else:
        st.success(f"✅ สามารถส่ง {selected_item} ไปยัง {target_country} ได้ภายใต้เงื่อนไขมาตรฐาน")
else:
    st.info("💡 กรุณาเลือกประเทศปลายทางและระบุชื่อสินค้าเพื่อเริ่มตรวจสอบเงื่อนไข")
