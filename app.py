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
st.subheader("รายการข้อมูลส่งออก")
st.markdown("---")

@st.cache_data
def load_data():
    file_path = "master_database.csv"
    if os.path.exists(file_path):
        try:
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

items_list = []
if not df.empty and 'Example Items' in df.columns:
    raw_items = df['Example Items'].dropna().astype(str).tolist()
    # ดึงคำที่ซ้ำซ้อนออก และเพิ่มคำว่า "เสื้อผ้า" เข้าไปให้เลือกได้โดยตรง!
    items_list = sorted(list(set([x.strip() for x in raw_items if x.strip() and x.strip() not in ['-', 'nan', '0', 'None', 'Example Items']])))
    if "สินค้ามือ 2" in items_list:
        items_list.append("เสื้อผ้ามือ 2 (สินค้ามือ 2)")
    if "สินค้าแบรนด์เนม (Luxury Brand)" in items_list:
        items_list.append("เสื้อผ้าแบรนด์เนม / เสื้อผ้าทั่วไป")

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
check_mode = st.radio("🛠️ เลือกวิธีการตรวจสอบสินค้า:", ["🔍 ค้นหาและเลือกรายชื่อสินค้า", "📸 ถ่ายรูป/อัปโหลดรูปภาพ (AI วิเคราะห์)"], horizontal=True)

selected_item = "- กรุณาเลือกสินค้า -"

if check_mode == "🔍 ค้นหาและเลือกรายชื่อสินค้า":
    selected_item = st.selectbox(f"📋 เลือกรายการสินค้า ({len(items_list)} รายการ):", options=["- กรุณาเลือกสินค้า -"] + items_list)
else:
    st.info("💡 ถ่ายรูปหรืออัปโหลดภาพสินค้าเพื่อให้ระบบ AI ช่วยค้นหาหมวดหมู่ที่ตรงกัน")
    c_img1, c_img2 = st.columns(2)
    with c_img1:
        camera_image = st.camera_input("ถ่ายภาพสินค้า")
    with c_img2:
        uploaded_file = st.file_uploader("อัปโหลดไฟล์รูปภาพ", type=["jpg", "jpeg", "png"])
    
    active_img = camera_image if camera_image else uploaded_file
    
    if 'ai_predicted' not in st.session_state:
        st.session_state.ai_predicted = ""

    if active_img:
        img = Image.open(active_img)
        st.image(img, caption="ภาพสินค้าของคุณ", width=250)
        
        if st.button("✨ ให้ AI วิเคราะห์ภาพนี้"):
            try:
                import google.generativeai as genai
                if "GEMINI_API_KEY" in st.secrets:
                    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    with st.spinner("🤖 AI กำลังใช้สายตาประมวลผล..."):
                        # สั่ง AI ให้ตอบคำที่ตรงกับฐานข้อมูลของเรา
                        prompt = "วิเคราะห์ภาพนี้ว่าคืออะไร และจัดหมวดหมู่ให้ตรงกับคำเหล่านี้เท่านั้น: 'บะหมี่กึ่งสำเร็จรูป', 'เครื่องสำอาง', 'เสื้อผ้ามือ 2 (สินค้ามือ 2)', 'แบตเตอรี่', 'ของเหลว', 'อาหารเสริม', 'ขนม'. ตอบมาแค่ 1 คำเท่านั้น"
                        response = model.generate_content([prompt, img])
                        st.session_state.ai_predicted = response.text.strip()
                else:
                    st.error("⚠️ ไม่พบ GEMINI_API_KEY ใน Streamlit Secrets")
            except ImportError:
                st.error("⚠️ ขาดไลบรารี AI! กรุณาเปลี่ยนชื่อไฟล์ equirements.txt เป็น requirements.txt ใน GitHub ก่อน")
            except Exception as e:
                st.error(f"❌ เกิดข้อผิดพลาด: {e}")

        if st.session_state.ai_predicted:
            st.success(f"🤖 AI วิเคราะห์หมวดหมู่สินค้าคือ: **{st.session_state.ai_predicted}**")
            kw = st.session_state.ai_predicted.lower()
            
            # ดักจับคำที่ AI น่าจะตอบมาเพื่อโยงเข้าชื่อสินค้าจริงๆ ในระบบ
            search_terms = [kw]
            if any(x in kw for x in ["อาหาร", "บะหมี่", "มาม่า", "food", "ขนม", "กุนเชียง", "น้ำพริก"]): search_terms.extend(["บะหมี่", "อาหาร", "ขนม", "กุนเชียง"])
            if any(x in kw for x in ["เสื้อ", "ผ้า", "แบรนด์", "มือสอง"]): search_terms.extend(["เสื้อผ้า", "สินค้ามือ 2", "สินค้าแบรนด์เนม"])
            if any(x in kw for x in ["ครีม", "สบู่", "โลชั่น"]): search_terms.extend(["เซรั่ม", "ครีมทาผิว", "สบู่"])
            
            matched_items = [item for item in items_list if any(term in item.lower() for term in search_terms)]
            
            if matched_items:
                selected_item = st.selectbox(f"📋 AI พบหมวดหมู่ที่ตรงกับภาพ ({len(matched_items)} รายการ):", options=["- กรุณาเลือกสินค้า -"] + matched_items)
            else:
                st.warning("⚠️ AI ค้นหาไม่พบหมวดหมู่ที่ใกล้เคียง กรุณาเลือกจากรายการเต็มด้านล่าง")
                selected_item = st.selectbox(f"📋 เลือกรายการสินค้าทั้งหมด:", options=["- กรุณาเลือกสินค้า -"] + items_list)

# ==========================================
# 3. ผลการตรวจสอบเงื่อนไข
# ==========================================
if target_country != "- กรุณาเลือกประเทศ -" and selected_item != "- กรุณาเลือกสินค้า -":
    st.markdown("---")
    st.markdown("### 📊 ผลการตรวจสอบข้อกำหนดการจัดส่ง")
    
    # แปลงชื่อเสื้อผ้าที่แอบเติมไว้กลับไปเป็นชื่อดั้งเดิมเพื่อค้นหาในตาราง
    search_db_item = selected_item
    if selected_item == "เสื้อผ้ามือ 2 (สินค้ามือ 2)": search_db_item = "สินค้ามือ 2"
    if selected_item == "เสื้อผ้าแบรนด์เนม / เสื้อผ้าทั่วไป": search_db_item = "สินค้าแบรนด์เนม (Luxury Brand)"

    working_df = pd.DataFrame()
    if not df.empty and 'Example Items' in df.columns:
        item_match = df[df['Example Items'].astype(str).str.strip() == search_db_item.strip()]
        if not item_match.empty:
            country_match = item_match[item_match['Country'].astype(str).str.upper() == target_country.upper()]
            working_df = country_match.copy() if not country_match.empty else item_match.copy()
            
    if working_df.empty:
        working_df = pd.DataFrame([{
            'Example Items': selected_item, 'Country': target_country,
            'UPS': 'Acceptable', 'FedEx': 'Acceptable', 'DHL': 'Acceptable',
            'Aramex': 'Acceptable', 'EMS World / Epacket 2kg': 'Acceptable', 'All In': 'Acceptable',
            'Condition': 'ตรวจสอบตามระเบียบมาตรฐานสากล'
        }])
        
    item_lower = selected_item.lower()
    country_upper = target_country.upper()
    
    is_fake_brand = any(kw in item_lower for kw in ['ก๊อป', 'ปลอม', 'mirror', 'เกรดเอ', 'เลียนแบบ', 'ลิขสิทธิ์', 'แบรนด์เนม'])
    is_second_hand = any(kw in item_lower for kw in ['มือสอง', 'มือ 2', 'secondhand', 'used'])
    is_clothing = any(kw in item_lower for kw in ['เสื้อ', 'ผ้า', 'ชุด', 'กางเกง'])
    
    # 📌 กฎญี่ปุ่น เสื้อผ้ามือสอง
    is_japan_secondhand = (country_upper == 'JAPAN' and (is_second_hand or 'มือสอง' in item_lower or 'มือ 2' in item_lower))
    
    is_oil_liquid = any(kw in item_lower for kw in ['น้ำมัน', 'ของเหลว', 'เจล', 'สเปรย์', 'oil', 'liquid', 'น้ำหอม'])
    is_battery = any(kw in item_lower for kw in ['แบต', 'ถ่าน', 'พัดลม', 'power bank', 'พาวเวอร์แบงค์'])
    is_illegal = any(kw in item_lower for kw in ['กัญชา', 'กัญชง', 'กระท่อม', 'ฝิ่น', 'ยาเสพติด', 'อาวุธ', 'ปืน', 'กระสุน', 'ระเบิด', 'เงินสด', 'ธนบัตร'])
    is_dhl_prohibited = any(kw in item_lower for kw in ['อาหาร', 'ของกิน', 'กะปิ', 'น้ำพริก', 'เพชร', 'ทอง', 'เงิน', 'สารเคมี', 'เครื่องสำอาง', 'สกินแคร์', 'อาหารเสริม', 'วิตามิน', 'บะหมี่'])

    display_df = working_df.copy()
    
    # ถ้าส่งไปญี่ปุ่นและเป็นของมือสอง ให้ขึ้น Unacceptable ทันที
    if is_japan_secondhand:
        for col in ["UPS", "FedEx", "DHL", "Aramex", "EMS World / Epacket 2kg"]:
            if col in display_df.columns:
                display_df[col] = 'Unacceptable'
    
    if not display_df.empty:
        final_status = "Acceptable"
        if selected_agent != "ทั้งหมด":
            val = str(display_df.iloc[0][selected_agent]).strip().upper()
            if val == "UNACCEPTABLE":
                final_status = "Unacceptable"
            elif val == "CHECK MSDS":
                final_status = "Check MSDS"
        else:
            agent_cols = ["UPS", "FedEx", "DHL", "Aramex", "EMS World / Epacket 2kg", "All In"]
            can_ship = False
            for c in agent_cols:
                if c in display_df.columns and str(display_df.iloc[0][c]).strip().upper() == "ACCEPTABLE":
                    can_ship = True
                    break
            if not can_ship:
                final_status = "Unacceptable"

        if final_status == "Unacceptable":
            st.error(f"❌ **ไม่อนุญาตให้จัดส่ง** {selected_item} ไปยัง {target_country} ผ่านเอเย่นต์ที่คุณเลือก")
        elif final_status == "Check MSDS":
            st.warning(f"⚠️ **สามารถส่งได้ แต่ต้องตรวจสอบเอกสาร** {selected_item} ไปยัง {target_country}")
        else:
            st.success(f"✅ **สามารถตรวจสอบและจัดส่ง** {selected_item} ไปยัง {target_country} ได้")

        if is_illegal:
            st.error("🚨 **สินค้าผิดกฎหมาย/ควบคุมพิเศษ:** ไม่อนุญาตให้ส่งผ่านขนส่งระหว่างประเทศทุกช่องทาง (รวมถึง All In)")
        elif is_fake_brand and selected_agent != "All In":
            st.warning("⚠️ สินค้าละเมิดลิขสิทธิ์ / สินค้าแบรนด์เนม ไม่อนุญาตให้จัดส่งผ่านขนส่งปกติ แนะนำให้ส่งผ่านช่องทาง All In เท่านั้น")
            
        if is_japan_secondhand:
            st.error("❌ **ประเทศญี่ปุ่น:** สินค้ามือสองหรือเสื้อผ้ามือสอง ห้ามส่งเข้าประเทศญี่ปุ่นเด็ดขาด!")
            
        if is_battery:
            if selected_agent == "UPS" or selected_agent == "ทั้งหมด":
                st.warning("⚡ **ข้อกำหนด UPS:** UPS แบต 2 ชิ้นกับถ่าน 1 ชิ้นพกได้")
            if selected_agent == "DHL" or selected_agent == "ทั้งหมด":
                st.error("🚨 **ข้อกำหนด DHL:** ห้ามส่งแบตเตอรี่หรือพาวเวอร์แบงค์เด็ดขาด!")
                
        if is_oil_liquid:
            st.info("🛢️ **ข้อกำหนดของเหลว:** ต้องแนบเอกสาร MSDS ให้ทางเอเย่นต์ตรวจสอบก่อนจัดส่ง")
            
        if (is_dhl_prohibited or is_oil_liquid) and (selected_agent == "DHL" or selected_agent == "ทั้งหมด"):
            st.error("🚨 **ประกาศ DHL ห้ามส่ง:** สินค้าประเภทอาหาร (สด/แห้ง/บะหมี่) เครื่องสำอาง อาหารเสริม ยา และของเหลว ไม่อนุญาตผ่าน DHL ตามประกาศ")
            
        st.markdown("---")
        st.dataframe(display_df, use_container_width=True)
    else:
        st.error(f"❌ ไม่อนุญาตให้ส่ง '{selected_item}' ผ่านเอเย่นต์ '{selected_agent}' เนื่องจากติดเงื่อนไขข้อห้ามแบบเด็ดขาด")
