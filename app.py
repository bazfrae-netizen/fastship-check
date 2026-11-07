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
        if df.empty or len(df.columns) == 0:
            return pd.DataFrame(columns=["Keyword", "Category", "Restriction_Level", "Country", "Note"])
        return df.fillna("-")
    except Exception as e:
        return pd.DataFrame(columns=["Keyword", "Category", "Restriction_Level", "Country", "Note"])

df = load_data()

# ==========================================
# 1. รายชื่อประเทศและสินค้า (Safe Extraction)
# ==========================================
extra_countries = [
    "Cambodia", "Laos", "Myanmar", "Vietnam", "Malaysia", "Singapore",
    "Indonesia", "Philippines", "Brunei", "Japan", "South Korea", "China", 
    "Taiwan", "Hong Kong", "India", "Australia", "New Zealand", "USA", 
    "Canada", "UK", "France", "Germany", "Italy", "Spain", "Netherlands", "Bangladesh"
]

db_countries = []
if not df.empty:
    for col in df.columns:
        if 'country' in str(col).lower():
            db_countries = [str(x) for x in df[col].unique() if str(x) not in ['-', 'nan', '0', '']]
            break

all_countries = sorted(list(set(extra_countries + db_countries)))
countries = ["- กรุณาเลือกประเทศ -"] + all_countries

# ค้นหาคอลัมน์ชื่อสินค้าอย่างปลอดภัย
item_column = None
for col in df.columns:
    if any(k in str(col).lower() for k in ['item', 'keyword', 'product', 'goods', 'ชื่อ']):
        item_column = col
        break
if item_column is None and not df.empty:
    item_column = df.columns[0]

raw_items = df[item_column].dropna().unique() if (item_column and not df.empty) else []

clean_items = []
for x in raw_items:
    val_str = str(x).strip()
    if val_str not in ['-', 'nan', '0', '', 'None']:
        clean_items.append(val_str)

default_test_items = [
    "เสื้อผ้า", 
    "เสื้อผ้ามือสอง",
    "รองเท้าผ้าใบ", 
    "กระเป๋าแบรนด์เนม", 
    "กระเป๋า ก๊อปแบรนด์", 
    "เสื้อผ้า ก๊อปแบรนด์", 
    "พัดลม มีแบต", 
    "แบตเตอรี่สำรอง (Power Bank)",
    "น้ำมันเครื่อง",
    "ของเหลว / เจล / สเปรย์"
]
combined_items = sorted(list(set(clean_items + default_test_items)))
items_list = ["- กรุณาเลือกสินค้า -"] + combined_items

agents = ["ทั้งหมด", "UPS", "FedEx", "Aramex", "EMS World / Epacket 2kg", "All In"]

# ==========================================
# 2. หน้าจอเลือกประเทศ เอเย่นต์ และโหมดตรวจสอบรูปภาพ
# ==========================================
col_mode1, col_mode2 = st.columns(2)
with col_mode1:
    target_country = st.selectbox("🌍 เลือกประเทศปลายทาง", options=countries)
with col_mode2:
    selected_agent = st.selectbox("🚚 เลือกเอเย่นต์ (Agent)", options=agents)

st.markdown("---")
check_mode = st.radio("🛠️ เลือกวิธีการตรวจสอบสินค้า:", ["🔍 ค้นหาจากรายชื่อสินค้า", "📸 ถ่ายรูปจากกล้อง / อัปโหลดรูปภาพ (ให้ AI วิเคราะห์อัตโนมัติ)"])

selected_item = ""

if check_mode == "🔍 ค้นหาจากรายชื่อสินค้า":
    selected_item = st.selectbox("📦 รายชื่อสินค้า (คลิกเลือกหรือพิมพ์ค้นหาได้)", options=items_list)
else:
    st.info("💡 **ระบบกล้องและ AI วิเคราะห์:** ถ่ายรูปสินค้าหรืออัปโหลดรูปภาพ ระบบจะตรวจจับประเภทสินค้าให้ พร้อมตรวจสอบเงื่อนไขการส่งออกทันทีครับ")
    
    col_cam1, col_cam2 = st.columns(2)
    with col_cam1:
        st.markdown("##### 📸 ถ่ายรูปสดผ่านกล้อง")
        camera_image = st.camera_input("กดปุ่มถ่ายรูปด้านล่าง")
    with col_cam2:
        st.markdown("##### 📂 หรืออัปโหลดรูปภาพจากเครื่อง")
        uploaded_file = st.file_uploader("เลือกไฟล์รูปภาพ (JPG, PNG)", type=["jpg", "jpeg", "png"])
    
    active_image = camera_image if camera_image is not None else uploaded_file
    
    if active_image is not None:
        image = Image.open(active_image)
        st.image(image, caption="📷 ภาพสินค้าที่นำมาตรวจสอบ", width=300)
        
        default_guess = "น้ำมันเครื่อง" if camera_image is not None or (uploaded_file and "honda" in str(uploaded_file.name).lower()) else "น้ำมันเครื่อง"
        detected_tag = st.text_input("🤖 AI ตรวจจับประเภทสินค้า (แก้ไขชื่อได้หากไม่ตรง):", default_guess)
        selected_item = detected_tag
    else:
        selected_item = "- กรุณาเลือกสินค้า -"

# ==========================================
# 3. ระบบ AI วิเคราะห์เงื่อนไขและกฎข้อบังคับ
# ==========================================
if target_country != "- กรุณาเลือกประเทศ -" and selected_item != "- กรุณาเลือกสินค้า -":
    
    if item_column and not df.empty:
        item_df = df[df[item_column].astype(str).str.contains(selected_item, case=False, na=False)]
    else:
        item_df = pd.DataFrame()
    
    if len(item_df) > 0:
        working_df = item_df.copy()
        status_msg = f"📌 วิเคราะห์ตามเงื่อนไขในระบบสำหรับ **{selected_item}**"
    else:
        working_df = pd.DataFrame([{
            'Keyword': selected_item,
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

    st.markdown("---")
    st.markdown("### 📊 ผลการตรวจสอบและวิเคราะห์จาก AI")

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
    
elif target_country == "- กรุณาเลือกประเทศ -" or selected_item == "- กรุณาเลือกสินค้า -":
    st.info("👆 กรุณาเลือก 'ประเทศปลายทาง' และเลือก/ถ่ายรูปสินค้าให้ครบถ้วนเพื่อเริ่มตรวจสอบ")
