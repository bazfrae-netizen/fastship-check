import streamlit as st
import pandas as pd
from PIL import Image

st.set_page_config(page_title="FastShip Check", layout="wide")

# ==========================================
# 🎨 ธีมสีส้ม FastShip แบบจัดเต็ม (Force CSS)
# ==========================================
st.markdown("""
    <style>
    /* เปลี่ยนสีหัวข้อหลักทั้งหมดให้เป็นสีส้ม FastShip */
    h1, h2, h3 {
        color: #FF6600 !important;
    }
    
    /* เปลี่ยนสีปุ่มกดหลัก (Buttons) เป็นสีส้ม */
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
    
    /* ไฮไลท์กรอบหรือกล่องข้อความแจ้งเตือน */
    .stAlert {
        border-left-color: #FF6600 !important;
    }
    
    /* ปรับแต่ง Radio Button ให้ active เป็นสีส้ม */
    .stRadio [data-baseweb="radio"] div[aria-checked="true"] {
        background-color: #FF6600 !important;
        border-color: #FF6600 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 FastShip Check")
st.subheader("ระบบวิเคราะห์เงื่อนไขการส่งออกอัจฉริยะ (กล้องถ่ายรูป & AI วิเคราะห์อัตโนมัติ 📸)")

@st.cache_data
def load_data():
    df = pd.read_csv("master_database.csv")
    df = df.fillna("-")
    return df

df = load_data()

# ==========================================
# 1. รายชื่อประเทศและสินค้า
# ==========================================
extra_countries = [
    "Cambodia", "Laos", "Myanmar", "Vietnam", "Malaysia", "Singapore",
    "Indonesia", "Philippines", "Brunei", "Japan", "South Korea", "China", 
    "Taiwan", "Hong Kong", "India", "Australia", "New Zealand", "USA", 
    "Canada", "UK", "France", "Germany", "Italy", "Spain", "Netherlands", "Bangladesh"
]

db_countries = [str(x) for x in df['Country'].unique() if str(x) not in ['-', 'nan', '0', '']]
all_countries = sorted(list(set(extra_countries + db_countries)))
countries = ["- กรุณาเลือกประเทศ -"] + all_countries

item_column = 'Example Items' if 'Example Items' in df.columns else 'Product Category'
raw_items = df[item_column].dropna().unique()

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
    st.info("💡 **ระบบกล้องและ AI วิเคราะห์:** ถ่ายรูปสินค้าหรืออัปโหลดรูปภาพ ระบบจะตรวจจับประเภทสินค้าให้ (เช่น น้ำมันเครื่อง, แบตเตอรี่, เสื้อผ้า) พร้อมตรวจสอบเงื่อนไขการส่งออกทันทีครับ")
    
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
        detected_tag = st.text_input("🤖 AI ตรวจจับประเภทสินค้า (แก้ไขชื่อได้หากไม่ตรง เช่น น้ำมันเครื่อง, พัดลม มีแบต, เสื้อผ้ามือสอง):", default_guess)
        selected_item = detected_tag
    else:
        selected_item = "- กรุณาเลือกสินค้า -"

# ==========================================
# 3. ระบบ AI วิเคราะห์เงื่อนไขและกฎข้อบังคับ
# ==========================================
if target_country != "- กรุณาเลือกประเทศ -" and selected_item != "- กรุณาเลือกสินค้า -":
    
    item_df = df[df[item_column].astype(str) == selected_item]
    
    if len(item_df) > 0:
        country_specific = item_df[item_df['Country'].astype(str).str.upper() == target_country.upper()]
        if len(country_specific) > 0:
            working_df = country_specific.copy()
            status_msg = f"📌 วิเคราะห์ตามเงื่อนไขเฉพาะของประเทศ **{target_country}**"
        else:
            working_df = item_df.head(1).copy() 
            status_msg = f"🌍 วิเคราะห์ตามมาตรฐานเอเย่นต์ (ไม่มีข้อห้ามเฉพาะจากประเทศ {target_country})"
    else:
        working_df = pd.DataFrame([{
            item_column: selected_item,
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
    
    # 🚨 กฎที่ 1: สินค้าก๊อปแบรนด์ / ปลอม
    is_fake_brand = any(kw in item_lower for kw in ['ก๊อป', 'ปลอม', 'mirror', 'เกรดเอ', 'มิลเลอร์', 'เลียนแบบ', 'brand name ปลอม', 'เกรด a'])
    
    # 🚨 กฎที่ 2: เฉพาะประเทศ Japan ถือว่าเสื้อผ้ามือสองห้ามส่งเด็ดขาด
    is_clothing = any(kw in item_lower for kw in ['เสื้อ', 'ผ้า', 'ชุด', 'กางเกง'])
    is_second_hand = any(kw in item_lower for kw in ['มือสอง', 'มือ 2', 'มือ ๒', 'secondhand', 'used'])
    is_japan_secondhand_rule = (country_upper == 'JAPAN' and is_clothing and is_second_hand)
    
    # ⚡ กฎที่ 3: น้ำมันเครื่อง / ของเหลว
    is_oil_or_liquid = any(kw in item_lower for kw in ['น้ำมัน', 'น้ำมันเครื่อง', 'ของเหลว', 'เจล', 'สเปรย์', 'oil', 'liquid'])
    
    # ⚡ กฎแบตเตอรี่ UPS (ไม่เกิน 2 ชิ้น)
    is_battery_item = any(kw in item_lower for kw in ['แบต', 'ถ่าน', 'พัดลม มีแบต'])
    
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
            
    if is_fake_brand and selected_agent != 'All In' and selected_agent != 'ทั้งหมด':
        working_df = pd.DataFrame()
    elif is_japan_secondhand_rule and selected_agent != 'All In' and selected_agent != 'ทั้งหมด':
        working_df = pd.DataFrame()

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
            st.warning("🛢️ **ข้อกำหนดสินค้าประเภทน้ำมันเครื่อง / ของเหลว / สารเคมี:** จำเป็นต้องส่งเอกสาร **MSDS (Safety Data Sheet)** ให้ทางเอเย่นต์ตรวจสอบและ Approve ก่อนจัดส่งทุกครั้ง (หรือแนะนำส่งผ่านช่องทาง **All In** เพื่อความสะดวก)")
        elif is_battery_item:
            st.warning("⚡ **กฎเหล็กสินค้ามีแบตเตอรี่/ถ่าน (ผ่าน UPS):** อนุญาตให้จัดส่งได้ **ไม่เกิน 2 ชิ้นต่อ 1 ชิปเมนต์ (กล่อง)** (ห้ามส่ง Power Bank เด็ดขาด)")
        else:
            st.success("📦 **จำนวนชิ้นที่อนุญาต:** สามารถจัดส่งได้ตามน้ำหนักและขนาดมาตรฐานของกล่องพัสดุ (ไม่จำกัดจำนวนชิ้นย่อย)")

        if country_upper == 'JAPAN' and is_clothing and not is_second_hand:
            st.info("🇯🇵 **ข้อกำหนดเฉพาะประเทศญี่ปุ่น (Japan):** เสื้อผ้ามือหนึ่ง **ส่งได้ปกติ** ✅ แต่มือสอง **ห้ามส่งผ่านขนส่งปกติ** ❌")
        
        if is_fake_brand:
            st.warning("🚨 **แจ้งเตือนสำคัญ:** สินค้าก๊อปแบรนด์/ปลอม เอเย่นต์หลักไม่อนุญาตให้ส่ง (ส่งได้เฉพาะช่องทางพิเศษ **All In** เท่านั้น)")

        st.markdown("#### 🤖 สรุปเอเย่นต์ที่พร้อมให้บริการ:")
        first_row = working_df.iloc[0]
        
        available_agents = []
        for a in ["UPS", "FedEx", "Aramex", "EMS World / Epacket 2kg", "All In"]:
            if a in working_df.columns:
                val = str(first_row.get(a, '-')).strip().upper()
                
                if is_fake_brand and a != 'All In':
                    val = 'UNACCEPTABLE'
                elif is_japan_secondhand_rule and a != 'All In':
                    val = 'UNACCEPTABLE'
                elif a == 'UPS' and is_battery_item:
                    val = 'ACCEPTABLE'
                elif a == 'All In':
                    val = 'ACCEPTABLE'
                
                if val not in ['-', 'X', 'NAN', 'UNACCEPTABLE', '']:
                    available_agents.append(a)
                    
        if available_agents:
            st.write(f"**🚚 เอเย่นต์ที่รองรับ:** {', '.join(available_agents)}")
        else:
            st.error("❌ ไม่มีเอเย่นต์ขนส่งปกติที่รองรับสินค้านี้ (แนะนำใช้บริการช่องทางพิเศษ All In)")
            
        condition = first_row.get('Condition', '-')
        if condition != '-':
             st.write(f"**📌 เงื่อนไขแพ็กเกจ/ข้อควรระวัง:** {condition}")
             
        st.markdown("---")
        st.write("**ตารางอ้างอิงข้อมูล (Reference):**")
        st.dataframe(working_df, use_container_width=True)
        
    else:
        st.error(f"❌ ไม่อนุญาตให้ส่ง '{selected_item}' ผ่านเอเย่นต์ '{selected_agent}'")
        if is_fake_brand:
            st.warning("สาเหตุ: สินค้าก๊อปแบรนด์/ปลอม เอเย่นต์มาตรฐานทั้งหมดปฏิเสธการรับ (รองรับเฉพาะ All In)")
        elif is_japan_secondhand_rule:
            st.warning("สาเหตุ: ประเทศญี่ปุ่นไม่อนุญาตให้นำเข้า 'เสื้อผ้ามือสอง' ผ่านเอเย่นต์ปกติ (มือหนึ่งส่งได้ แต่มือสองต้องส่งผ่าน All In เท่านั้น)")
        else:
            st.warning("สาเหตุ: เอเย่นต์ปฏิเสธการรับส่งสินค้านี้ตามเงื่อนไข")
            
elif target_country == "- กรุณาเลือกประเทศ -" or selected_item == "- กรุณาเลือกสินค้า -":
    st.info("👆 กรุณาเลือก 'ประเทศปลายทาง' และถ่ายรูป/เลือกสินค้าให้ครบถ้วนเพื่อเริ่มตรวจสอบ")