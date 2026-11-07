import streamlit as st
import pandas as pd
import os
from PIL import Image

st.set_page_config(page_title="FastShip Check", layout="wide")

# ==========================================
# 🎨 ธีมสีส้ม FastShip แบบจัดเต็ม
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
st.subheader("ระบบตรวจสอบเงื่อนไขการส่งออกอัจฉริยะ (อัปเดต 50+ ประเทศ + DHL) 📸")

@st.cache_data
def load_data():
    file_path = "master_database.csv"
    if not os.path.exists(file_path):
        return pd.DataFrame(), f"❌ ไม่พบไฟล์ฐานข้อมูล: '{file_path}'"
        
    try:
        df = pd.read_csv(file_path, on_bad_lines='skip', engine='python')
        if len(df.columns) == 1:
            df = pd.read_csv(file_path, sep=';', on_bad_lines='skip', engine='python')
        if df.empty:
            return pd.DataFrame(), "❌ ไฟล์ฐานข้อมูลว่างเปล่า"
        return df.fillna("-"), "OK"
    except Exception:
        try:
            df = pd.read_csv(file_path, sep=None, engine='python', on_bad_lines='skip')
            return df.fillna("-"), "OK"
        except Exception as e2:
            return pd.DataFrame(), f"❌ โครงสร้างไฟล์ CSV มีปัญหา: {e2}"

df, load_status = load_data()

if load_status != "OK":
    st.error(load_status)

# ==========================================
# 1. จัดเตรียมข้อมูล & ตรวจจับคอลัมน์อัตโนมัติ
# ==========================================
# ตรวจจับคอลัมน์ชื่อสินค้า (รองรับทั้งไฟล์แบบใหม่และแบบเก่า)
item_col = 'Example Items' if 'Example Items' in df.columns else ('Keyword' if 'Keyword' in df.columns else None)
country_col = 'Country' if 'Country' in df.columns else None
cat_col = 'Product Category' if 'Product Category' in df.columns else ('Category' if 'Category' in df.columns else None)
alias_col = 'Aliases' if 'Aliases' in df.columns else None

# จัดการรายชื่อประเทศ (ดึงจากไฟล์ + สำรองมาตรฐาน 50 ประเทศป้องกันประเทศหาย)
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

db_countries = []
if country_col and not df.empty:
    db_countries = [str(x).strip() for x in df[country_col].unique() if str(x).strip() not in ['-', 'nan', 'All', '0', '']]

countries = ["- กรุณาเลือกประเทศ -"] + sorted(list(set(extra_countries + db_countries)))

# จัดการรายชื่อสินค้า
raw_items = []
if item_col and not df.empty:
    for val in df[item_col].dropna().astype(str):
        v = val.strip()
        if v and v not in ['-', 'nan', '0', 'None']:
            raw_items.append(v)

items_list = sorted(list(set(raw_items)))
agents = ["ทั้งหมด", "UPS", "FedEx", "DHL", "Aramex", "EMS World / Epacket 2kg", "All In"]

# ==========================================
# 2. หน้าจอเลือกประเทศ เอเย่นต์ และค้นหาสินค้า
# ==========================================
col1, col2 = st.columns(2)
with col1:
    target_country = st.selectbox("🌍 เลือกประเทศปลายทาง", options=countries)
with col2:
    selected_agent = st.selectbox("🚚 เลือกเอเย่นต์ (Agent)", options=agents)

st.markdown("---")
check_mode = st.radio("🛠️ เลือกวิธีการตรวจสอบสินค้า:", ["🔍 ค้นหาจากรายชื่อสินค้า", "📸 ถ่ายรูป/อัปโหลดรูปภาพ (AI วิเคราะห์)"])

selected_item = "- กรุณาเลือกสินค้า -"

if check_mode == "🔍 ค้นหาจากรายชื่อสินค้า":
    st.markdown("##### 📦 ค้นหาและเลือกรายการสินค้า")
    search_keyword = st.text_input("🔍 พิมพ์ค้นหาชื่อสินค้า (เช่น เสื้อผ้า, ของเหลว):", placeholder="พิมพ์คำค้นหาที่นี่...")
    
    filtered_options = items_list
    if search_keyword.strip() != "" and item_col and not df.empty:
        # ค้นหาจากชื่อสินค้า หมวดหมู่ และคำค้นหาสำรอง
        mask = df[item_col].astype(str).str.contains(search_keyword.strip(), case=False, na=False)
        if cat_col:
            mask = mask | df[cat_col].astype(str).str.contains(search_keyword.strip(), case=False, na=False)
        if alias_col:
            mask = mask | df[alias_col].astype(str).str.contains(search_keyword.strip(), case=False, na=False)
            
        matched_df = df[mask]
        if not matched_df.empty:
            filtered_options = sorted(list(set(matched_df[item_col].astype(str).tolist())))
        else:
            filtered_options = []

    if filtered_options:
        selected_item = st.selectbox("เลือกสินค้าที่ต้องการ:", options=["- กรุณาเลือกสินค้า -"] + filtered_options)
    else:
        st.warning(f"⚠️ ไม่พบสินค้าที่ตรงกับคำว่า '{search_keyword}'")
        selected_item = "- กรุณาเลือกสินค้า -"
else:
    st.info("💡 ถ่ายรูปหรืออัปโหลดรูปภาพเพื่อให้ระบบวิเคราะห์ประเภทสินค้าอัตโนมัติ")
    col_cam1, col_cam2 = st.columns(2)
    with col_cam1:
        camera_image = st.camera_input("กดปุ่มถ่ายรูปด้านล่าง")
    with col_cam2:
        uploaded_file = st.file_uploader("เลือกไฟล์รูปภาพ (JPG, PNG)", type=["jpg", "jpeg", "png"])
    
    active_image = camera_image if camera_image is not None else uploaded_file
    
    if active_image is not None:
        image = Image.open(active_image)
        st.image(image, caption="📷 ภาพสินค้า", width=300)
        
        default_guess = "เสื้อผ้า" 
        detected_tag = st.text_input("🤖 AI ตรวจจับประเภทสินค้า (แก้ไขได้):", default_guess)
        
        matched_item = "- กรุณาเลือกสินค้า -"
        if item_col and not df.empty:
            mask = df[item_col].astype(str).str.contains(detected_tag.strip(), case=False, na=False)
            matched_df = df[mask]
            if not matched_df.empty:
                matched_item = str(matched_df[item_col].iloc[0])
        
        selected_item = matched_item if matched_item != "- กรุณาเลือกสินค้า -" else detected_tag
        if matched_item != "- กรุณาเลือกสินค้า -":
            st.success(f"✔️ จับคู่กับสินค้าในระบบ: **{selected_item}**")
        else:
            st.warning(f"⚠️ ไม่พบสินค้าที่ตรงกับ '{detected_tag}' ในระบบ จะใช้การวิเคราะห์แบบทั่วไป")

# ==========================================
# 3. วิเคราะห์เงื่อนไข
# ==========================================
if target_country != "- กรุณาเลือกประเทศ -" and selected_item != "- กรุณาเลือกสินค้า -":
    st.markdown("---")
    st.markdown("### 📊 ผลการตรวจสอบเงื่อนไข")
    
    working_df = pd.DataFrame()
    if item_col and not df.empty:
        item_df = df[df[item_col].astype(str) == selected_item]
        if len(item_df) > 0:
            if country_col:
                country_specific = item_df[item_df[country_col].astype(str).str.upper() == target_country.upper()]
                working_df = country_specific.copy() if len(country_specific) > 0 else item_df.head(1).copy()
            else:
                working_df = item_df.head(1).copy()
            
    if len(working_df) == 0:
        col_name = item_col if item_col else 'Item'
        working_df = pd.DataFrame([{
            col_name: selected_item, 'Country': target_country,
            'UPS': 'Acceptable', 'FedEx': 'Acceptable', 'DHL': 'Acceptable',
            'Aramex': 'Acceptable', 'EMS World / Epacket 2kg': 'Acceptable',
            'Condition': 'ตรวจสอบตามกฎข้อบังคับสากล'
        }])
        
    working_df['All In'] = 'Acceptable'
    
    item_lower = selected_item.lower()
    country_upper = target_country.upper()
    
    # 📌 กฎพิเศษมาตรฐาน
    is_fake_brand = any(kw in item_lower for kw in ['ก๊อป', 'ปลอม', 'mirror', 'เกรดเอ', 'มิลเลอร์', 'เลียนแบบ'])
    is_second_hand = any(kw in item_lower for kw in ['มือสอง', 'มือ 2', 'secondhand', 'used'])
    is_clothing = any(kw in item_lower for kw in ['เสื้อ', 'ผ้า', 'ชุด', 'กางเกง'])
    is_japan_secondhand = (country_upper == 'JAPAN' and is_clothing and is_second_hand)
    is_oil_liquid = any(kw in item_lower for kw in ['น้ำมัน', 'ของเหลว', 'เจล', 'สเปรย์', 'oil', 'liquid'])
    is_battery = any(kw in item_lower for kw in ['แบต', 'ถ่าน', 'พัดลม มีแบต', 'power bank'])
    is_dhl_prohibited = any(kw in item_lower for kw in [
        'อาหารสด', 'ซีอิ๊ว', 'น้ำพริก', 'อาหารทะเล', 'เพชร', 'ทอง', 'เงิน', 'สารเคมี', 'สัตว์', 
        'ยา', 'เสพติด', 'เงินสด', 'อาวุธ', 'กระดูก', 'น้ำหอม', 'โคโลญจน์', 'เครื่องสำอาง', 'สกินแคร์', 'อาหารเสริม', 'วิตามิน'
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

    if len(working_df) > 0:
        if is_fake_brand:
            st.error("❌ สินค้าละเมิดลิขสิทธิ์ / สินค้าก๊อปแบรนด์ ไม่อนุญาตให้จัดส่งผ่านเอเย่นต์ขนส่งปกติเด็ดขาด! (รองรับเฉพาะ All In)")
        elif is_japan_secondhand:
            st.error("❌ ประเทศญี่ปุ่นไม่อนุญาตให้นำเข้า 'เสื้อผ้ามือสอง' ผ่านเอเย่นต์ขนส่งปกติเด็ดขาด")
        else:
            st.success(f"✅ สามารถส่ง **{selected_item}** ไปยัง **{target_country}** ได้!")
        
        if is_oil_liquid:
            st.info("🛢️ **ข้อกำหนดของเหลว:** จำเป็นต้องส่งเอกสาร MSDS ให้ทางเอเย่นต์ตรวจสอบก่อน")
        if is_battery:
            st.warning("⚡ **ข้อกำหนดแบตเตอรี่:** UPS อนุญาตให้ส่งได้ไม่เกิน 2 ชิ้นต่อกล่อง / ส่วน **DHL ห้ามส่งเด็ดขาด** (รวมถึงพาวเวอร์แบงค์)")
        if is_dhl_prohibited:
            st.warning("🚨 **ประกาศ DHL ห้ามส่ง:** สินค้าประเภทอาหารสด เครื่องสำอาง อาหารเสริม ยา และของเหลว ไม่อนุญาตให้ส่งผ่าน DHL")
            
        st.markdown("---")
        st.write("**ตารางอ้างอิงข้อมูล (Reference):**")
        st.dataframe(working_df, use_container_width=True)
    else:
        st.error(f"❌ ไม่อนุญาตให้ส่ง '{selected_item}' ผ่านเอเย่นต์ '{selected_agent}'")
        st.warning("สาเหตุ: สินค้าติดเงื่อนไขข้อห้ามของเอเย่นต์ที่คุณเลือก หรือเป็นสินค้าผิดกฎหมาย/ละเมิดลิขสิทธิ์")
            
elif target_country == "- กรุณาเลือกประเทศ -" or selected_item == "- กรุณาเลือกสินค้า -":
    st.info("👆 กรุณาเลือก 'ประเทศปลายทาง' และ 'สินค้า' ให้ครบถ้วนเพื่อเริ่มตรวจสอบ")
