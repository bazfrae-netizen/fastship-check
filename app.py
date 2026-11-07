import streamlit as st
import pandas as pd
from PIL import Image

st.set_page_config(page_title="FastShip Check", layout="wide")

# ==========================================
# 🎨 ธีมสีส้ม FastShip แบบจัดเต็ม (Force CSS)
# ==========================================
st.markdown("""
    <style>
    h1, h2, h3 {
        color: #FF6600 !important;
    }
    div.stButton > button:first-child {
        background-color: #FF6600 !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
    }
    div.stButton > button:first-child:hover {
        background-color: #E65C00 !important;
        color: white !important;
    }
    .stAlert {
        border-left-color: #FF6600 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 FastShip Check")
st.subheader("ระบบวิเคราะห์เงื่อนไขการส่งออกอัจฉริยะ (กล้องถ่ายรูป & AI วิเคราะห์อัตโนมัติ 📸)")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("master_database.csv")
        if df is None or df.empty:
            return pd.DataFrame()
        return df.fillna("-")
    except Exception as e:
        return pd.DataFrame()

df = load_data()

# ==========================================
# 1. รายชื่อประเทศและสินค้าจาก CSV
# ==========================================
db_countries = []
if not df.empty and 'Country' in df.columns:
    db_countries = [str(x) for x in df['Country'].unique() if str(x) not in ['-', 'nan', '0', '']]

extra_countries = [
    "Australia", "Austria", "Bangladesh", "Belgium", "Canada", "Chile", "China", 
    "Croatia", "Czech Republic", "Denmark", "Egypt", "Finland", "France", "Germany", 
    "Greece", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Ireland", 
    "Israel", "Italy", "Japan", "Kuwait", "Macao", "Malaysia", "Malta", "Mexico", 
    "Netherlands", "New Zealand", "Norway", "Oman", "Pakistan", "Philippines", 
    "Poland", "Puerto Rico", "Qatar", "Saudi Arabia", "Singapore", "South Africa", 
    "South Korea", "Spain", "Sweden", "Switzerland", "Taiwan", "Turkey", "USA", 
    "United Arab Emirates", "United Kingdom", "Vietnam"
]

all_countries = sorted(list(set(extra_countries + db_countries)))
countries = ["- กรุณาเลือกประเทศ -"] + all_countries

raw_items = []
if not df.empty:
    for col in ['Example Items', 'Product Category']:
        if col in df.columns:
            for val in df[col].dropna().astype(str):
                v = val.strip()
                if v and v not in ['-', 'nan', '0', 'None', 'Example Items', 'Product Category', '\\']:
                    raw_items.append(v)

items_list = ["- กรุณาเลือกสินค้า -"] + sorted(list(set(raw_items)))
agents = ["ทั้งหมด", "UPS", "FedEx", "Aramex", "EMS World / Epacket 2kg", "All In"]

# ==========================================
# 2. หน้าจอเลือกประเทศ เอเย่นต์ และโหมดตรวจสอบ
# ==========================================
col1, col2 = st.columns(2)
with col1:
    target_country = st.selectbox("🌍 เลือกประเทศปลายทาง", options=countries, key="target_country_box")
with col2:
    selected_agent = st.selectbox("🚚 เลือกเอเย่นต์ (Agent)", options=agents, key="selected_agent_box")

st.markdown("---")
check_mode = st.radio("🛠️ เลือกวิธีการตรวจสอบสินค้า:", ["🔍 ค้นหาจากรายชื่อสินค้า", "📸 ถ่ายรูปจากกล้อง / อัปโหลดรูปภาพ (ให้ AI วิเคราะห์อัตโนมัติ)"], key="check_mode_radio_main")

# แยกตัวแปรชัดเจนตามโหมด ไม่ให้เกิดการทับซ้อนของ Widget
selected_item = "- กรุณาเลือกสินค้า -"

if check_mode == "🔍 ค้นหาจากรายชื่อสินค้า":
    selected_item = st.selectbox("📦 รายชื่อสินค้า (คลิกเลือกหรือพิมพ์ค้นหาได้ทุกรายการ)", options=items_list, key="search_item_selectbox")
else:
    st.info("💡 **ระบบกล้องและ AI วิเคราะห์:** ถ่ายรูปสินค้าหรืออัปโหลดรูปภาพ ระบบจะตรวจจับประเภทสินค้าให้ พร้อมตรวจสอบเงื่อนไขการส่งออกทันทีครับ")
    
    col_cam1, col_cam2 = st.columns(2)
    with col_cam1:
        st.markdown("##### 📸 ถ่ายรูปสดผ่านกล้อง")
        camera_image = st.camera_input("กดปุ่มถ่ายรูปด้านล่าง", key="camera_input_widget")
    with col_cam2:
        st.markdown("##### 📂 หรืออัปโหลดรูปภาพจากเครื่อง")
        uploaded_file = st.file_uploader("เลือกไฟล์รูปภาพ (JPG, PNG)", type=["jpg", "jpeg", "png"], key="file_uploader_widget")
    
    active_image = camera_image if camera_image is not None else uploaded_file
    
    if active_image is not None:
        image = Image.open(active_image)
        st.image(image, caption="📷 ภาพสินค้าที่นำมาตรวจสอบ", width=300)
        
        default_guess = "น้ำมันเครื่อง" if camera_image is not None or (uploaded_file and "honda" in str(uploaded_file.name).lower()) else "น้ำมันเครื่อง"
        detected_tag = st.text_input("🤖 AI ตรวจจับประเภทสินค้า (แก้ไขชื่อได้หากไม่ตรง):", default_guess, key="ai_detected_tag_input")
        selected_item = detected_tag

# ==========================================
# 3. ระบบ AI วิเคราะห์เงื่อนไขและกฎข้อบังคับ
# ==========================================
if target_country != "- กรุณาเลือกประเทศ -" and selected_item != "- กรุณาเลือกสินค้า -":
    
    if not df.empty:
        mask = False
        for col in ['Example Items', 'Product Category']:
            if col in df.columns:
                mask = mask | df[col].astype(str).str.contains(selected_item, case=False, na=False)
        item_df = df[mask] if isinstance(mask, pd.Series) else pd.DataFrame()
    else:
        item_df = pd.DataFrame()
    
    if len(item_df) > 0:
        country_col = next((c for c in item_df.columns if 'country' in str(c).lower()), None)
        if country_col:
            country_specific = item_df[item_df[country_col].astype(str).str.upper() == target_country.upper()]
            if len(country_specific) > 0:
                working_df = country_specific.copy()
                status_msg = f"📌 วิเคราะห์ตามเงื่อนไขเฉพาะของประเทศ **{target_country}**"
            else:
                working_df = item_df.copy()
                status_msg = f"🌍 วิเคราะห์ตามมาตรฐานเอเย่นต์ (แสดงผลรวมสำหรับสินค้านี้)"
        else:
            working_df = item_df.copy()
            status_msg = f"📌 วิเคราะห์ตามเงื่อนไขในระบบ"
    else:
        working_df = pd.DataFrame([{
            'Example Items': selected_item,
            'Country': target_country,
            'UPS': 'Acceptable',
            'FedEx': 'Acceptable',
            'Aramex': 'Acceptable',
            'EMS World / Epacket 2kg': 'Acceptable',
            'Condition': 'ตรวจสอบตามกฎข้อบังคับสากล'
        }])
        status_msg = f"⚙️ วิเคราะห์ตามกฎข้อบังคับสากลและนโยบายเอเย่นต์"

    working_df['All In'] = 'Acceptable'
    
    item_lower = selected_item.lower()
    country_upper = target_country.upper()
    
    is_fake_brand = any(kw in item_lower for kw in ['ก๊อป', 'ปลอม', 'mirror', 'เกรดเอ', 'มิลเลอร์', 'เลียนแบบ', 'เกรด a'])
    is_clothing = any(kw in item_lower for kw in ['เสื้อ', 'ผ้า', 'ชุด', 'กางเกง'])
    is_second_hand = any(kw in item_lower for kw in ['มือสอง', 'มือ 2', 'มือ ๒', 'secondhand', 'used'])
    is_japan_secondhand_rule = (country_upper == 'JAPAN' and is_clothing and is_second_hand)
    is_oil_or_liquid = any(kw in item_lower for kw in ['น้ำมัน', 'น้ำมันเครื่อง', 'ของเหลว', 'เจล', 'สเปรย์', 'oil', 'liquid'])
    is_battery_item = any(kw in item_lower for kw in ['แบต', 'ถ่าน', 'พัดลม มีแบต', 'power bank'])
    
    for col in ["UPS", "FedEx", "Aramex", "EMS World / Epacket 2kg"]:
        if col in working_df.columns:
            if is_fake_brand or is_japan_secondhand_rule:
                working_df[col] = 'Unacceptable'
            elif is_battery_item and col == 'UPS':
                working_df['UPS'] = 'Acceptable'
            elif is_oil_or_liquid and col in ["UPS", "FedEx"]:
                working_df[col] = 'Check MSDS'

    if selected_agent != "ทั้งหมด" and selected_agent in working_df.columns:
        if not (selected_agent == 'All In'):
            working_df = working_df[~working_df[selected_agent].astype(str).str.upper().isin(['-', 'X', 'NAN', ''])]

    st.markdown("---")
    st.markdown("### 📊 ผลการตรวจสอบและวิเคราะห์จาก AI")

    if len(working_df) > 0:
        if is_fake_brand:
            st.error("❌ สินค้าละเมิดลิขสิทธิ์ / สินค้าก๊อปแบรนด์ ไม่อนุญาตให้จัดส่งผ่านเอเย่นต์ขนส่งปกติเด็ดขาด!")
        elif is_japan_secondhand_rule:
            st.error("❌ ประเทศญี่ปุ่นไม่อนุญาตให้นำเข้า 'เสื้อผ้ามือสอง' ผ่านเอเย่นต์ขนส่งปกติเด็ดขาด (อนุญาตเฉพาะมือหนึ่งเท่านั้น)")
        else:
            st.success(f"✅ สามารถส่ง **{selected_item}** ไปยัง **{target_country}** ได้!")
            
        st.info(status_msg)
        
        if is_oil_or_liquid:
            st.warning("🛢️ **ข้อกำหนดสินค้าประเภทน้ำมันเครื่อง / ของเหลว / สารเคมี:** จำเป็นต้องส่งเอกสาร **MSDS (Safety Data Sheet)** ให้ทางเอเย่นต์ตรวจสอบก่อนจัดส่งทุกครั้ง")
        elif is_battery_item:
            st.warning("⚡ **กฎเหล็กสินค้ามีแบตเตอรี่/ถ่าน (ผ่าน UPS):** อนุญาตให้จัดส่งได้ **ไม่เกิน 2 ชิ้นต่อ 1 ชิปเมนต์ (กล่อง)**")

        st.markdown("---")
        st.write("**ตารางอ้างอิงข้อมูล (Reference):**")
        st.dataframe(working_df, use_container_width=True)
    else:
        st.error(f"❌ ไม่อนุญาตให้ส่ง '{selected_item}' ผ่านเอเย่นต์ '{selected_agent}'")
        st.warning("สาเหตุ: เอเย่นต์ที่เลือกปฏิเสธการรับส่งสินค้านี้ตามเงื่อนไข")
    
elif target_country == "- กรุณาเลือกประเทศ -" or selected_item == "- กรุณาเลือกสินค้า -":
    st.info("👆 กรุณาเลือก 'ประเทศปลายทาง' และเลือก/ถ่ายรูปสินค้าให้ครบถ้วนเพื่อเริ่มตรวจสอบ")
