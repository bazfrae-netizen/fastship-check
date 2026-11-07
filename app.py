import streamlit as st
import pandas as pd
from PIL import Image

st.set_page_config(page_title="FastShip Check", layout="wide")

# ==========================================
# 🎨 ธีมสีส้ม FastShip (Force CSS)
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
    div.stButton > button:first-child:hover {
        background-color: #E65C00 !important;
        color: white !important;
    }
    .stAlert { border-left-color: #FF6600 !important; }
    .stRadio [data-baseweb="radio"] div[aria-checked="true"] {
        background-color: #FF6600 !important;
        border-color: #FF6600 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 FastShip Check")
st.subheader("ระบบตรวจสอบเงื่อนไขการส่งออก (ใช้เป็น Guideline เท่านั้น)")

# ==========================================
# 0. ค่าคงที่
# ==========================================
DB_AGENTS = ["UPS", "FedEx", "Aramex", "EMS World / Epacket 2kg"]
ALL_AGENTS = DB_AGENTS + ["All In"]

# รหัสประเทศในไฟล์ Excel -> ชื่อประเทศที่ใช้ในแอป
COUNTRY_CODES = {
    "AUS": "Australia", "AUT": "Austria", "BGD": "Bangladesh", "BEL": "Belgium",
    "CHN": "China", "CAN": "Canada", "CHL": "Chile", "HRV": "Croatia",
    "CZE": "Czech Republic", "DNK": "Denmark", "EGY": "Egypt", "FIN": "Finland",
    "FRA": "France", "GER": "Germany", "DEU": "Germany", "GRC": "Greece",
    "HKG": "Hong Kong", "HUN": "Hungary", "ITA": "Italy", "IND": "India",
    "IDN": "Indonesia", "ISL": "Iceland", "IRL": "Ireland", "ISR": "Israel",
    "JPN": "Japan", "MYS": "Malaysia", "MAC": "Macao", "MEX": "Mexico",
    "MLT": "Malta", "NLD": "Netherlands", "KWT": "Kuwait", "NOR": "Norway",
    "NZL": "New Zealand", "OMN": "Oman", "PHL": "Philippines", "PAK": "Pakistan",
    "POL": "Poland", "PRI": "Puerto Rico", "QAT": "Qatar", "SGP": "Singapore",
    "ZAF": "South Africa", "KOR": "South Korea", "ESP": "Spain", "CHE": "Switzerland",
    "SWE": "Sweden", "SAU": "Saudi Arabia", "TWN": "Taiwan", "GBR": "UK",
    "TUR": "Turkey", "USA": "USA", "ARE": "United Arab Emirates", "VNM": "Vietnam",
}
COUNTRY_ALIASES = {
    "UNITED STATES OF AMERICA": "USA",
    "UNITED STATES": "USA",
    "UNITED KINGDOM": "UK",
}


def norm_country(value):
    s = str(value).strip()
    u = s.upper()
    if u in COUNTRY_CODES:
        return COUNTRY_CODES[u]
    if u in COUNTRY_ALIASES:
        return COUNTRY_ALIASES[u]
    return s


def normalize_status(value):
    s = str(value).strip().upper()
    if s.startswith("UNACCEPT"):
        return "Unacceptable"
    if s.startswith("ACCEPT"):
        return "Acceptable"
    if s in ("", "-", "X", "NAN"):
        return "Unacceptable"
    return "Check"


STATUS_LABEL = {
    "Acceptable": "✅ ส่งได้",
    "Unacceptable": "❌ ส่งไม่ได้",
    "Check MSDS": "⚠️ ส่งได้เมื่อ MSDS ผ่านการอนุมัติ",
    "Check": "⚠️ ต้องดูเงื่อนไขเพิ่มเติม",
    "Unverified": "❓ ไม่มีข้อมูลยืนยัน ต้องสอบถามทีม",
}

# ==========================================
# 1. โหลดข้อมูล
# ==========================================
@st.cache_data
def load_data():
    d = pd.read_csv("master_database.csv", encoding="utf-8-sig").fillna("-")
    country_col = "Country" if "Country" in d.columns else "Country Code"
    d["_country"] = d[country_col].apply(norm_country)
    return d


df = load_data()

extra_countries = [
    "Cambodia", "Laos", "Myanmar", "Vietnam", "Malaysia", "Singapore",
    "Indonesia", "Philippines", "Brunei", "Japan", "South Korea", "China",
    "Taiwan", "Hong Kong", "India", "Australia", "New Zealand", "USA",
    "Canada", "UK", "France", "Germany", "Italy", "Spain", "Netherlands", "Bangladesh",
]
db_countries = [c for c in df["_country"].unique() if c not in ["-", "nan", "0", ""]]
all_countries = sorted(set(extra_countries + db_countries))
countries = ["- กรุณาเลือกประเทศ -"] + all_countries

item_column = "Example Items" if "Example Items" in df.columns else "Product Category"
clean_items = [
    str(x).strip() for x in df[item_column].dropna().unique()
    if str(x).strip() not in ["-", "nan", "0", "", "None"]
]
default_test_items = [
    "เสื้อผ้า", "เสื้อผ้ามือสอง", "รองเท้าผ้าใบ",
    "กระเป๋าแบรนด์เนม", "กระเป๋า ก๊อปแบรนด์", "เสื้อผ้า ก๊อปแบรนด์",
    "พัดลม มีแบต", "แบตเตอรี่สำรอง (Power Bank)",
    "น้ำมันเครื่อง", "ของเหลว / เจล / สเปรย์",
]
items_list = ["- กรุณาเลือกสินค้า -"] + sorted(set(clean_items + default_test_items))
agents = ["ทั้งหมด"] + ALL_AGENTS

# ==========================================
# 2. ตัวตรวจสอบเงื่อนไข
# ==========================================
def has_any(text, keywords):
    return any(k in text for k in keywords)


def evaluate(item, country):
    """คืนค่า (statuses, flags, source, condition, rows)"""
    t = item.lower()
    c = country.upper()

    flags = {
        "fake": has_any(t, ["ก๊อป", "ปลอม", "mirror", "เกรดเอ", "มิลเลอร์", "เลียนแบบ", "เกรด a"]),
        "clothing": has_any(t, ["เสื้อ", "ผ้า", "ชุด", "กางเกง"]),
        "second_hand": has_any(t, ["มือสอง", "มือ 2", "มือ ๒", "secondhand", "used"]),
        "powerbank": has_any(t, ["power bank", "powerbank", "พาวเวอร์แบงค์", "แบตเตอรี่สำรอง", "แบตสำรอง"]),
        "battery": has_any(t, ["แบต", "ถ่าน"]),
        "liquid": has_any(t, ["น้ำมัน", "ของเหลว", "เจล", "สเปรย์", "oil", "liquid"]),
    }
    flags["japan_second_hand"] = (
        c == "JAPAN" and flags["clothing"] and flags["second_hand"]
    )

    # --- ข้อมูลพื้นฐานจากฐานข้อมูล (เฉพาะสินค้า + ประเทศที่เลือกเท่านั้น) ---
    item_df = df[df[item_column].astype(str).str.strip() == item]
    rows = item_df[item_df["_country"].str.upper() == c]

    condition = "-"
    if len(rows) > 0:
        first = rows.iloc[0]
        statuses = {a: normalize_status(first.get(a, "-")) for a in DB_AGENTS}
        condition = str(first.get("Condition", "-")).strip()
        source = "db"
    else:
        statuses = {a: "Unverified" for a in DB_AGENTS}
        source = "no_country" if len(item_df) > 0 else "no_item"
    statuses["All In"] = "Unverified"

    # --- กฎเฉพาะที่ทับข้อมูลพื้นฐาน ---
    if flags["fake"]:
        for a in ALL_AGENTS:
            statuses[a] = "Unacceptable"
    elif flags["japan_second_hand"]:
        for a in DB_AGENTS:
            statuses[a] = "Unacceptable"
    else:
        if flags["powerbank"]:
            for a in DB_AGENTS:
                statuses[a] = "Unacceptable"
        elif flags["battery"] and statuses["UPS"] == "Unverified":
            statuses["UPS"] = "Acceptable"
        if flags["liquid"]:
            for a in ["UPS", "FedEx"]:
                if statuses[a] != "Unacceptable":
                    statuses[a] = "Check MSDS"

    return statuses, flags, source, condition, rows


# ==========================================
# 3. หน้าจอเลือกข้อมูล
# ==========================================
col1, col2 = st.columns(2)
with col1:
    target_country = st.selectbox("🌍 เลือกประเทศปลายทาง", options=countries)
with col2:
    selected_agent = st.selectbox("🚚 เลือกเอเย่นต์ (Agent)", options=agents)

st.markdown("---")
check_mode = st.radio(
    "🛠️ เลือกวิธีการตรวจสอบสินค้า:",
    ["🔍 ค้นหาจากรายชื่อสินค้า", "📸 ถ่ายรูป / อัปโหลดรูปเพื่อดูประกอบ"],
)

if check_mode == "🔍 ค้นหาจากรายชื่อสินค้า":
    selected_item = st.selectbox(
        "📦 รายชื่อสินค้า (คลิกเลือกหรือพิมพ์ค้นหาได้)", options=items_list, key="item_search"
    )
else:
    st.info(
        "💡 ตอนนี้ระบบยังไม่ได้ตรวจจับประเภทสินค้าจากรูปอัตโนมัติ "
        "ให้ถ่าย/อัปโหลดรูปเพื่อดูประกอบ แล้วเลือกประเภทสินค้าด้วยตัวเองด้านล่าง"
    )
    cam1, cam2 = st.columns(2)
    with cam1:
        st.markdown("##### 📸 ถ่ายรูปสดผ่านกล้อง")
        camera_image = st.camera_input("กดปุ่มถ่ายรูปด้านล่าง")
    with cam2:
        st.markdown("##### 📂 หรืออัปโหลดรูปภาพจากเครื่อง")
        uploaded_file = st.file_uploader("เลือกไฟล์รูปภาพ (JPG, PNG)", type=["jpg", "jpeg", "png"])

    active_image = camera_image if camera_image is not None else uploaded_file
    if active_image is not None:
        st.image(Image.open(active_image), caption="📷 ภาพสินค้า", width=300)
    selected_item = st.selectbox(
        "📦 เลือกประเภทสินค้าให้ตรงกับในรูป", options=items_list, key="item_image"
    )

# ==========================================
# 4. แสดงผล
# ==========================================
if target_country == "- กรุณาเลือกประเทศ -" or selected_item == "- กรุณาเลือกสินค้า -":
    st.info("👆 กรุณาเลือก 'ประเทศปลายทาง' และ 'สินค้า' ให้ครบถ้วนเพื่อเริ่มตรวจสอบ")
    st.stop()

statuses, flags, source, condition, rows = evaluate(selected_item, target_country)
view_agents = ALL_AGENTS if selected_agent == "ทั้งหมด" else [selected_agent]

st.markdown("---")
st.markdown("### 📊 ผลการตรวจสอบ")

ok_agents = [a for a in view_agents if statuses[a] in ("Acceptable", "Check MSDS", "Check")]
unverified = [a for a in view_agents if statuses[a] == "Unverified"]

# --- สรุปผลหลัก ---
if flags["fake"]:
    st.error("❌ สินค้าก๊อปแบรนด์ / ละเมิดลิขสิทธิ์ ไม่สามารถจัดส่งได้ทุกช่องทาง")
elif flags["japan_second_hand"]:
    st.error("❌ ญี่ปุ่นไม่อนุญาตให้นำเข้าเสื้อผ้ามือสองผ่านเอเย่นต์ปกติ (มือหนึ่งส่งได้) "
             "หากลูกค้าต้องการส่งจริง ให้สอบถามทีม/หัวหน้างานก่อน")
elif flags["powerbank"]:
    st.error("❌ Power Bank / แบตเตอรี่สำรอง ไม่สามารถจัดส่งผ่านเอเย่นต์ปกติได้")
elif ok_agents:
    st.success(f"✅ **{selected_item}** → **{target_country}** ส่งได้ผ่าน: {', '.join(ok_agents)}")
elif unverified:
    st.warning(f"❓ ไม่มีข้อมูลยืนยันสำหรับ {', '.join(unverified)} กรุณาสอบถามทีมก่อนแจ้งลูกค้า")
else:
    st.error(f"❌ ไม่สามารถส่ง '{selected_item}' ไป {target_country} ผ่าน "
             f"{'เอเย่นต์ที่เลือก' if selected_agent != 'ทั้งหมด' else 'เอเย่นต์ใดได้เลย'}")

# --- แหล่งที่มาของข้อมูล ---
if source == "db":
    st.info(f"📌 ข้อมูลจากฐานข้อมูล: {target_country}")
elif source == "no_country":
    st.warning(f"⚠️ ฐานข้อมูลมี '{selected_item}' แต่ **ไม่มีข้อมูลของ {target_country}** "
               "จึงไม่นำข้อมูลของประเทศอื่นมาใช้ ให้ตรวจสอบกับทีมก่อน")
else:
    st.warning("⚠️ ไม่พบสินค้านี้ในฐานข้อมูล ผลที่เห็นมาจากกฎทั่วไปเท่านั้น ให้ตรวจสอบกับทีมก่อน")

# --- คำเตือนตามประเภทสินค้า ---
if flags["liquid"]:
    st.warning("🛢️ สินค้าประเภทน้ำมัน/ของเหลว/สารเคมี ต้องส่ง **MSDS** ให้เอเย่นต์อนุมัติก่อนจัดส่งทุกครั้ง")
if flags["battery"] and not flags["powerbank"]:
    st.warning("⚡ สินค้าที่มีแบตเตอรี่/ถ่าน ส่งผ่าน UPS ได้ **ไม่เกิน 2 ชิ้นต่อกล่อง**")
if target_country.upper() == "JAPAN" and flags["clothing"] and not flags["second_hand"]:
    st.info("🇯🇵 ญี่ปุ่น: เสื้อผ้ามือหนึ่งส่งได้ปกติ ✅ แต่มือสองส่งผ่านขนส่งปกติไม่ได้ ❌")

# --- ตารางเอเย่นต์ ---
st.markdown("#### 🚚 สถานะรายเอเย่นต์")
st.dataframe(
    pd.DataFrame({
        "เอเย่นต์": view_agents,
        "สถานะ": [STATUS_LABEL[statuses[a]] for a in view_agents],
    }),
    use_container_width=True,
    hide_index=True,
)

if condition not in ("-", "", "nan"):
    st.write(f"**📌 เงื่อนไข / ข้อควรระวัง:** {condition}")

if source == "db":
    with st.expander("ตารางอ้างอิงข้อมูลดิบ (Reference)"):
        st.dataframe(rows.drop(columns=["_country"]), use_container_width=True)

st.caption(
    "ผลนี้ใช้เป็น Guideline เท่านั้น สินค้าทุกชิ้นมีสิทธิ์ถูกสุ่มตรวจจากศุลกากรปลายทาง "
    "และการตรวจปล่อยขึ้นอยู่กับดุลยพินิจของศุลกากร กรุณาพิจารณาปริมาณและความชัดเจนของสินค้าร่วมด้วย"
)
