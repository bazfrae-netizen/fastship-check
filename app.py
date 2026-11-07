import streamlit as st
import pandas as pd
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
st.subheader("ระบบตรวจสอบเงื่อนไขการส่งออกอัจฉริยะ 📸")

@st.cache_data
def load_data():
    try:
        df = pd.read_csv("master_database.csv")
        return df.fillna("-")
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการโหลดข้อมูล: {e}")
        return pd.DataFrame()

df = load_data()

# ==========================================
# 1. จัดเตรียมข้อมูลจาก CSV (โครงสร้างใหม่)
# ==========================================
# ดึงรายชื่อประเทศ
db_countries = []
if not df.empty and 'Country' in df.columns:
    db_countries = [str(x).strip() for x in df['Country'].unique() if str(x).strip() not in ['-', 'nan', 'All', '']]

extra_countries = [
    "Australia", "Austria", "Bangladesh", "Belgium", "Canada", "China", 
    "France", "Germany", "Hong Kong", "India", "Indonesia", "Italy", "Japan", 
    "Malaysia", "Philippines", "Singapore", "South Korea", "Taiwan", "UK", "USA", "Vietnam"
]

all_countries = sorted(list(set(extra_countries + db_countries)))
countries = ["- กรุณาเลือกประเทศ -"] + all_countries

# ดึงรายการสินค้าหลักจากคอลัมน์ Keyword
items_list = []
if not df.empty and 'Keyword' in df.columns:
    items_list = sorted([str(x).strip() for x in df['Keyword'].unique() if str(x).strip() not in ['-', 'nan', '']])

agents = ["ทั้งหมด", "UPS", "FedEx", "Aramex", "EMS World / Epacket 2kg", "All In"]

# ==========================================
# 2. หน้าจอเลือกประเทศ เอเย่นต์ และโหมดตรวจสอบ
# ==========================================
col1, col2 = st.columns(2)
with col1:
    target_country = st.selectbox("🌍 เลือกประเทศปลายทาง", options=countries)
with col2:
    selected_agent = st.selectbox("🚚 เลือกเอเย่นต์ (Agent)", options=agents)

st.markdown("---")
check_mode = st.radio("🛠️ เลือกวิธีการตรวจสอบสินค้า:", ["🔍 ค้นหาจากรายชื่อสินค้า", "📸 ถ่ายรูป/อัปโหลดรูปภาพ (AI วิเคราะห์)"])

selected_item = "- กรุณาเลือกสินค้า -"
search_keyword = ""

if check_mode == "🔍 ค้นหาจากรายชื่อสินค้า":
    st.markdown("##### 📦 ค้นหาและเลือกรายการสินค้า")
    search_keyword = st.text_input("🔍 พิมพ์ค้นหาชื่อสินค้า (เช่น เสื้อผ้า, ของเหลว):", placeholder="พิมพ์คำค้นหาที่นี่...")
    
    filtered_options = items_list
    if search_keyword.strip() != "" and not df.empty:
        # ค้นหาจากทั้ง Keyword และ Aliases
        mask_kw = df['Keyword'].astype(str).str.contains(search_keyword.strip(), case=False, na=False) if 'Keyword' in df.columns else False
        mask_al = df['Aliases'].astype(str).str.contains(search_keyword.strip(), case=False, na=False) if 'Aliases' in df.columns else False
        matched_df = df[mask_kw | mask_al]
        
        if not matched_df.empty and 'Keyword' in matched_df.columns:
            filtered_options = sorted(list(set(matched_df['Keyword'].astype(str).tolist())))
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
        
        # สมมติผลลัพธ์จาก AI เป็น "เสื้อผ้า" เป็นค่าเริ่มต้น
        default_guess = "เสื้อผ้า" 
        detected_tag = st.text_input("🤖 AI ตรวจจับประเภทสินค้า (แก้ไขได้):", default_guess)
        
        # จับคู่คำที่ AI ตรวจได้กับ Keyword หรือ Aliases ในระบบ
        matched_item = "- กรุณาเลือกสินค้า -"
        if not df.empty:
            mask_kw = df['Keyword'].astype(str).str.contains(detected_tag.strip(), case=False, na=False) if 'Keyword' in df.columns else False
            mask_al = df['Aliases'].astype(str).str.contains(detected_tag.strip(), case=False, na=False) if 'Aliases' in df.columns else False
            matched_df = df[mask_kw | mask_al]
            
            if not matched_df.empty and 'Keyword' in matched_df.columns:
                matched_item = str(matched_df['Keyword'].iloc[0])
        
        selected_item = matched_item if matched_item != "- กรุณาเลือกสินค้า -" else detected_tag
        if matched_item != "- กรุณาเลือกสินค้า -":
            st.success(f"✔️ จับคู่กับหมวดหมู่ในระบบ: **{selected_item}**")
        else:
            st.warning(f"⚠️ ไม่พบหมวดหมู่ที่ตรงกับ '{detected_tag}' ในระบบ จะใช้การวิเคราะห์แบบทั่วไป")

# ==========================================
# 3. วิเคราะห์เงื่อนไขจากโครงสร้าง CSV ใหม่
# ==========================================
if target_country != "- กรุณาเลือกประเทศ -" and selected_item != "- กรุณาเลือกสินค้า -":
    st.markdown("---")
    st.markdown("### 📊 ผลการตรวจสอบเงื่อนไข")
    
    working_df = pd.DataFrame()
    if not df.empty and 'Keyword' in df.columns:
        working_df = df[df['Keyword'].astype(str) == selected_item].copy()
    
    is_fake_brand = any(kw in selected_item.lower() for kw in ['ก๊อป', 'brand fake', 'ปลอม', 'replica'])
    is_second_hand = any(kw in selected_item.lower() for kw in ['มือสอง', 'second hand', 'used'])
    is_clothing = any(kw in selected_item.lower() for kw in ['เสื้อผ้า', 'clothing', 'apparel'])
    
    is_japan_rule = (target_country.upper() == 'JAPAN' and is_second_hand)

    if not working_df.empty:
        item_info = working_df.iloc[0]
        level = str(item_info.get('Restriction_Level', '')).strip().lower()
        note = str(item_info.get('Note', '')).strip()
        
        # เงื่อนไขละเมิดลิขสิทธิ์
        if level == 'danger' or is_fake_brand:
            st.error(f"❌ **สินค้านี้จัดอยู่ในกลุ่มห้ามส่ง (Prohibited / Danger)**")
            if note and note != '-': st.write(f"📝 **รายละเอียด:** {note}")
            st.warning("🚨 ไม่อนุญาตให้จัดส่งผ่านเอเย่นต์ปกติเด็ดขาด (อาจส่งได้เฉพาะช่องทางพิเศษ All In เท่านั้น)")
        
        # เงื่อนไขเสื้อผ้ามือสองญี่ปุ่น
        elif is_japan_rule:
            st.error("❌ **ประเทศญี่ปุ่นไม่อนุญาตให้นำเข้า 'เสื้อผ้ามือสอง' ผ่านเอเย่นต์ขนส่งปกติ**")
            st.warning("แนะนำ: จัดส่งผ่านช่องทางพิเศษ All In หรือตรวจสอบข้อจำกัดในการทำความสะอาดตามกฎของญี่ปุ่น")
            
        # เงื่อนไขสินค้าต้องเฝ้าระวัง (Warning / ของเหลว / แบตเตอรี่)
        elif level == 'warning':
            st.warning(f"⚠️ **สินค้านี้จัดอยู่ในกลุ่มต้องเฝ้าระวัง (Warning / Restricted)**")
            if note and note != '-': st.write(f"📝 **คำแนะนำ:** {note}")
            
            if 'msds' in note.lower() or any(kw in selected_item.lower() for kw in ['liquid', 'oil', 'ของเหลว']):
                st.info("🛢️ จำเป็นต้องแนบเอกสาร **MSDS (Material Safety Data Sheet)** ให้เอเย่นต์ตรวจสอบก่อนจัดส่ง")
            if 'battery' in note.lower() or 'แบต' in selected_item.lower():
                st.info("⚡ หากส่งผ่าน UPS อนุญาตให้จัดส่งได้ **ไม่เกิน 2 ชิ้นต่อ 1 กล่อง** (ห้ามส่ง Power Bank เด็ดขาด)")
                
            st.success(f"✅ สามารถจัดส่งไปยัง **{target_country}** ได้ (หากปฏิบัติตามเงื่อนไขด้านบน)")
            
        # สินค้าปกติ (Allowed)
        else:
            st.success(f"✅ สามารถจัดส่ง **{selected_item}** ไปยัง **{target_country}** ได้ตามปกติ!")
            if note and note != '-': st.write(f"📝 **หมายเหตุ:** {note}")
            
        # ตารางข้อมูลอ้างอิง
        st.markdown("---")
        st.write("**📄 ข้อมูลอ้างอิงจากฐานข้อมูล (Reference):**")
        st.dataframe(working_df[['Keyword', 'Category', 'Restriction_Level', 'Country', 'Note']], use_container_width=True)
        
    else:
        # กรณีพิมพ์ชื่อสินค้าเองแล้วไม่เจอในฐานข้อมูล
        st.warning(f"⚠️ ไม่พบกฎเฉพาะเจาะจงสำหรับ '{selected_item}' ในฐานข้อมูล")
        if is_fake_brand:
            st.error("❌ สินค้าละเมิดลิขสิทธิ์ / ของก๊อป ไม่อนุญาตให้จัดส่งผ่านเอเย่นต์ปกติ")
        elif is_japan_rule:
            st.error("❌ ประเทศญี่ปุ่นไม่อนุญาตให้นำเข้าเสื้อผ้ามือสองผ่านเอเย่นต์ปกติ")
        else:
            st.info(f"✅ เบื้องต้นคาดว่าสามารถจัดส่งไปยัง **{target_country}** ได้ โปรดตรวจสอบกฎระเบียบสากลเพิ่มเติม")
            
elif target_country == "- กรุณาเลือกประเทศ -" or selected_item == "- กรุณาเลือกสินค้า -":
    st.info("👆 กรุณาเลือก 'ประเทศปลายทาง' และ 'รายการสินค้า' ให้ครบถ้วนเพื่อเริ่มตรวจสอบ")
