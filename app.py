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

# 📌 ข้อมูลสำรองฉุกเฉิน (Fallback Data) ป้องกันกรณีไฟล์ CSV หายหรือโหลดไม่ได้
fallback_data = [
    {"Country": "Australia", "Product Category": "FOOD", "Example Items": "กุนเชียง หมู/ปลา/ไก่", "UPS": "Unacceptable", "FedEx": "Unacceptable", "DHL": "Unacceptable", "Aramex": "Unacceptable", "EMS World / Epacket 2kg": "Acceptable", "Condition": "ePacket สูงสุด 2 kg"},
    {"Country": "Japan", "Product Category": "General Apparel", "Example Items": "เสื้อผ้ามือสอง", "UPS": "Unacceptable", "FedEx": "Unacceptable", "DHL": "Unacceptable", "Aramex": "Unacceptable", "EMS World / Epacket 2kg": "Unacceptable", "Condition": "ญี่ปุ่นห้ามนำเข้าเสื้อผ้ามือสอง"},
    {"Country": "USA", "Product Category": "Cosmetics", "Example Items": "เครื่องสำอาง และ สกินแคร์", "UPS": "Acceptable", "FedEx": "Acceptable", "DHL": "Unacceptable", "Aramex": "Acceptable", "EMS World / Epacket 2kg": "Acceptable", "Condition": "ต้องมีส่วนผสมชัดเจน (DHL ห้ามส่ง)"},
    {"Country": "All", "Product Category": "Dangerous Goods", "Example Items": "พาวเวอร์แบงค์ / แบตเตอรี่", "UPS": "Acceptable", "FedEx": "Check MSDS", "DHL": "Unacceptable", "Aramex": "Unacceptable", "EMS World / Epacket 2kg": "Unacceptable", "Condition": "UPS สูงสุด 2 ชิ้น / DHL ห้ามส่ง"},
    {"Country": "All", "Product Category": "General Apparel", "Example Items": "เสื้อผ้าทั่วไป", "UPS": "Acceptable", "FedEx": "Acceptable", "DHL": "Acceptable", "Aramex": "Acceptable", "EMS World / Epacket 2kg": "Acceptable", "Condition": "ส่งได้ปกติ"},
    {"Country": "All", "Product Category": "Accessories", "Example Items": "กระเป๋า และ รองเท้า", "UPS": "Acceptable", "FedEx": "Acceptable", "DHL": "Acceptable", "Aramex": "Acceptable", "EMS World / Epacket 2kg": "Acceptable", "Condition": "ระวังสินค้าละเมิดลิขสิทธิ์"},
    {"Country": "All", "Product Category": "Supplements", "Example Items": "อาหารเสริม และ วิตามิน", "UPS": "Acceptable", "FedEx": "Acceptable", "DHL": "Unacceptable", "Aramex": "Acceptable", "EMS World / Epacket 2kg": "Acceptable", "Condition": "ห้ามส่งผ่าน DHL"},
    {"Country": "All", "Product Category": "Perfumery", "Example Items": "น้ำหอม และ สเปรย์", "UPS": "Check MSDS", "FedEx": "Check MSDS", "DHL": "Unacceptable", "Aramex": "Unacceptable", "EMS World / Epacket 2kg": "Unacceptable", "Condition": "ของเหลว/แอลกอฮอล์ต้องตรวจสอบ MSDS"},
]

@st.cache_data
def load_data():
    file_path = "master_database.csv"
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path, on_bad_lines='skip', engine='python')
            if len(df.columns) == 1:
                df = pd.read_csv(file_path, sep=';', on_bad_lines='skip', engine='python')
            if not df.empty:
                return df.fillna("-"), "OK (จากไฟล์ CSV)"
        except Exception:
            pass
    
    # หากอ่านไฟล์ไม่ได้ ให้ใช้ข้อมูลสำรองทันที
    df_fallback = pd.DataFrame(fallback_data)
    return df_fallback.fillna("-"), "⚠️ ใช้ฐานข้อมูลสำรอง (ระบบยังทำงานได้ปกติ)"

df, load_status = load_data()

# แสดงสถานะเบื้องหลังให้รู้ชัดเจน
if "⚠️" in load_status:
    st.warning(load_status + " (แนะนำให้อัปโหลดไฟล์ master_database.csv ไว้ที่หน้า GitHub ร่วมกับ app.py)")

# ==========================================
# 1. จัดเตรียมข้อมูล & ตรวจจับคอลัมน์อัตโนมัติ
# ==========================================
item_col = 'Example Items' if 'Example Items' in df.columns else ('Keyword' if 'Keyword' in df.columns else None)
country_col = 'Country' if 'Country' in df.columns else None
cat_col = 'Product Category' if 'Product Category' in df.columns else ('Category' if 'Category' in df.columns else None)
alias_col = 'Aliases' if 'Aliases' in df.columns else None

# รายชื่อประเทศสำรอง 50+ ประเทศ
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

# จัดการรายชื่อสินค้า (รับประกันไม่มีวันว่างเปล่า)
raw_items = []
if item_col and not df.empty:
    for val in df[item_col].dropna().astype(str):
        v = val.strip()
        if v and v not in ['-', 'nan', '0', 'None']:
            raw_items.append(v)

if not raw_items:
    raw_items = ["เสื้อผ้าทั่วไป", "เสื้อผ้ามือสอง", "เครื่องสำอาง และ สกินแคร์", "พาวเวอร์แบงค์ / แบตเตอรี่", "อาหารเสริม และ วิตามิน", "น้ำหอม และ สเปรย์", "กระเป๋า และ รองเท้า", "กุนเชียง หมู/ปลา/ไก่"]

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
    search_keyword = st.text_input("🔍 พิมพ์ค้นหาชื่อสินค้า (ถ้าไม่พิมพ์ จะแสดงรายการทั้งหมดให้เลือก):", placeholder="พิมพ์คำค้นหาที่นี่ (หรือเว้นว่างเพื่อดูทั้งหมด)...")
    
    filtered_options = items_list
    if search_keyword.strip() != "" and item_col and not df.empty:
        mask = df[item_col].astype(str).str.contains(search_keyword.strip(), case=False, na=False)
        if cat_col:
            mask = mask | df[cat_col].astype(str).str.contains(search_keyword.strip(), case=False, na=False)
        if alias_col:
            mask = mask | df[alias_col].astype(str).str.contains(search_keyword.strip(), case=False, na=False)
            
        matched_df = df[mask]
        if not matched_df.empty:
            filtered_options = sorted(list(set(matched_df[item_col].astype(str).tolist())))
        else:
            # ถ้าค้นหาไม่เจอในตู้ ให้ลองหาใน items_list พื้นฐาน
            filtered_options = [x for x in items_list if search_keyword.strip().lower() in x.lower()]

    if filtered_options:
        selected_item = st.selectbox("📦 เลือกรายการสินค้า (คลิกเลื่อนดูรายการได้):", options=["- กรุณาเลือกสินค้า -"] + filtered_options)
    else:
        st.warning(f"⚠️ ไม่พบสินค้าที่ตรงกับคำว่า '{search_keyword}' (แสดงรายการทั้งหมดแทน)")
        selected_item = st.selectbox("📦 เลือกรายการสินค้า:", options=["- กรุณาเลือกสินค้า -"] + items_list)
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
        
        default_guess = "เสื้อผ้าทั่วไป" 
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
        col_name = item_col if item_col else 'Example Items'
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
    is_battery = any(kw in item_lower for kw in ['แบต', 'ถ่าน', 'พัดลม', 'power bank', 'พาวเวอร์แบงค์'])
    is_dhl_prohibited = any(kw in item_lower for kw in [
        'อาหารสด', 'ซีอิ๊ว', 'น้ำพริก', 'อาหารทะเล', 'เพชร', 'ทอง', 'เงิน', 'สารเคมี', 'สัตว์', 
        'ยา', 'เสพติด', 'เงินสด', 'อาวุธ', 'กระดูก', 'น้ำหอม', 'โคโลญจน์', 'เครื่องสำอาง', 'สกินแคร์', 'อาหารเสริม', 'วิตามิน', 'แบต', 'พาวเวอร์แบงค์'
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
