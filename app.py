import streamlit as st
import pandas as pd

st.set_page_config(page_title="FastShip Check", layout="wide")
st.title("📦 FastShip Check")
st.subheader("ระบบวิเคราะห์เงื่อนไขการส่งออกอัจฉริยะ")

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
    "Canada", "UK", "France", "Germany", "Italy", "Spain", "Netherlands"
]

db_countries = [str(x) for x in df['Country'].unique() if str(x) not in ['-', 'nan', '0', '']]
all_countries = sorted(list(set(extra_countries + db_countries)))
countries = ["- กรุณาเลือกประเทศ -"] + all_countries

agents = ["ทั้งหมด", "UPS", "FedEx", "Aramex", "EMS World / Epacket 2kg", "All In"]

# ==========================================
# 2. หน้าจอค้นหา (เปลี่ยนเป็นช่องพิมพ์ข้อความอิสระ เพื่อความยืดหยุ่นสูงสุด)
# ==========================================
col1, col2 = st.columns(2)

with col1:
    target_country = st.selectbox("🌍 ประเทศปลายทาง", options=countries)
    selected_agent = st.selectbox("🚚 เอเย่นต์ (Agent)", options=agents)

with col2:
    # ใช้ Text Input พิมพ์ชื่อสินค้าได้อิสระ ไม่จำกัดเฉพาะใน Dropdown
    selected_item = st.text_input("📦 พิมพ์ชื่อสินค้าที่ต้องการตรวจสอบ (เช่น เสื้อผ้า, พัดลม มีแบต, กระเป๋า)", "")

# ==========================================
# 3. ระบบ AI วิเคราะห์เงื่อนไขและกฎข้อบังคับ
# ==========================================
if target_country != "- กรุณาเลือกประเทศ -" and selected_item.strip() != "":
    
    item_column = 'Example Items' if 'Example Items' in df.columns else 'Product Category'
    
    # ค้นหาแบบยืดหยุ่น (Partial match ในฐานข้อมูล)
    item_df = df[df[item_column].astype(str).str.contains(selected_item, case=False, na=False)]
    
    # ถ้าในตารางหลักไม่เจอ ให้สร้างแถวจำลองสำหรับวิเคราะห์ตามกฎเกณฑ์สากลทันที
    if len(item_df) == 0:
        # สร้าง Dataframe จำลองเพื่อให้ระบบกฎทำงานต่อได้
        item_df = pd.DataFrame([{
            item_column: selected_item,
            'Country': target_country,
            'UPS': 'Acceptable',
            'FedEx': 'Acceptable',
            'Aramex': 'Acceptable',
            'EMS World / Epacket 2kg': 'Acceptable',
            'Condition': 'วิเคราะห์ตามกฎข้อบังคับทั่วไปของระบบ'
        }])

    country_specific = item_df[item_df['Country'].astype(str).str.upper() == target_country.upper()]
    
    if len(country_specific) > 0:
        working_df = country_specific.copy()
        status_msg = f"📌 วิเคราะห์ตามเงื่อนไขเฉพาะของประเทศ **{target_country}**"
    else:
        working_df = item_df.head(1).copy() 
        status_msg = f"🌍 วิเคราะห์ตามมาตรฐานเอเย่นต์ (ไม่มีข้อห้ามเฉพาะจากประเทศ {target_country})"
    
    working_df['All In'] = 'Acceptable'
    
    item_lower = selected_item.lower()
    country_upper = target_country.upper()
    
    # กฎ 1: สินค้าก๊อปแบรนด์ (ห้ามส่งทุกเอเย่นต์ ยกเว้น All In)
    is_fake_brand = any(kw in item_lower for kw in ['ก๊อป', 'ปลอม', 'mirror', 'Brand Name ปลอม', 'เกรดเอ', 'มิลเลอร์', 'แบรนด์ปลอม'])
    
    # กฎ 2: เสื้อผ้ามือสองเฉพาะญี่ปุ่น (มือหนึ่งได้ มือสองห้าม)
    is_secondhand_clothing = ('เสื้อ' in item_lower or 'ผ้า' in item_lower or 'กางเกง' in item_lower or 'ชุด' in item_lower) and ('มือ 2' in item_lower or 'มือสอง' in item_lower or 'มือสอง' in item_lower)
    is_japan_secondhand = (country_upper == 'JAPAN' and is_secondhand_clothing)
    
    # กฎ 3: แบตเตอรี่ UPS (ไม่เกิน 2 ชิ้น)
    is_battery_item = any(kw in item_lower for kw in ['แบต', 'ถ่าน', 'พัดลม มีแบต'])
    
    for col in ["UPS", "FedEx", "Aramex", "EMS World / Epacket 2kg"]:
        if col in working_df.columns:
            if is_fake_brand or is_japan_secondhand:
                working_df[col] = 'Unacceptable'
            elif is_battery_item and col == 'UPS':
                working_df['UPS'] = 'Acceptable'

    if selected_agent != "ทั้งหมด" and selected_agent in working_df.columns:
        if not (selected_agent == 'All In'):
            working_df = working_df[~working_df[selected_agent].astype(str).str.upper().isin(['-', 'X', 'NAN', ''])]
        
    if len(working_df) > 0 and not (is_fake_brand and selected_agent != 'All In' and selected_agent != 'ทั้งหมด'):
        if is_fake_brand:
            st.error("❌ สินค้าละเมิดลิขสิทธิ์ / สินค้าก๊อปแบรนด์ ไม่อนุญาตให้จัดส่งผ่านเอเย่นต์ขนส่งปกติเด็ดขาด!")
        elif is_japan_secondhand:
            st.error("❌ ประเทศญี่ปุ่นไม่อนุญาตให้ส่งเสื้อผ้ามือสองผ่านเอเย่นต์ขนส่งปกติ (อนุญาตเฉพาะมือหนึ่งเท่านั้น)")
        else:
            st.success(f"✅ สามารถส่ง **{selected_item}** ไปยัง **{target_country}** ได้!")
            
        st.info(status_msg)
        
        if is_battery_item:
            st.warning("⚡ **กฎเหล็กสินค้ามีแบตเตอรี่/ถ่าน (ผ่าน UPS):** อนุญาตให้จัดส่งได้ **ไม่เกิน 2 ชิ้นต่อ 1 ชิปเมนต์ (กล่อง)** (ห้ามส่ง Power Bank เด็ดขาด)")
        if is_fake_brand:
            st.warning("🚨 **แจ้งเตือน:** สินค้าก๊อปแบรนด์/ละเมิดลิขสิทธิ์ ส่งได้เฉพาะเอเย่นต์ **All In** เท่านั้น เอเย่นต์หลัก (UPS, FedEx, ฯลฯ) ปฏิเสธการรับ")
        if is_japan_secondhand:
            st.warning("🚨 **แจ้งเตือน:** ญี่ปุ่นอนุญาตเฉพาะเสื้อผ้ามือหนึ่งเท่านั้น เสื้อผ้ามือสองห้ามส่งผ่านขนส่งปกติ")

        st.markdown("### 🤖 สรุปผลการจัดส่ง:")
        first_row = working_df.iloc[0]
        
        available_agents = []
        for a in ["UPS", "FedEx", "Aramex", "EMS World / Epacket 2kg", "All In"]:
            if a in working_df.columns:
                val = str(first_row.get(a, '-')).strip().upper()
                
                if is_fake_brand and a != 'All In':
                    val = 'UNACCEPTABLE'
                elif is_japan_secondhand and a != 'All In':
                    val = 'UNACCEPTABLE'
                elif a == 'UPS' and is_battery_item:
                    val = 'ACCEPTABLE'
                elif a == 'All In':
                    val = 'ACCEPTABLE'
                
                if val not in ['-', 'X', 'NAN', 'UNACCEPTABLE', '']:
                    available_agents.append(a)
                    
        if available_agents:
            st.write(f"**🚚 เอเย่นต์ที่พร้อมให้บริการ:** {', '.join(available_agents)}")
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
            st.warning("สาเหตุ: สินค้าก๊อปแบรนด์/ละเมิดลิขสิทธิ์ไม่อนุญาตให้ส่งออกผ่านเอเย่นต์มาตรฐาน")
        elif is_japan_secondhand:
            st.warning("สาเหตุ: ญี่ปุ่นไม่อนุญาตให้นำเข้าเสื้อผ้ามือสอง")
        else:
            st.warning("สาเหตุ: เอเย่นต์ปฏิเสธการรับส่งสินค้านี้ตามเงื่อนไข")
        
elif target_country == "- กรุณาเลือกประเทศ -" or selected_item.strip() == "":
    st.info("👆 กรุณาเลือก 'ประเทศปลายทาง' และ 'พิมพ์ชื่อสินค้า' ให้ครบถ้วนเพื่อเริ่มตรวจสอบ")