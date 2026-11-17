"""FastShip Check — Gemini free-tier assisted review (not shipping authorization)."""
import hashlib
import io
import json
import os
import re
import time
from difflib import SequenceMatcher

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

st.set_page_config(page_title="FastShip Check | Free", page_icon="📦", layout="wide")
st.markdown('''<style>h1,h2,h3{color:#ff6600!important}div.stButton>button:first-child{background:#ff6600;color:white;border:0;border-radius:8px}.stAlert{border-radius:8px}</style>''', unsafe_allow_html=True)
st.title("📦 FastShip Check")
st.caption("ตรวจสอบเงื่อนไขการส่งออก • Gemini Free Tier • ต้องให้พนักงานยืนยันผลก่อนจัดส่ง")

DB_PATH = "master_database.csv"
AGENTS = ["UPS", "FedEx", "DHL", "Aramex", "EMS World / Epacket 2kg", "All In"]
UNKNOWN = "ต้องตรวจสอบเพิ่มเติม"


def norm(v):
    return re.sub(r"\s+", " ", str(v).strip()).casefold()


@st.cache_data(show_spinner=False)
def load_data(path, modified):
    errors = []
    for kwargs in ({"encoding": "utf-8-sig"}, {"encoding": "utf-8"}, {"encoding": "cp874"}):
        try:
            frame = pd.read_csv(path, dtype=str, keep_default_na=False, **kwargs)
            frame.columns = frame.columns.str.strip()
            if not {"Example Items", "Country"}.issubset(frame.columns):
                return pd.DataFrame(), "CSV ต้องมีคอลัมน์ Example Items และ Country"
            if not any(c in frame.columns for c in AGENTS):
                return pd.DataFrame(), "CSV ไม่พบคอลัมน์บริษัทขนส่งที่รองรับ"
            return frame.fillna(""), ""
        except Exception as e:
            errors.append(str(e))
    return pd.DataFrame(), "ไม่สามารถอ่าน CSV ได้: " + errors[-1]


if not os.path.isfile(DB_PATH):
    st.error("ไม่พบ master_database.csv กรุณาวางไฟล์ในโฟลเดอร์เดียวกับ app.py")
    st.stop()

df, db_error = load_data(DB_PATH, os.path.getmtime(DB_PATH))
if db_error or df.empty:
    st.error(db_error or "ฐานข้อมูลว่าง")
    st.stop()

item_names = sorted({str(x).strip() for x in df["Example Items"] if norm(x) not in {"", "-", "none", "nan", "0"}})
country_names = sorted({str(x).strip() for x in df["Country"] if norm(x) not in {"", "-", "all", "*", "ทุกประเทศ"}})
if not item_names:
    st.error("ฐานข้อมูลไม่มีชื่อสินค้า")
    st.stop()


def get_secret(name, default=""):
    try:
        return st.secrets.get(name, os.environ.get(name, default))
    except Exception:
        return os.environ.get(name, default)


def image_bytes(upload):
    image = Image.open(upload)
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((640, 640))
    output = io.BytesIO()
    image.save(output, "JPEG", quality=70, optimize=True)
    return output.getvalue(), image


def parse_ai(text):
    text = text.strip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.S)
        if not match:
            raise ValueError("AI ไม่ได้ตอบกลับเป็น JSON")
        obj = json.loads(match.group())
    if not isinstance(obj, dict):
        raise ValueError("รูปแบบผล AI ไม่ถูกต้อง")
    name = str(obj.get("item_name", "")).strip()[:100]
    category = str(obj.get("category", "")).strip()[:80]
    uncertain = obj.get("uncertain", True)
    if not isinstance(uncertain, bool):
        uncertain = True
    if not name:
        raise ValueError("AI ไม่สามารถระบุชื่อสินค้า")
    return {"item_name": name, "category": category, "uncertain": uncertain}


def analyze_photo(jpeg):
    from google import genai
    from google.genai import types
    key = get_secret("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("ยังไม่ได้ตั้งค่า GEMINI_API_KEY ใน Streamlit Secrets")
    model = get_secret("GEMINI_MODEL", "gemini-3.5-flash-lite")
    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=20000))
    prompt = (
        "ดูภาพสินค้าและตอบ JSON object เท่านั้น โดยมี key item_name (ชื่อสินค้าไทยสั้นๆ), "
        "category (หมวดหมู่สั้นๆ), uncertain (boolean). "
        "ถ้าไม่แน่ใจให้ uncertain=true ห้ามเดายี่ห้อ ส่วนผสม สภาพมือสอง แบตเตอรี่ หรือความถูกต้องตามกฎหมายจากภาพ "
        "ห้ามตัดสินว่าส่งออกได้หรือไม่ได้ ตัวอย่าง: "
        '{"item_name":"ขวดโลชั่น","category":"เครื่องสำอาง","uncertain":true}'
    )
    result = client.models.generate_content(
        model=model,
        contents=[prompt, types.Part.from_bytes(data=jpeg, mime_type="image/jpeg")],
        config=types.GenerateContentConfig(temperature=0, max_output_tokens=150, response_mime_type="application/json"),
    )
    return parse_ai(result.text or "")


def suggestions(label, names, limit=12):
    query = norm(label)
    if not query:
        return []
    scored = []
    for name in names:
        key = norm(name)
        score = SequenceMatcher(None, query, key).ratio()
        if query in key or key in query:
            score += 0.6
        if score >= 0.40:
            scored.append((score, name))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [name for _, name in scored[:limit]]


def interpret_status(value):
    v = norm(value)
    if v in {"acceptable", "accept", "allowed", "yes", "อนุญาต", "ส่งได้"}:
        return "ACCEPTABLE"
    if v in {"unacceptable", "prohibited", "not allowed", "no", "ห้ามส่ง", "ส่งไม่ได้"}:
        return "UNACCEPTABLE"
    if "msds" in v or "document" in v or "เอกสาร" in v:
        return "DOCUMENT"
    return "UNKNOWN"


def is_food_item(frame_rows, item_name):
    food_keywords = ["food", "อาหาร", "บะหมี่", "มาม่า", "ขนม", "ของกิน", "เครื่องดื่ม", "น้ำพริก", "กะปิ", "กุนเชียง", "อาหารเสริม", "วิตามิน"]
    if any(k in norm(item_name) for k in food_keywords):
        return True
    if not frame_rows.empty and "Product Category" in frame_rows.columns:
        cats = " ".join(frame_rows["Product Category"].map(norm).tolist())
        if any(k in cats for k in food_keywords):
            return True
    return False


def check_dhl_prohibited(frame_rows, item_name):
    text_to_check = norm(item_name)
    if not frame_rows.empty and "Product Category" in frame_rows.columns:
        text_to_check += " " + " ".join(frame_rows["Product Category"].map(norm).tolist())

    dhl_rules = [
        (["อาหารสด", "อาหารที่มีน้ำ", "น้ำซุป", "ของเหลว", "เครื่องดื่ม", "ซอส", "น้ำจิ้ม", "น้ำพริก", "กะปิ", "แกง"], "อาหารสด และอาหารที่มีน้ำเป็นส่วนประกอบ"),
        (["เพชร", "พลอย", "ทอง", "ทองแท่ง", "เครื่องเงิน", "อัญมณี", "จิวเวลรี่", "ของมีค่า"], "เพชร พลอยมีค่า ทองแท่ง เครื่องเงิน และของมีค่า"),
        (["สารเคมี", "เคมี", "น้ำยา", "ทินเนอร์", "แอลกอฮอล์", "กรด", "ด่าง"], "สารเคมีทุกชนิด"),
        (["ละเมิดลิขสิทธิ์", "ปลอม", "เลียนแบบ", "ก๊อป", "mirror", "เกรดเอ", "แบรนด์เนม"], "สินค้าละเมิดลิขสิทธิ์ ของปลอม หรือสินค้าเลียนแบบ"),
        (["ผลิตภัณฑ์จากสัตว์", "สัตว์ที่มีชีวิต", "สัตว์", "เนื้อสัตว์", "หนังสัตว์", "งาช้าง", "รังนก", "น้ำผึ้ง"], "ผลิตภัณฑ์จากสัตว์และสัตว์ที่มีชีวิต"),
        (["แบต", "แบตเตอรี่", "ลิเธียม", "ถ่าน", "power bank", "พาวเวอร์แบงค์", "สารมีพิษ", "วัตถุอันตราย"], "แบตเตอรี่ลิเธียม พาวเวอร์แบงค์ และสารมีพิษ"),
        (["ดวงตราไปรษณียากร", "แสตมป์", "stamp"], "ดวงตราไปรษณียากร (แสตมป์)"),
        (["ยา", "สิ่งเสพติด", "ยาเสพติด", "กัญชา", "กัญชง", "กระท่อม", "ฝิ่น"], "ยาที่ผิดกฎหมาย และสิ่งเสพติดทุกชนิด"),
        (["เงินสด", "ธนบัตร", "เช็ค", "เหรียญกษาปณ์"], "เงินสดและสิ่งเทียบเท่า ทั้งธนบัตรและเช็ค"),
        (["อาวุธ", "ปืน", "กระสุน", "ระเบิด", "มีด", "ดาบ"], "อาวุธทุกชนิด รวมทั้งปืนและกระสุนปืน"),
        (["ชิ้นส่วนมนุษย์", "กระดูก", "เถ้ากระดูก", "อัฐิ", "เส้นผม"], "ชิ้นส่วนมนุษย์ รวมถึงกระดูก"),
        (["สเปรย์", "น้ำหอม", "โคโลญจน์", "perfume", "spray"], "สเปรย์ น้ำหอม โคโลญจน์"),
        (["เครื่องสำอาง", "สกินแคร์", "ความงาม", "ครีม", "เซรั่ม", "โลชั่น", "ลิปสติก", "แป้งพัฟ", "สบู่"], "เครื่องสำอาง สกินแคร์ และผลิตภัณฑ์เพื่อความงาม"),
        (["อาหารเสริม", "วิตามิน", "คอลลาเจน", "โปรตีน", "สมุนไพร"], "อาหารเสริม วิตามิน และผลิตภัณฑ์เสริมอาหาร"),
    ]
    for keywords, rule_desc in dhl_rules:
        if any(k in text_to_check for k in keywords):
            return True, rule_desc
    return False, ""


def review(frame, item, country, agent):
    exact = frame[frame["Example Items"].map(norm) == norm(item)]
    if exact.empty:
        if agent == "DHL":
            is_prohibited, rule_desc = check_dhl_prohibited(pd.DataFrame(), item)
            if is_prohibited:
                return "UNACCEPTABLE", pd.DataFrame(), f"ประกาศ DHL ห้ามส่ง: {rule_desc}"
            return "ACCEPTABLE", pd.DataFrame(), "ไม่อยู่ในรายการห้ามส่งของ DHL — สามารถจัดส่งได้"
        return "UNKNOWN", pd.DataFrame(), "ไม่พบรายการสินค้านี้ในฐานข้อมูล"

    relevant = exact[exact["Country"].map(norm) == norm(country)]
    if relevant.empty:
        relevant = exact[exact["Country"].map(norm).isin({"all", "*", "ทุกประเทศ"})]

    # กฎเฉพาะของ DHL ตามใบประกาศ
    if agent == "DHL":
        is_prohibited, rule_desc = check_dhl_prohibited(relevant if not relevant.empty else exact, item)
        if is_prohibited:
            return "UNACCEPTABLE", relevant if not relevant.empty else exact.head(1), f"ประกาศ DHL ห้ามส่ง: {rule_desc}"
        if not relevant.empty and "DHL" in relevant.columns:
            states = [interpret_status(v) for v in relevant["DHL"]]
            if "UNACCEPTABLE" in states:
                return "UNACCEPTABLE", relevant, "ฐานข้อมูลระบุว่า DHL ไม่อนุญาตให้ส่งสินค้านี้ไปยังประเทศปลายทาง"
        return "ACCEPTABLE", relevant if not relevant.empty else exact.head(1), "ไม่อยู่ในรายการห้ามส่งของ DHL — สามารถจัดส่งได้"

    if relevant.empty:
        if agent == "All In" and is_food_item(exact, item):
            return "ACCEPTABLE", exact.head(1), "ช่องทาง All In รองรับการจัดส่งสินค้าประเภทอาหาร/ของกินทั้งหมด"
        return "UNKNOWN", pd.DataFrame(), "ไม่พบเงื่อนไขสำหรับประเทศที่เลือก (ไม่ใช้ข้อมูลประเทศอื่นแทน)"

    if agent not in relevant.columns:
        if agent == "All In" and is_food_item(relevant, item):
            return "ACCEPTABLE", relevant, "ช่องทาง All In รองรับการจัดส่งสินค้าประเภทอาหาร/ของกินทั้งหมด"
        return "UNKNOWN", relevant, "ไม่มีคอลัมน์เอเย่นต์นี้ในฐานข้อมูล"

    states = [interpret_status(v) for v in relevant[agent]]
    if "UNACCEPTABLE" in states:
        return "UNACCEPTABLE", relevant, "มีแถวที่ระบุห้ามส่ง"
    if "UNKNOWN" in states:
        return "UNKNOWN", relevant, "มีข้อมูลว่างหรือสถานะที่ระบบยังไม่รู้จัก"
    if "DOCUMENT" in states:
        return "DOCUMENT", relevant, "มีเงื่อนไขต้องตรวจเอกสาร"
    if states and all(s == "ACCEPTABLE" for s in states):
        return "ACCEPTABLE", relevant, "ข้อมูลทุกแถวที่เกี่ยวข้องระบุ Acceptable"
    return "UNKNOWN", relevant, "ยังไม่สามารถสรุปผลได้"


left, right = st.columns(2)
with left:
    country = st.selectbox("🌍 ประเทศปลายทาง", ["- เลือกประเทศ -"] + country_names)
with right:
    agent = st.selectbox("🚚 เอเย่นต์ (Agent)", ["- เลือกเอเย่นต์ -"] + AGENTS)

mode = st.radio("🛠️ วิธีตรวจสอบสินค้า", ["🔍 ค้นหาสินค้า", "📸 ถ่ายภาพ/อัปโหลดภาพ (AI ฟรี)"], horizontal=True)
selected = None
if mode.startswith("🔍"):
    selected = st.selectbox("📋 เลือกรายการสินค้า", ["- เลือกสินค้า -"] + item_names)
    if selected.startswith("- เลือก"):
        selected = None
else:
    c1, c2 = st.columns(2)
    with c1:
        camera = st.camera_input("ถ่ายภาพสินค้า", key="camera")
    with c2:
        upload = st.file_uploader("หรืออัปโหลดภาพ", type=["jpg", "jpeg", "png"], key="upload")
    active = upload if upload is not None else camera
    if active is not None:
        try:
            jpeg, preview = image_bytes(active)
            st.image(preview, caption="ภาพที่เลือก", width=260)
            digest = hashlib.sha256(jpeg).hexdigest()
            if st.session_state.get("photo_hash") != digest:
                st.session_state.photo_hash = digest
                st.session_state.photo_result = None
                st.session_state.photo_error = None
                st.session_state.photo_seconds = None
                if get_secret("GEMINI_API_KEY"):
                    with st.spinner("🤖 กำลังวิเคราะห์ภาพใหม่โดยอัตโนมัติ..."):
                        start = time.perf_counter()
                        try:
                            st.session_state.photo_result = analyze_photo(jpeg)
                        except Exception as exc:
                            msg = str(exc)
                            if "429" in msg or "RESOURCE_EXHAUSTED" in msg.upper():
                                msg = "โควตา Gemini ฟรีอาจเต็มหรือเรียกถี่เกินไป กรุณารอแล้วลองใหม่ หรือใช้ค้นหาสินค้าแทน"
                            st.session_state.photo_error = msg
                        st.session_state.photo_seconds = time.perf_counter() - start
                else:
                    st.session_state.photo_error = "ไม่พบ GEMINI_API_KEY ใน Streamlit Secrets"
            if st.session_state.get("photo_error"):
                st.error("วิเคราะห์ภาพไม่สำเร็จ: " + st.session_state.photo_error)
                if st.button("🔄 ลองวิเคราะห์ภาพนี้อีกครั้ง"):
                    st.session_state.photo_hash = None
                    st.rerun()
            result = st.session_state.get("photo_result")
            if result:
                st.success(f"AI เห็น: {result['item_name']} • หมวดหมู่: {result['category'] or 'ไม่ระบุ'}")
                if result["uncertain"]:
                    st.warning("AI ไม่มั่นใจในรายละเอียด กรุณาตรวจสินค้าจริงและฉลาก")
                if st.session_state.get("photo_seconds") is not None:
                    st.caption(f"⏱️ เวลาเรียก AI: {st.session_state.photo_seconds:.2f} วินาที")
                recommended = suggestions(result["item_name"], item_names)
                if result["category"]:
                    recommended += [x for x in suggestions(result["category"], item_names) if x not in recommended]
                recommended = recommended[:15]
                options = ["- เลือกสินค้า -"] + recommended + [x for x in item_names if x not in recommended]
                selected = st.selectbox("📋 พนักงานยืนยันชื่อสินค้าจากฐานข้อมูล", options, key="ai_confirm_item")
                if selected.startswith("- เลือก"):
                    selected = None
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            st.error(f"อ่านภาพไม่สำเร็จ: {exc}")
    else:
        st.info("ถ่ายภาพแล้วระบบจะวิเคราะห์อัตโนมัติ 1 ครั้งต่อภาพใหม่ ภายในโควตา Gemini ฟรี")

if selected and country != "- เลือกประเทศ -" and agent != "- เลือกเอเย่นต์ -":
    st.divider()
    st.subheader("📊 ผลการตรวจสอบเงื่อนไขการจัดส่ง")
    status, matches, reason = review(df, selected, country, agent)
    if status == "UNACCEPTABLE":
        st.error("⛔ ไม่อนุญาตให้ส่งผ่านเอเย่นต์นี้")
    elif status == "DOCUMENT":
        st.warning("📄 ต้องตรวจเอกสาร/เงื่อนไขเพิ่มเติมก่อนตัดสินใจ")
    elif status == "ACCEPTABLE":
        st.success("✅ สามารถจัดส่งได้ (Acceptable) — กรุณาตรวจสภาพจริงและยืนยันก่อนจัดส่ง")
    else:
        st.warning("⚠️ ต้องตรวจสอบเพิ่มเติม — ห้ามสรุปว่าส่งได้จากข้อมูลที่มี")
    st.caption(reason)
    flags = []
    s = norm(selected)
    for keywords, label in [
        (["แบต", "ถ่าน", "power bank", "พาวเวอร์แบงค์"], "แบตเตอรี่/วัตถุอันตราย"),
        (["ของเหลว", "น้ำหอม", "สเปรย์", "เจล", "liquid"], "ของเหลว/อาจต้องใช้ MSDS"),
        (["อาหาร", "ขนม", "วิตามิน", "อาหารเสริม"], "อาหาร/อาหารเสริม"),
        (["มือสอง", "มือ 2", "used", "secondhand"], "สินค้ามือสอง"),
        (["แบรนด์เนม", "ปลอม", "เลียนแบบ", "ก๊อป"], "สินค้ามีแบรนด์/ตรวจสิทธิ์และความแท้"),
    ]:
        if any(k in s for k in keywords):
            flags.append(label)
    if flags:
        st.warning("🔎 ประเด็นที่ควรตรวจเพิ่มเติม: " + ", ".join(flags))
    st.caption("ผลจากระบบเป็นเครื่องมือช่วยตรวจ ไม่ใช่คำอนุญาตส่งออกขั้นสุดท้าย")
    if not matches.empty:
        st.dataframe(matches, use_container_width=True, hide_index=True)
    st.checkbox("ฉันตรวจสอบสินค้าจริงและยืนยันเงื่อนไขกับข้อมูลบริษัทล่าสุดแล้ว", key="manual_verified")
else:
    st.caption("เลือกประเทศ เอเย่นต์ และยืนยันชื่อสินค้าเพื่อดูผลตรวจสอบ")
