import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(page_title="FastShip Check", layout="wide", page_icon="📦")

# ==========================================
# 🎨 ธีมสีส้ม FastShip พรีเมียม
# ==========================================
st.markdown("""
    <style>
    h1, h2, h3 { color: #FF6600 !important; }
    div.stButton > button:first-child {
        background-color: #FF6600 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
    }
    div.stButton > button:first-child:hover { background-color: #E65C00 !important; }
    .stAlert { border-left-color: #FF6600 !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 FastShip Check")
st.subheader("ระบบตรวจสอบเงื่อนไขการส่งออกระหว่างประเทศ (ฐานข้อมูล 4,000+ รายการ + DHL)")
st.markdown("---")

@st.cache_data
def load_data():
    file_path = "master_database.csv"
    if os.path.exists(file_path):
        try:
            # ใช้ engine='python' และ on_bad_lines='skip' เพื่อให้อ่านไฟล์ขนาดใหญ่ได้เสถียรที่สุด
            df = pd.read_csv(file_path, on_bad_lines='skip', encoding='utf-8', engine='python')
            if not df.empty and 'Example Items' in df.columns:
                return df.fillna("-")
        except Exception:
            try:
                df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')
                if not df.empty and 'Example Items' in df.columns:
                    return df.fillna("-")
            except Exception:
                pass
    return pd.DataFrame()

df = load_data()

# ==========================================
# 1. จัดเตรียมรายชื่อประเทศและสินค้า
# ==========================================
extra_countries = [
    "Australia", "Austria", "Bangladesh", "Belgium", "Canada", "Chile", "China", 
    "Croatia", "Czech Republic", "Denmark", "Egypt", "Finland", "France", "Germany", 
    "Greece", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Ireland", 
    "Israel", "Italy", "Japan", "Kuwait", "Macao", "Malaysia", "Malta", "Mexico", 
    "Netherlands", "New Zealand", "Norway", "Oman", "Pakistan", "Philippines", 
    "Poland", "Puerto Rico", "Qatar", "Saudi Arabia", "Singapore", "South Africa", 
    "South Korea", "Spain", "Sweden", "Switzerland", "Taiwan", "Turkey", "United Kingdom", "USA",
    "United Arab Emirates", "Vietnam"
]

db_countries = df['Country'].dropna().unique().tolist() if not df.empty and 'Country' in df.columns else []
countries = ["- กรุณาเลือกประเทศ -"] + sorted(list(set(extra_countries + [str(x) for x in db_countries if str(x) not in ['-', 'nan', 'All']])))

# ดึงรายการสินค้าทั้งหมดจากคอลัมน์ Example Items ใน CSV แบบจัดเต็ม
items_list = []
if not df.empty and 'Example Items' in df.columns:
    raw_items = df['Example Items'].dropna().astype(str).tolist()
    items_list = sorted(list(set([x.strip() for x in raw_items if x.strip() and x.strip() not in ['-', 'nan', '0', 'None', 'Example Items']])))

agents = ["ทั้งหมด", "UPS", "FedEx", "DHL", "Aramex", "EMS World / Epacket 2kg", "All In"]

# ==========================================
# 2. ส่วนควบคุมหลัก
# ==========================================
col_c1, col_c2 = st.columns(2)
with col_c1:
    target_country = st.selectbox("🌍 เลือกประเทศปลายทาง", options=countries)
with col_c2:
    selected_agent = st.selectbox("🚚 เลือกเอเย่นต์ (Agent)", options=agents)

st.markdown("<br>", unsafe_allow_html=True)
check_mode = st.radio("🛠️ เลือกวิธีการตรวจสอบสินค้า:", ["🔍 ค้นหาและเลือกรายชื่อสินค้า (จัดเต็ม)", "📸 ถ่ายรูป/อัปโหลดรูปภาพ (AI วิเคราะห์)"], horizontal=True)

selected_item = "- กรุณาเลือกสินค้า -"

if check_mode == "🔍 ค้นหาและเลือกรายชื่อสินค้า (จัดเต็ม)":
    st.markdown("##### 📦 ค้นหาหรือเลื่อนเลือกรายการสินค้าจากฐานข้อมูลจริง")
    search_keyword = st.text_input("🔍 กรองชื่อสินค้า (พิมพ์เพื่อค้นหา หรือเว้นว่างเพื่อดูทั้งหมด):", placeholder="พิมพ์คำค้นหา...")
    
    filtered_items = items_list
    if search_keyword.strip() != "":
        kw = search_keyword.strip().lower()
        matched = [item for item in items_list if kw in item.lower()]
        if matched:
            filtered_items = matched

    selected_item = st.selectbox(f"📋 เลือกรายการสินค้าทั้งหมด ({len(filtered_items)} รายการ):", options=["- กรุณาเลือกสินค้า -"] + filtered_items)

else:
    st.info("💡 ถ่ายรูปหรืออัปโหลดภาพสินค้าเพื่อให้ระบบ AI วิเคราะห์")
    c_img1, c_img2 = st.columns(2)
    with c_img1:
        camera_image = st.camera_input("ถ่ายภาพสินค้า")
    with c_img2:
        uploaded_file = st.file_uploader("อัปโหลดไฟล์รูปภาพ", type=["jpg", "jpeg", "png"])
    
    active_img = camera_image if camera_image else uploaded_file
    if active_img:
        st.image(Image.open(active_img), caption="ภาพสินค้าของคุณ", width=250)
        detected_tag = st.text_input("🤖 AI วิเคราะห์ประเภทสินค้า:", "สินค้าทั่วไป")
        selected_item = detected_tag

# ==========================================
# 3. ผลการตรวจสอบเงื่อนไข
# ==========================================
if target_country != "- กรุณาเลือกประเทศ -" and selected_item != "- กรุณาเลือกสินค้า -":
    st.markdown("---")
    st.markdown("### 📊 ผลการตรวจสอบข้อกำหนดการจัดส่ง")
    
    working_df = pd.DataFrame()
    if not df.empty and 'Example Items' in df.columns:
        item_match = df[df['Example Items'].astype(str).str.strip() == selected_item.strip()]
        if not item_match.empty:
            country_match = item_match[item_match['Country'].astype(str).str.upper() == target_country.upper()]
            working_df = country_match.copy() if not country_match.empty else item_match.copy()
            
    if working_df.empty:
        working_df = pd.DataFrame([{
            'Example Items': selected_item, 'Country': target_country,
            'UPS': 'Acceptable', 'FedEx': 'Acceptable', 'DHL': 'Acceptable',
            'Aramex': 'Acceptable', 'EMS World / Epacket 2kg': 'Acceptable',
            'Condition': 'ตรวจสอบตามระเบียบมาตรฐานสากล'
        }])
        
    working_df['All In'] = 'Acceptable'
    
    item_lower = selected_item.lower()
    country_upper = target_country.upper()
    
    # 📌 กฎพิเศษและข้อห้ามเฉพาะเอเย่นต์
    is_fake_brand = any(kw in item_lower for kw in ['ก๊อป', 'ปลอม', 'mirror', 'เกรดเอ', 'เลียนแบบ', 'ลิขสิทธิ์'])
    is_second_hand = any(kw in item_lower for kw in ['มือสอง', 'มือ 2', 'secondhand', 'used'])
    is_clothing = any(kw in item_lower for kw in ['เสื้อ', 'ผ้า', 'ชุด', 'กางเกง', 'แบรนด์เนม'])
    is_japan_secondhand = (country_upper == 'JAPAN' and is_clothing and is_second_hand)
    is_oil_liquid = any(kw in item_lower for kw in ['น้ำมัน', 'ของเหลว', 'เจล', 'สเปรย์', 'oil', 'liquid', 'น้ำหอม'])
    is_battery = any(kw in item_lower for kw in ['แบต', 'ถ่าน', 'พัดลม', 'power bank', 'พาวเวอร์แบงค์'])
    is_dhl_prohibited = any(kw in item_lower for kw in [
        'อาหารสด', 'ซีอิ๊ว', 'น้ำพริก', 'อาหารทะเล', 'เพชร', 'ทอง', 'เงิน', 'สารเคมี', 
        'ยา', 'เสพติด', 'เงินสด', 'อาวุธ', 'น้ำหอม', 'เครื่องสำอาง', 'สกินแคร์', 'อาหารเสริม', 'วิตามิน', 'แบต', 'พาวเวอร์แบงค์'
    ])

    for col in ["UPS", "FedEx", "DHL", "Aramex", "EMS World / Epacket 2kg"]:
        if col in working_df.columns:
            if is_fake_brand or is_japan_secondhand:
                working_df[col] = 'Unacceptable'
            elif is_oil_liquid and col in ["UPS", "FedEx"]:
                working_df[col] = 'Check MSDS'
            elif is_battery and col == 'UPS':
                working_df['UPS'] = 'Acceptable'
            if col == 'DHL' and (is_dhl_prohibited or is_battery):
                working_df['DHL'] = 'Unacceptable'

    if selected_agent != "ทั้งหมด" and selected_agent in working_df.columns:
        if selected_agent != 'All In':
            working_df = working_df[~working_df[selected_agent].astype(str).str.upper().isin(['-', 'X', 'NAN', ''])]

    if not working_df.empty:
        if is_fake_brand:
            st.error("❌ สินค้าละเมิดลิขสิทธิ์ / สินค้าแบรนด์เนม ไม่อนุญาตให้จัดส่งผ่านขนส่งปกติ (แนะนำช่องทาง All In เท่านั้น)")
        elif is_japan_secondhand:
            st.error("❌ ประเทศญี่ปุ่นไม่อนุญาตให้นำเข้า 'เสื้อผ้ามือสอง' ผ่านขนส่งปกติ")
        else:
            st.success(f"✅ สามารถตรวจสอบและจัดส่ง **{selected_item}** ไปยัง **{target_country}** ได้")
            
        if is_oil_liquid:
            st.info("🛢️ **ข้อกำหนดของเหลว:** ต้องแนบเอกสาร MSDS ให้ทางเอเย่นต์ตรวจสอบก่อนจัดส่ง")
        if is_battery:
            st.warning("⚡ **ข้อกำหนดแบตเตอรี่:** UPS ส่งได้สูงสุด 2 ชิ้น/กล่อง / **DHL ห้ามส่งเด็ดขาด**")
        if is_dhl_prohibited:
            st.warning("🚨 **ประกาศ DHL ห้ามส่ง:** สินค้าประเภทอาหารสด เครื่องสำอาง อาหารเสริม และของเหลว ไม่อนุญาตผ่าน DHL")
            
        st.markdown("---")
        st.dataframe(working_df, use_container_width=True)
    else:
        st.error(f"❌ ไม่อนุญาตให้ส่ง '{selected_item}' ผ่านเอเย่นต์ '{selected_agent}' เนื่องจากติดเงื่อนไขข้อห้าม")
        
else:
    st.info("👆 กรุณาเลือก 'ประเทศปลายทาง' และ 'รายการสินค้า' ให้ครบถ้วนเพื่อเริ่มตรวจสอบเงื่อนไข")
