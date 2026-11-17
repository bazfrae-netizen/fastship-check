"""FastShip Check v3 — image recognition assists humans; CSV is not legal clearance."""
import base64
import hashlib
import io
import json
import os
import time
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps, UnidentifiedImageError

st.set_page_config(page_title="FastShip Check", page_icon="📦", layout="wide")
st.markdown('''<style>h1,h2,h3{color:#ff6600!important}.stButton button[kind="primary"]{background:#ff6600;border-color:#ff6600;color:white}.stButton button[kind="primary"]:hover{background:#e65c00;border-color:#e65c00;color:white}</style>''', unsafe_allow_html=True)
st.title("📦 FastShip Check")
st.caption("ระบบช่วยระบุสินค้าและตรวจสอบเงื่อนไขการส่งออก • ต้องให้เจ้าหน้าที่ตรวจสอบก่อนส่งจริง")

AGENTS = ["UPS", "FedEx", "DHL", "Aramex", "EMS World / Epacket 2kg", "All In"]
COUNTRIES = ["Australia", "Austria", "Bangladesh", "Belgium", "Canada", "Chile", "China", "Croatia", "Czech Republic", "Denmark", "Egypt", "Finland", "France", "Germany", "Greece", "Hong Kong", "Hungary", "Iceland", "India", "Indonesia", "Ireland", "Israel", "Italy", "Japan", "Kuwait", "Macao", "Malaysia", "Malta", "Mexico", "Netherlands", "New Zealand", "Norway", "Oman", "Pakistan", "Philippines", "Poland", "Puerto Rico", "Qatar", "Saudi Arabia", "Singapore", "South Africa", "South Korea", "Spain", "Sweden", "Switzerland", "Taiwan", "Turkey", "United Kingdom", "USA", "United Arab Emirates", "Vietnam"]
ALIASES = {"เสื้อผ้ามือ 2 (สินค้ามือ 2)": "สินค้ามือ 2", "เสื้อผ้าแบรนด์เนม / เสื้อผ้าทั่วไป": "สินค้าแบรนด์เนม (Luxury Brand)"}
PLACEHOLDER = "- กรุณาเลือกสินค้า -"
COUNTRY_PLACEHOLDER = "- กรุณาเลือกประเทศ -"
# คำเตือนเหล่านี้เป็นเพียงสัญญาณให้ตรวจสอบเพิ่ม ไม่ใช่ข้อกฎหมายหรือข้อห้ามอัตโนมัติ
REVIEW_WORDS = ["แบต", "ถ่าน", "power bank", "พาวเวอร์แบงค์", "ของเหลว", "น้ำหอม", "สเปรย์", "สารเคมี", "อาหาร", "ยา", "วิตามิน", "อาหารเสริม", "เครื่องสำอาง", "กัญชา", "กระท่อม", "อาวุธ", "ปืน", "เงินสด", "ธนบัตร", "แบรนด์เนม", "มือสอง", "มือ 2", "ลิขสิทธิ์", "ปลอม", "ก๊อป", "เจล", "น้ำมัน"]


def clean(v):
    return str(v).strip().casefold()


@st.cache_data(show_spinner=False)
def read_database(path, mtime):
    last_error = ""
    for options in ({"encoding": "utf-8-sig"}, {"encoding": "utf-8-sig", "sep": None, "engine": "python"}, {"encoding": "cp874"}):
        try:
            frame = pd.read_csv(path, dtype=str, keep_default_na=False, **options)
            frame.columns = frame.columns.astype(str).str.strip()
            if not {"Example Items", "Country"}.issubset(frame.columns):
                last_error = "CSV ต้องมีคอลัมน์ Example Items และ Country"
                continue
            if frame.empty:
                last_error = "CSV ไม่มีข้อมูล"
                continue
            return frame, ""
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
    return pd.DataFrame(), last_error


@st.cache_resource(show_spinner=False)
def openai_client(api_key):
    from openai import OpenAI
    return OpenAI(api_key=api_key, timeout=18.0, max_retries=0)


def prepare_image(raw):
    if len(raw) > 12 * 1024 * 1024:
        raise ValueError("ไฟล์ภาพใหญ่เกิน 12 MB")
    with Image.open(io.BytesIO(raw)) as source:
        source.verify()
    with Image.open(io.BytesIO(raw)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((512, 512))
        out = io.BytesIO()
        image.save(out, format="JPEG", quality=72, optimize=True)
        return out.getvalue()


def analyze_image(jpeg, api_key, model):
    prompt = ("You inspect a parcel photo. Identify only the most visible physical product. "
              "Return JSON with exactly these keys: product_th (Thai product name, short), "
              "category_th (Thai category), keywords_th (list of at most 4 Thai synonyms), "
              "uncertain (boolean). If unclear or multiple products, uncertain=true. "
              "Do not guess ingredients, battery contents, whether a brand is counterfeit, "
              "or whether shipping is legal. Do not decide shipping eligibility.")
    encoded = base64.b64encode(jpeg).decode("ascii")
    start = time.perf_counter()
    response = openai_client(api_key).responses.create(
        model=model,
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": prompt},
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{encoded}", "detail": "low"}
        ]}],
        text={"format": {"type": "json_object"}},
        max_output_tokens=180,
    )
    elapsed = round(time.perf_counter() - start, 2)
    result = json.loads(response.output_text)
    if not isinstance(result, dict) or not isinstance(result.get("product_th"), str):
        raise ValueError("AI ส่งผลลัพธ์ไม่ตรงรูปแบบ")
    result["product_th"] = result["product_th"].strip()[:100]
    result["category_th"] = str(result.get("category_th", "")).strip()[:100]
    result["keywords_th"] = [str(x).strip()[:60] for x in result.get("keywords_th", [])[:4]] if isinstance(result.get("keywords_th"), list) else []
    result["uncertain"] = result.get("uncertain") is not False
    return result, elapsed


def suggest_items(result, items):
    product = clean(result.get("product_th", ""))
    terms = [clean(x) for x in [result.get("category_th", "")] + result.get("keywords_th", [])]
    terms = [t for t in terms if len(t) >= 3]
    scored = []
    for item in items:
        name = clean(item)
        score = 0
        if product and name == product:
            score = 100
        elif product and (product in name or name in product) and len(name) >= 3:
            score = 85
        elif product:
            score = 50 * SequenceMatcher(None, product, name).ratio()
        if any(t in name for t in terms):
            score += 15
        if score >= 32:
            scored.append((score, item))
    return [name for _, name in sorted(scored, key=lambda pair: (-pair[0], pair[1]))[:30]]


def status_of(value):
    raw = clean(value).upper()
    if raw == "ACCEPTABLE":
        return "Acceptable"
    if raw == "UNACCEPTABLE":
        return "Unacceptable"
    if raw == "CHECK MSDS":
        return "Check MSDS"
    return "Unknown"


def combine_status(values):
    # หากมีข้อห้ามในแถวใดให้ยึดข้อห้ามไว้ก่อน และต้องไม่ใช้แถวแรกเพียงแถวเดียว
    statuses = [status_of(x) for x in values]
    if not statuses or "Unknown" in statuses:
        return "Unknown"
    if "Unacceptable" in statuses:
        return "Unacceptable"
    if "Check MSDS" in statuses:
        return "Check MSDS"
    return "Acceptable" if all(s == "Acceptable" for s in statuses) else "Unknown"


def image_result_cache():
    if "ai_cache" not in st.session_state:
        st.session_state.ai_cache = {}  # per session only; no shared customer images
    return st.session_state.ai_cache


file_path = Path(__file__).with_name("master_database.csv")
if not file_path.exists():
    st.error("ไม่พบ master_database.csv กรุณาวางไว้โฟลเดอร์เดียวกับ app.py")
    st.stop()
df, db_error = read_database(str(file_path), file_path.stat().st_mtime_ns)
if df.empty:
    st.error(f"โหลดฐานข้อมูลไม่สำเร็จ: {db_error}")
    st.stop()

items = sorted({str(x).strip() for x in df["Example Items"] if clean(x) not in ("", "-", "nan", "0", "none")})
items = sorted(set(items + [alias for alias, actual in ALIASES.items() if actual in items]))
db_countries = {str(x).strip() for x in df["Country"] if clean(x) not in ("", "-", "all", "nan")}
countries = [COUNTRY_PLACEHOLDER] + sorted(set(COUNTRIES) | db_countries)

col1, col2 = st.columns(2)
with col1:
    country = st.selectbox("🌍 ประเทศปลายทาง", countries)
with col2:
    agent = st.selectbox("🚚 เอเย่นต์ (Agent)", ["ทั้งหมด"] + AGENTS)
mode = st.radio("🛠️ วิธีตรวจสอบสินค้า", ["🔍 ค้นหาและเลือกรายชื่อสินค้า", "📸 ถ่ายภาพ/อัปโหลด (AI วิเคราะห์ทันที)"], horizontal=True)
selected_item = PLACEHOLDER

if mode.startswith("🔍"):
    selected_item = st.selectbox(f"📋 รายการสินค้า ({len(items)} รายการ)", [PLACEHOLDER] + items)
else:
    st.info("ถ่ายภาพหรืออัปโหลดภาพใหม่ ระบบจะวิเคราะห์อัตโนมัติหนึ่งครั้งต่อภาพ และไม่เสียค่า API ซ้ำเมื่อเปลี่ยนประเทศ/เอเย่นต์")
    c1, c2 = st.columns(2)
    with c1:
        camera = st.camera_input("📸 ถ่ายภาพสินค้า", key="photo_camera")
    with c2:
        upload = st.file_uploader("📁 อัปโหลดรูปสินค้า", type=["jpg", "jpeg", "png"], key="photo_upload")
    # ผู้ใช้สามารถเลือกแหล่งภาพได้ชัดเจนเมื่อมีทั้งสองช่อง
    if camera is not None and upload is not None:
        source = st.radio("เลือกภาพที่ต้องการวิเคราะห์", ["กล้อง", "ไฟล์อัปโหลด"], horizontal=True)
        active = camera if source == "กล้อง" else upload
    else:
        active = camera if camera is not None else upload

    if active is not None:
        raw = active.getvalue()
        fingerprint = hashlib.sha256(raw).hexdigest()
        st.image(raw, caption="ภาพสินค้าที่เลือก", width=260)
        if st.session_state.get("current_image") != fingerprint:
            st.session_state.current_image = fingerprint
            st.session_state["confirmed_item"] = PLACEHOLDER
            st.session_state["full_item"] = PLACEHOLDER
        cache = image_result_cache()
        if fingerprint not in cache:
            api_key = st.secrets.get("OPENAI_API_KEY", "")
            model = st.secrets.get("OPENAI_MODEL", "gpt-4.1-mini")
            if not api_key:
                cache[fingerprint] = {"error": "ไม่พบ OPENAI_API_KEY ใน Streamlit Secrets"}
            else:
                try:
                    with st.spinner("🤖 AI กำลังวิเคราะห์ภาพ..."):
                        jpeg = prepare_image(raw)
                        prediction, seconds = analyze_image(jpeg, api_key, model)
                    cache[fingerprint] = {"result": prediction, "seconds": seconds}
                except (UnidentifiedImageError, ValueError, json.JSONDecodeError) as exc:
                    cache[fingerprint] = {"error": f"ข้อมูลภาพ/ผลวิเคราะห์ไม่ถูกต้อง: {exc}"}
                except Exception as exc:
                    cache[fingerprint] = {"error": f"เรียก AI ไม่สำเร็จ ({type(exc).__name__}): {exc}"}
        outcome = cache[fingerprint]
        if "error" in outcome:
            st.error(outcome["error"])
            if st.button("🔁 ลองวิเคราะห์ภาพนี้อีกครั้ง"):
                cache.pop(fingerprint, None)
                st.rerun()
        else:
            prediction = outcome["result"]
            st.success(f"🤖 AI ระบุ: {prediction['product_th']} • หมวดหมู่: {prediction['category_th']}")
            st.metric("เวลาที่ OpenAI API ตอบกลับ", f"{outcome['seconds']:.2f} วินาที")
            if prediction["uncertain"]:
                st.warning("AI ไม่มั่นใจ หรือภาพมีสินค้าหลายชิ้น กรุณาตรวจสอบสินค้าจริงและฉลาก")
            candidates = suggest_items(prediction, items)
            if st.session_state.get("confirmed_item") not in [PLACEHOLDER] + candidates:
                st.session_state["confirmed_item"] = PLACEHOLDER
            choice = st.selectbox("📋 ยืนยันรายการสินค้าจากฐานข้อมูล", [PLACEHOLDER] + candidates, key="confirmed_item")
            with st.expander("ไม่พบชื่อสินค้าที่ตรง? เลือกจากรายการทั้งหมด"):
                fallback = st.selectbox("สินค้าทั้งหมด", [PLACEHOLDER] + items, key="full_item")
            selected_item = fallback if fallback != PLACEHOLDER else choice
            if selected_item == PLACEHOLDER:
                st.caption("โปรดยืนยันสินค้าจริงก่อนตรวจสอบเงื่อนไขการจัดส่ง")
    else:
        st.caption("รอภาพใหม่จากกล้องหรือไฟล์อัปโหลด")

if country != COUNTRY_PLACEHOLDER and selected_item != PLACEHOLDER:
    st.divider()
    st.subheader("📊 ผลการตรวจสอบข้อกำหนดการจัดส่ง")
    item_name = ALIASES.get(selected_item, selected_item)
    product_rows = df[df["Example Items"].map(clean) == clean(item_name)]
    # รองรับ Country=All เฉพาะกรณีฐานข้อมูลระบุชัด และแยกจากข้อมูลประเทศอื่น
    exact_rows = product_rows[product_rows["Country"].map(clean) == clean(country)]
    generic_rows = product_rows[product_rows["Country"].map(clean).isin(["all", "ทุกประเทศ"])]
    rows = pd.concat([exact_rows, generic_rows], ignore_index=True).drop_duplicates()
    warnings = [word for word in REVIEW_WORDS if clean(word) in clean(selected_item)]
    if warnings:
        st.warning("⚠️ อาจมีข้อกำหนดพิเศษ: " + ", ".join(warnings) + " — ต้องตรวจสอบชนิดสินค้า เอกสาร และประกาศล่าสุด")
    if rows.empty:
        st.error("⛔ ยังยืนยันการจัดส่งไม่ได้: ไม่พบข้อมูลสินค้านี้สำหรับประเทศปลายทาง")
        st.info("กรุณาตรวจสอบฐานข้อมูลต้นทางหรือสอบถามผู้รับผิดชอบก่อนส่ง")
    else:
        if not exact_rows.empty and not generic_rows.empty:
            st.caption("ใช้ข้อมูลประเทศปลายทางร่วมกับแถว Country=All ที่ระบุไว้ในฐานข้อมูล")
        carriers = AGENTS if agent == "ทั้งหมด" else [agent]
        for carrier in carriers:
            state = combine_status(rows[carrier].tolist()) if carrier in rows.columns else "Unknown"
            if state == "Unacceptable":
                st.error(f"❌ {carrier}: Unacceptable — ฐานข้อมูลระบุว่าไม่ผ่านเงื่อนไข")
            elif state == "Check MSDS":
                st.warning(f"📄 {carrier}: Check MSDS — ต้องตรวจเอกสารและขออนุมัติก่อนส่ง")
            elif state == "Acceptable":
                if warnings:
                    st.warning(f"⚠️ {carrier}: ฐานข้อมูลระบุ Acceptable แต่มีประเด็นต้องตรวจสอบเพิ่มเติม")
                else:
                    st.success(f"🟢 {carrier}: ฐานข้อมูลระบุ Acceptable (ยังต้องตรวจสอบเงื่อนไขล่าสุด)")
            else:
                st.warning(f"❓ {carrier}: ข้อมูลไม่ครบ/ไม่รู้จักสถานะ — ห้ามสรุปว่าส่งได้")
        with st.expander("ดูข้อมูลเงื่อนไขจาก CSV", expanded=True):
            st.dataframe(rows, use_container_width=True, hide_index=True)
    st.info("ผล AI ใช้ระบุสินค้าเท่านั้น ไม่ใช่คำอนุญาตให้จัดส่ง เจ้าหน้าที่ต้องตรวจสินค้าจริงและเงื่อนไขบริษัทขนส่งล่าสุดก่อนดำเนินการ")
