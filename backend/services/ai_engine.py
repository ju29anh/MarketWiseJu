"""Private provider integration, voice generation and source-based strategy helpers."""
import base64
import json
import logging
import re
import struct
import unicodedata
from urllib.parse import urlsplit
from urllib.request import Request, build_opener
from typing import Any, Dict, List, Optional, Tuple


from core.config import settings

logger = logging.getLogger(__name__)

# Internal API execution fallback order (prioritizes smartest responsive full Flash models, with multi-tier fallback)
_GENERATION_MODEL_ORDER = [
    ("gemini-3.6-flash", "Gemini 3.6 Flash (gemini-3.6-flash)"),
    ("gemini-3.5-flash", "Gemini 3.5 Flash (gemini-3.5-flash)"),
    ("gemini-3.5-flash-lite", "Gemini 3.5 Flash-Lite (gemini-3.5-flash-lite)"),
    ("gemini-3.1-flash-lite", "Gemini 3.1 Flash-Lite (gemini-3.1-flash-lite)"),
]

CATEGORY_TO_DATASET = {
    "Technology & Gaming": "technology_gaming_laptops.csv",
    "Smartphones & Mobile": "smartphones_market.csv",
    "Audio & Consumer Electronics": "consumer_electronics_audio.csv",
    "Fashion & E-Commerce": "fashion_apparel_trends.csv",
    "Food & Beverage": "food_beverage_specialty_coffee.csv",
    "FMCG & Consumer Goods": "fmcg_packaged_goods.csv",
    "Beauty & Skincare": "beauty_skincare_products.csv",
    "Electric Vehicles": "automotive_electric_vehicles.csv",
    "Education & EdTech": "education_edtech_courses.csv",
    "Healthcare & Fitness": "healthcare_fitness_wearables.csv",
    "Smart Home & IoT": "smart_home_iot_devices.csv",
    "Digital Services & SaaS": "digital_services_saas.csv",
    "Real Estate & Housing": "real_estate_proptech.csv",
    "Tourism & Hospitality": "tourism_travel_hospitality.csv",
    "FinTech & Digital Finance": "fintech_digital_banking.csv",
    "Logistics & Supply Chain": "logistics_supply_chain.csv",
}

# Reputable Web Domains & Authority Registry
TIER1_ACADEMIC_GOV_DOMAINS = (
    ".gov.vn", ".edu.vn", ".ac.vn", ".gov", ".edu",
    "wikipedia.org", "wikidata.org", "openalex.org",
    "chinhphu.vn", "moet.gov.vn", "gso.gov.vn", "worldbank.org",
    "imf.org", "undp.org", "unesco.org", "who.int",
)

TIER2_REPUTABLE_PRESS_DOMAINS = (
    "vnexpress.net", "tuoitre.vn", "thanhnien.vn", "cafef.vn",
    "vneconomy.vn", "baochinhphu.vn", "nhandan.vn", "dantri.com.vn",
    "vietnamnet.vn", "laodong.vn", "vtv.vn", "vov.vn", "plo.vn",
    "tienphong.vn", "sggp.org.vn", "thesaigontimes.vn", "baobinhduong.vn",
    "baodautu.vn", "congthuong.vn", "vietstock.vn", "ndh.vn",
    "forbes.com", "reuters.com", "bloomberg.com", "nikkei.com",
    "ft.com", "cnbc.com", "techcrunch.com", "news.google.com",
)

CATEGORY_PEERS_DEFAULT: Dict[str, List[str]] = {
    "Education & EdTech": [
        "ĐH Quốc gia TP.HCM (VNU-HCM)",
        "ĐH Bách Khoa TP.HCM",
        "ĐH Thủ Dầu Một (TDMU)",
        "ĐH Quốc tế Miền Đông (EIU)",
        "ĐH Kinh tế TP.HCM (UEH)",
        "ĐH FPT (FPT University)",
        "ĐH Công nghiệp TP.HCM (IUH)",
        "ĐH Bình Dương (BDU)",
        "ĐH Sư phạm Kỹ thuật TP.HCM",
        "ĐH Tôn Đức Thắng",
        "ĐH Văn Lang",
    ],
    "Food & Beverage": [
        "Highlands Coffee",
        "Phúc Long Coffee & Tea",
        "The Coffee House",
        "Katinat Saigon Kafe",
        "Phê La",
        "Cộng Cà Phê",
        "Starbucks Vietnam",
        "Trung Nguyên Legend",
    ],
    "Electric Vehicles": [
        "VinFast VF 5 Plus",
        "VinFast VF 6",
        "VinFast VF 7",
        "VinFast VF 3",
        "BYD Atto 3",
        "Tesla Model Y",
        "Hyundai Ioniq 5",
        "Wuling Mini EV",
    ],
    "Smartphones & Mobile": [
        "iPhone 16 Pro Max",
        "Samsung Galaxy S24 Ultra",
        "Xiaomi 14 Ultra",
        "OPPO Find X7",
        "Samsung Galaxy Z Fold6",
        "iPhone 15 Plus",
        "Vivo X100 Pro",
        "Realme GT 6",
    ],
    "Technology & Gaming": [
        "ASUS ROG Strix G16",
        "Lenovo Legion Pro 5",
        "Acer Predator Helios Neo 16",
        "MSI Raider GE68 HX",
        "Dell Alienware m16 R2",
        "HP Omen Transcend 14",
        "MacBook Pro 16 M3 Max",
        "Gigabyte Aorus 16X",
    ],
    "Beauty & Skincare": [
        "La Roche-Posay Cicaplast",
        "Cocoon Vietnam",
        "Skin1004 Madagascar Centella",
        "The Ordinary Niacinamide",
        "Paula's Choice BHA 2%",
        "CeraVe Moisturizing",
        "Anessa Perfect UV",
        "L'Oréal Paris Revitalift",
    ],
    "Real Estate & Housing": [
        "Vinhomes Grand Park",
        "Masterise Homes Global City",
        "Ecopark Hưng Yên",
        "Khang Điền The Privia",
        "Nam Long Mizuki Park",
        "Becamex Tokyu Bình Dương",
        "Phú Mỹ Hưng Midtown",
        "Sun Group Sun Urban City",
    ],
    "FinTech & Digital Finance": [
        "Vietcombank VCB Digibank",
        "Techcombank Mobile",
        "MB Bank App",
        "Ví Điện Tử MoMo",
        "VNPay QR",
        "ZaloPay",
        "Ngân hàng số Cake by VPBank",
        "TCBS Techcom Securities",
    ],
    "Healthcare & Fitness": [
        "Hệ thống Y tế Vinmec",
        "Bệnh viện Đa khoa Tâm Anh",
        "Hệ thống Nhà thuốc Long Châu",
        "Hệ thống Tiêm chủng VNVC",
        "Bệnh viện Đại học Y Dược",
        "Hệ thống Y tế Medlatec",
        "Nhà thuốc Pharmacity",
        "Garmin Forerunner Health",
    ],
    "Digital Services & SaaS": [
        "FPT Software",
        "Viettel Solutions",
        "MISA AMIS Platform",
        "Base.vn Enterprise",
        "VNG Cloud / Zalo Mini App",
        "KiotViet POS",
        "VNPT IT",
        "OpenAI ChatGPT Enterprise",
    ],
    "Tourism & Hospitality": [
        "Vinpearl Resort & Spa",
        "Sun World Entertainment",
        "Vietnam Airlines",
        "Vietjet Air",
        "Traveloka Vietnam",
        "Booking.com Vietnam",
        "InterContinental Danang",
        "Saigontourist Group",
    ],
    "Logistics & Supply Chain": [
        "Viettel Post",
        "Giao Hàng Tiết Kiệm (GHTK)",
        "Giao Hàng Nhanh (GHN)",
        "J&T Express Vietnam",
        "SPX Express",
        "Gemadept Logistics",
        "Tân Cảng Sài Gòn (SNP)",
        "DHL Express Vietnam",
    ],
    "Fashion & E-Commerce": [
        "Coolmate Vietnam",
        "Uniqlo Vietnam",
        "Zara Vietnam",
        "Shopee Mall Fashion",
        "TikTok Shop Vietnam",
        "Routine Menswear",
        "IVY moda",
        "Nike Vietnam",
    ],
    "FMCG & Consumer Goods": [
        "Masan Consumer (Chin-su / Omachi)",
        "Acecook Việt Nam (Hảo Hảo)",
        "Vinamilk",
        "TH true MILK",
        "Unilever Vietnam",
        "Suntory PepsiCo Vietnam",
        "Tập đoàn Thiên Long",
        "Bách Hóa Xanh",
    ],
    "Smart Home & IoT": [
        "Roborock S8 Pro Ultra",
        "Ecovacs Deebot X2 Omni",
        "Dreame L20 Ultra",
        "Xiaomi Smart Home Ecosystem",
        "Camera An Ninh Ezviz",
        "Máy lọc nước Karofi",
        "Philips Hue Smart Lighting",
        "Panasonic Smart Inverter",
    ],
    "Audio & Consumer Electronics": [
        "Sony WH-1000XM5",
        "Apple AirPods Pro 2",
        "Bose QuietComfort Ultra",
        "Marshall Stanmore III",
        "JBL Charge 5",
        "Sennheiser Momentum 4",
        "Samsung Galaxy Buds3 Pro",
        "Harman Kardon Aura Studio 4",
    ],
}

# Known Real-World Vietnamese Entity Calibrations (Grounded Baseline Profiles)
KNOWN_ENTITY_PROFILES = {'dai hoc thu dau mot': {'summary_hint': 'Trường đại học công lập trọng điểm của tỉnh Bình Dương, đạt chuẩn '
                                         'kiểm định AUN-QA, quy mô hơn 20.000 sinh viên.'},
 'dai hoc binh duong': {'summary_hint': 'Trường đại học đa ngành tại Bình Dương thành lập năm 1997, định '
                                        'hướng đào tạo ứng dụng và liên kết doanh nghiệp KCN.'}}

_AI_CLASSIFY_CACHE: Dict[str, Dict[str, Any]] = {}
_AI_SYNTHESIS_CACHE: Dict[str, Dict[str, Any]] = {}
_AI_QUANT_CACHE: Dict[str, Dict[str, Any]] = {}


def _clean_key(text: str) -> str:
    s = unicodedata.normalize("NFD", str(text or "").casefold().strip()).replace("đ", "d")
    return " ".join("".join(c for c in s if unicodedata.category(c) != "Mn").split())


def is_ai_configured() -> bool:
    key = getattr(settings, "gemini_api_key", None)
    if not key:
        return False
    return bool(key.get_secret_value().strip())


def score_web_source_credibility(url: str, provider: str = "", excerpt: str = "") -> Dict[str, Any]:
    """
    Evaluates the authority and trustworthiness of a web source based on domain, provider, and content depth.
    """
    host = ""
    try:
        host = (urlsplit(url).hostname or "").lower()
    except Exception:
        host = ""

    prov_low = (provider or "").lower()
    if any(host == d.lstrip('.') or host.endswith(d if d.startswith('.') else '.' + d) for d in TIER1_ACADEMIC_GOV_DOMAINS):
        base_score = 95
        tier = "Học thuật / Chính phủ / Bách khoa (.edu / .gov / Wiki / OpenAlex)"
        is_reputable = True
    elif any(host == d.lstrip('.') or host.endswith(d if d.startswith('.') else '.' + d) for d in TIER2_REPUTABLE_PRESS_DOMAINS):
        base_score = 91
        tier = "Báo chí Chính thống Uy tín"
        is_reputable = True
    elif host.endswith(".vn") or host.endswith(".org"):
        base_score = 65
        tier = "Tên miền tổ chức; chưa xác minh"
        is_reputable = False
    else:
        base_score = 78
        tier = "Nguồn Web & Cổng thông tin Ngành"
        is_reputable = False

    if excerpt and len(excerpt) > 80:
        base_score = min(99, base_score + 2)

    return {
        "domain": host or provider or "web",
        "credibility_score": int(base_score),
        "credibility_tier": tier,
        "is_reputable": is_reputable,
    }


def _extract_json_block(raw_text: str) -> Optional[Dict[str, Any]]:
    if not raw_text:
        return None
    cleaned = re.sub(r"```(?:json)?", "", raw_text, flags=re.IGNORECASE).replace("```", "").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(cleaned[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except Exception:
        return None


def call_gemini_json(prompt: str, timeout: float = 6.0, preferred_model: Optional[str] = None) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Calls Google Generative Language API across the multi-tier Gemini Flash cascade
    (gemini-3.6-flash -> gemini-3.5-flash -> gemini-3.5-flash-lite -> gemini-3.1-flash-lite).
    Returns (parsed_dict_or_None, model_id).
    """
    if not is_ai_configured():
        return None, None

    api_key = settings.gemini_api_key.get_secret_value().strip()
    model_sequence = list(_GENERATION_MODEL_ORDER)
    if preferred_model == "gemini-3.8-flash":
        preferred_model = "gemini-3.6-flash"
    if preferred_model:
        model_sequence.sort(key=lambda item: 0 if item[0] == preferred_model else 1)

    for model_id, model_label in model_sequence:
        gen_cfg: Dict[str, Any] = {"temperature": 0.2, "maxOutputTokens": 4096}
        if "gemini" in model_id:
            gen_cfg["responseMimeType"] = "application/json"
        if "lite" not in model_id and ("3.6-flash" in model_id or "3.5-flash" in model_id):
            gen_cfg["thinkingConfig"] = {"thinkingBudget": 0}

        payload = json.dumps({
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": gen_cfg,
        }).encode("utf-8")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
        try:
            from services.research import NoRedirect
            req = Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key,
                    "User-Agent": "MarketWise-AI-Engine/3.8",
                },
            )
            with build_opener(NoRedirect).open(req, timeout=timeout) as resp:
                raw = resp.read(500_000).decode("utf-8", errors="ignore")
                data = json.loads(raw)
                candidates = data.get("candidates") or []
                if candidates:
                    parts = (candidates[0].get("content") or {}).get("parts") or []
                    text = "".join(p.get("text", "") for p in parts if not p.get("thought"))
                    if text:
                        parsed = _extract_json_block(text)
                        if parsed:
                            return parsed, model_id
        except Exception as exc:
            logger.debug("Gemini model %s skipped: %s", model_id, type(exc).__name__)
            continue

    return None, None


def _pcm16_to_wav_bytes(pcm_bytes: bytes, sample_rate: int = 24000, channels: int = 1) -> bytes:
    """Wraps raw 16-bit PCM mono audio returned by Gemini TTS into a standard browser-playable WAV container."""
    if pcm_bytes.startswith(b"RIFF"):
        return pcm_bytes
    byte_rate = sample_rate * channels * 2
    block_align = channels * 2
    data_size = len(pcm_bytes)
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,
        1,  # PCM format
        channels,
        sample_rate,
        byte_rate,
        block_align,
        16,  # bits per sample
        b"data",
        data_size,
    )
    return header + pcm_bytes


def generate_tts_briefing(text: str, voice_name: str = "Kore") -> Dict[str, Any]:
    """
    Synthesizes an executive voice briefing using Google's `gemini-3.8-flash-tts` model.
    Falls back cleanly with a structured Vietnamese speech script if network/quota is unavailable.
    """
    clean_script = re.sub(r"[#*`>_~]+", " ", str(text or "")).strip()
    clean_script = " ".join(clean_script.split())[:1200]
    if not clean_script:
        clean_script = "Báo cáo phân tích thị trường và dự báo học máy từ hệ thống MarketWise."

    if is_ai_configured():
        api_key = settings.gemini_api_key.get_secret_value().strip()
        tts_models = [
            "gemini-3.8-flash-tts",
            "gemini-3.8-flash-lite-tts",
            "gemini-3.1-flash-tts-preview",
            "gemini-2.5-flash-preview-tts",
        ]
        for model_id in tts_models:
            payload = json.dumps({
                "contents": [{"role": "user", "parts": [{"text": f"Đọc bản tin phân tích thị trường bằng tiếng Việt rõ ràng, chuyên nghiệp: {clean_script}"}]}],
                "generationConfig": {
                    "responseModalities": ["AUDIO"],
                    "speechConfig": {
                        "voiceConfig": {
                            "prebuiltVoiceConfig": {
                                "voiceName": voice_name
                            }
                        }
                    }
                }
            }).encode("utf-8")

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_id}:generateContent"
            try:
                from services.research import NoRedirect
                req = Request(
                    url,
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": api_key,
                        "User-Agent": "MarketWise-AI-TTS/3.8",
                    },
                )
                with build_opener(NoRedirect).open(req, timeout=10.0) as resp:
                    raw = resp.read(5_000_000).decode("utf-8", errors="ignore")
                    data = json.loads(raw)
                    candidates = data.get("candidates") or []
                    if candidates:
                        parts = (candidates[0].get("content") or {}).get("parts") or []
                        for part in parts:
                            inline = part.get("inlineData") or {}
                            b64_audio = inline.get("data")
                            mime = inline.get("mimeType") or "audio/pcm"
                            if b64_audio:
                                raw_audio = base64.b64decode(b64_audio)
                                wav_bytes = _pcm16_to_wav_bytes(raw_audio) if "pcm" in mime.lower() or not raw_audio.startswith(b"RIFF") else raw_audio
                                wav_b64 = base64.b64encode(wav_bytes).decode("ascii")
                                return {
                                    "status": "ok",
                                    "model_used": model_id,
                                    "voice": voice_name,
                                    "audio_data_url": f"data:audio/wav;base64,{wav_b64}",
                                    "audio_base64": wav_b64,
                                    "mime_type": "audio/wav",
                                    "fallback_browser_tts": False,
                                    "clean_text": clean_script,
                                    "script": clean_script,
                                    "mode": "neural_api_audio",
                                }
            except Exception as exc:
                logger.debug("TTS model %s fallback: %s", model_id, type(exc).__name__)
                continue

    return {
        "status": "ok",
        "model_used": "browser_speech_synthesis",
        "voice": "vi-VN Standard Neural",
        "audio_data_url": None,
        "audio_base64": None,
        "mime_type": None,
        "fallback_browser_tts": True,
        "clean_text": clean_script,
        "script": clean_script,
        "mode": "browser_speech_synthesis",
    }


def classify_query_with_ai(query: str, corpus_text: str = "") -> Optional[Dict[str, str]]:
    """
    Uses `gemini-3.5-flash-lite` / `gemini-3.8-flash` to classify an ambiguous query into one of the 16 canonical categories.
    """
    if not query or not is_ai_configured():
        return None

    cache_key = _clean_key(query)
    if cache_key in _AI_CLASSIFY_CACHE:
        return _AI_CLASSIFY_CACHE[cache_key]

    valid_categories = list(CATEGORY_TO_DATASET.keys())
    prompt = (
        f"Phân loại đối tượng/sản phẩm/tổ chức sau vào ĐÚNG 1 danh mục phù hợp nhất trong danh sách 16 ngành.\n"
        f"Đối tượng: \"{query}\"\n"
        f"Ngữ cảnh bổ sung: \"{(corpus_text or '')[:400]}\"\n"
        f"Danh sách 16 ngành hợp lệ: {json.dumps(valid_categories, ensure_ascii=False)}\n"
        f"Trả về duy nhất JSON có cấu trúc: "
        f"{{\"category\": \"<tên ngành chính xác trong danh sách>\", \"sub_sector_vi\": \"<tên phân ngành cụ thể bằng tiếng Việt>\"}}"
    )
    parsed, model_label = call_gemini_json(prompt, timeout=3.5, preferred_model="gemini-3.5-flash-lite")
    if parsed and parsed.get("category") in CATEGORY_TO_DATASET:
        cat = parsed["category"]
        result = {
            "category": cat,
            "dataset": CATEGORY_TO_DATASET[cat],
            "sub_sector_vi": str(parsed.get("sub_sector_vi") or cat),
            "ai_model": model_label or "Gemini 3.5 Flash-Lite",
        }
        _AI_CLASSIFY_CACHE[cache_key] = result
        return result
    return None


def get_domain_peers(product_name: str, category: str) -> List[str]:
    """
    Returns realistic domain-specific peer entities for clustering & competitor comparison
    so that the scatter plot and benchmark table always show entities directly related to `product_name`.
    """
    cache_key = _clean_key(product_name)
    if cache_key in _AI_SYNTHESIS_CACHE:
        cached_peers = _AI_SYNTHESIS_CACHE[cache_key].get("real_peers")
        if cached_peers and len(cached_peers) >= 4:
            return cached_peers

    base_peers = list(CATEGORY_PEERS_DEFAULT.get(category, CATEGORY_PEERS_DEFAULT["FMCG & Consumer Goods"]))
    cleaned_target = _clean_key(product_name)
    filtered = [p.strip() for p in base_peers if _clean_key(p) != cleaned_target]
    return filtered[:7] + [product_name.strip()]


def build_web_grounded_dataset(product_name, category, web_sources=None, web_research=None):
    """Search excerpts cannot establish a historical training series."""
    raise ValueError('Cần dữ liệu quan sát có nguồn; không tự tạo chuỗi thời gian từ trích đoạn tìm kiếm.')


def build_domain_specific_strategy(
    product_name: str,
    category: str,
    potential_score: int,
    growth_pct: float,
    cluster_name: str,
    web_sources: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Generates domain-accurate Vietnamese strategy and peer group for `product_name`,
    combining Gemini 3.8 Flash / 3.5 Flash-Lite synthesis with specialized industry playbooks.
    """
    cache_key = f"{_clean_key(product_name)}::{category}::{potential_score}"
    if cache_key in _AI_SYNTHESIS_CACHE:
        return _AI_SYNTHESIS_CACHE[cache_key]

    from services.research_evidence import subject_context
    from services.report_sections import get_keyword_intelligence
    ctx = subject_context(product_name, web_sources or [])
    if category and category != "General Research":
        ctx = {**ctx, "category": category}
    intel = get_keyword_intelligence(product_name, ctx, web_sources or [])

    snippets = []
    for s in (web_sources or [])[:6]:
        t = s.get("title", "")
        e = s.get("excerpt", "")
        prov = s.get("provider", "Web")
        if t or e:
            snippets.append(f"- [{prov}] {t}: {e[:200]}")
    context_str = "\n".join(snippets) if snippets else "Dữ liệu chuẩn ngành tại Việt Nam."

    # 1. Try Gemini 3.8 Flash / 3.5 Flash-Lite Multi-Model Synthesis first if API key is configured
    if is_ai_configured() and getattr(settings, "environment", "") != "test":
        prompt = (
            f"Bạn là chuyên gia phân tích chiến lược thị trường cấp cao tại Việt Nam sử dụng mô hình Gemini 3.8 Flash.\n"
            f"Hãy phân tích chuyên sâu, cụ thể và hoàn toàn sát thực tế cho đối tượng: \"{product_name}\" "
            f"(Lĩnh vực: {category}, Điểm tiềm năng: {potential_score}/100, Tăng trưởng dự báo: {growth_pct:+.1f}%).\n"
            f"Thông tin thu thập từ các nguồn Web uy tín & Báo chí:\n{context_str}\n\n"
            f"YÊU CẦU QUAN TRỌNG:\n"
            f"1. Mọi nhận định, đối thủ cùng ngành (real_peers), cơ hội, rủi ro, 5 trụ cột chiến lược và kế hoạch 30-60-90 ngày "
            f"PHẢI viết riêng cho đúng bản chất thực tế của \"{product_name}\" tại Việt Nam (không dùng câu chữ mẫu chung chung).\n"
            f"2. Ví dụ: Nếu là trường Công an/Quân đội (như Trường đại học Cảnh sát nhân dân) thì phân tích chỉ tiêu biên chế Bộ Công an, "
            f"sơ tuyển địa phương, kỳ thi Đánh giá năng lực CA1/CA2, miễn 100% học phí, rèn luyện nội trú và phân công công tác sau tốt nghiệp. "
            f"Nếu là trường đại học dân sự thì phân tích tuyển sinh đa phương thức, kiểm định AUN-QA/ABET, học phí tín chỉ, học kỳ doanh nghiệp. "
            f"Nếu là điện thoại nhập khẩu Trung Quốc thì phân tích cấu hình/giá (P/P), nhập khẩu chính ngạch hợp quy vs xách tay, ROM Quốc tế, bảo hành màn hình/nguồn.\n\n"
            f"Trả về DUY NHẤT 1 JSON hợp lệ theo đúng cấu trúc:\n"
            f"{{\n"
            f"  \"sub_sector_vi\": \"<phân ngành cụ thể tiếng Việt của {product_name}>\",\n"
            f"  \"real_peers\": [\"<7 đơn vị/sản phẩm cùng phân khúc tại VN để đối sánh>\", \"{product_name}\"],\n"
            f"  \"executive_summary\": \"<Đoạn phân tích tổng quan thực tế 3-4 câu sâu sắc, nêu rõ đặc thù riêng của {product_name}>\",\n"
            f"  \"opportunities\": [\"<Cơ hội 1 cụ thể của {product_name}>\", \"<Cơ hội 2 cụ thể>\", \"<Cơ hội 3 cụ thể>\"],\n"
            f"  \"risks\": [\"<Rủi ro/thách thức 1 cụ thể của {product_name}>\", \"<Rủi ro 2 cụ thể>\", \"<Rủi ro 3 cụ thể>\"],\n"
            f"  \"target_segment\": \"🎯 <Phân khúc đối tượng mục tiêu đặc thù của {product_name}>\",\n"
            f"  \"product_strategy\": \"📦 <Chiến lược sản phẩm/chương trình đào tạo/dịch vụ đặc thù cho {product_name}>\",\n"
            f"  \"pricing_strategy\": \"💰 <Chiến lược định giá/học phí/chế độ đãi ngộ đặc thù cho {product_name}>\",\n"
            f"  \"marketing_strategy\": \"📢 <Chiến lược truyền thông & thu hút khách hàng/thí sinh đặc thù cho {product_name}>\",\n"
            f"  \"distribution_strategy\": \"🚚 <Chiến lược kênh phân phối/tuyển sinh/cơ sở hạ tầng đặc thù cho {product_name}>\",\n"
            f"  \"recommended_action\": \"🚀 <Khuyến nghị hành động trọng tâm sắc bén cho {product_name}>\",\n"
            f"  \"action_plan_30_60_90\": [\n"
            f"    {{\"period\": \"Ngày 1–30\", \"goal\": \"<Mục tiêu 30 ngày đầu cụ thể cho {product_name}>\", \"actions\": [\"<Việc cụ thể 1>\", \"<Việc cụ thể 2>\", \"<Việc cụ thể 3>\"], \"owner\": \"<Bộ phận phụ trách>\", \"deliverable\": \"<Sản phẩm bàn giao>\", \"gate\": \"<Điều kiện nghiệm thu>\"}},\n"
            f"    {{\"period\": \"Ngày 31–60\", \"goal\": \"<Mục tiêu ngày 31-60 cụ thể cho {product_name}>\", \"actions\": [\"<Việc cụ thể 1>\", \"<Việc cụ thể 2>\", \"<Việc cụ thể 3>\"], \"owner\": \"<Bộ phận phụ trách>\", \"deliverable\": \"<Sản phẩm bàn giao>\", \"gate\": \"<Điều kiện nghiệm thu>\"}},\n"
            f"    {{\"period\": \"Ngày 61–90\", \"goal\": \"<Mục tiêu ngày 61-90 cụ thể cho {product_name}>\", \"actions\": [\"<Việc cụ thể 1>\", \"<Việc cụ thể 2>\", \"<Việc cụ thể 3>\"], \"owner\": \"<Bộ phận phụ trách>\", \"deliverable\": \"<Sản phẩm bàn giao>\", \"gate\": \"<Điều kiện nghiệm thu>\"}}\n"
            f"  ]\n"
            f"}}"
        )
        parsed, model_label = call_gemini_json(prompt, timeout=9.0, preferred_model="gemini-3.6-flash")
        if parsed and isinstance(parsed.get("real_peers"), list) and parsed.get("executive_summary"):
            peers = [str(p).strip() for p in parsed["real_peers"] if str(p).strip()]
            if _clean_key(product_name) not in {_clean_key(p) for p in peers}:
                peers.append(product_name.strip())
            parsed["real_peers"] = peers[:8]
            if not isinstance(parsed.get("action_plan_30_60_90"), list) or len(parsed["action_plan_30_60_90"]) != 3:
                parsed["action_plan_30_60_90"] = intel["action_plan"]
            parsed["specific_kpis"] = intel["kpis"]
            parsed["ai_model_used"] = model_label or "gemini-3.6-flash"
            _AI_SYNTHESIS_CACHE[cache_key] = parsed
            _AI_SYNTHESIS_CACHE[_clean_key(product_name)] = parsed
            return parsed

    # 2. Deep Sub-Domain & Archetype Intelligence Fallback (tailored per entity & sub-sector)
    q_low = _clean_key(product_name)
    peers = [p.strip() for p in intel.get("peers", "").split(",") if p.strip()]
    if len(peers) < 4:
        peers = get_domain_peers(product_name, category)
    elif _clean_key(product_name) not in {_clean_key(p) for p in peers}:
        peers = peers[:7] + [product_name.strip()]
    known_hint = (KNOWN_ENTITY_PROFILES.get(q_low) or {}).get("summary_hint", "")

    if intel.get("sub_type") == "police_military_academy":
        result = {
            "sub_sector_vi": "Đào tạo Sĩ quan Lực lượng Vũ trang & An ninh Quốc gia",
            "real_peers": peers,
            "ai_model_used": "MarketWise rule-based strategy engine (Public Security & Academy)",
            "executive_summary": (
                f"“{product_name}” là cơ sở giáo dục đại học trọng điểm khối lực lượng vũ trang với điểm tiềm năng đạt "
                f"{potential_score}/100 và xu hướng quy mô chỉ tiêu dự báo {growth_pct:+.1f}% trong 7 kỳ tới. "
                f"Đơn vị tuyển sinh theo chỉ tiêu biên chế phân vùng địa bàn, kết hợp sơ tuyển chính trị - sức khỏe tại địa phương và kỳ thi Đánh giá năng lực (CA1, CA2), "
                f"đào tạo học viên chính quy hưởng chế độ miễn 100% học phí và phân công công tác trực tiếp sau tốt nghiệp."
            ),
            "opportunities": [
                f"Chủ trương xây dựng lực lượng chính quy, tinh nhuệ, hiện đại đến năm 2030 thúc đẩy đầu tư mạnh vào hạ tầng huấn luyện và phòng Lab nghiệp vụ tại “{product_name}”.",
                f"Nhu cầu đào tạo sĩ quan chuyên sâu về phòng chống tội phạm công nghệ cao, điều tra số, kỹ thuật hình sự và quản lý hành chính trên nền tảng dữ liệu quốc gia.",
                f"Mở rộng hợp tác đào tạo, nghiên cứu khoa học nghiệp vụ và chia sẻ kinh nghiệm thực tiễn với Công an các đơn vị, địa phương và đối tác quốc tế.",
            ],
            "risks": [
                f"Yêu cầu đổi mới giáo trình nghiệp vụ liên tục để theo kịp phương thức hoạt động tinh vi của tội phạm công nghệ cao và tội phạm xuyên quốc gia.",
                f"Sự chênh lệch tỷ lệ chọi và phổ điểm chuẩn giữa các phân vùng tuyển sinh, tổ hợp xét tuyển (CA1, CA2) và tiêu chuẩn sơ tuyển sức khỏe/chính trị.",
                f"Áp lực đầu tư đồng bộ thao trường chiến thuật, phòng thực hành mô phỏng số và phát triển đội ngũ giảng viên vừa giỏi lý luận vừa dày dạn thực tiễn chiến đấu.",
            ],
            "target_segment": f"🎯 {intel['audience']}.",
            "product_strategy": f"📦 Chuẩn hóa chương trình đào tạo sĩ quan nghiệp vụ của “{product_name}” theo hướng kết hợp chặt chẽ giữa pháp luật, nghiệp vụ chuyên sâu, võ thuật - điều lệnh và kỹ năng điều tra công nghệ số.",
            "pricing_strategy": f"💰 Thực hiện chế độ đài thọ 100% học phí, trang cấp quân trang, bố trí nội trú và cấp phụ cấp sinh hoạt phí cho học viên chính quy tại “{product_name}” theo quy định của Nhà nước và Bộ chủ quản.",
            "marketing_strategy": f"📢 Phối hợp Ban Tuyển sinh Công an các tỉnh/thành phố và các trường THPT truyền thông minh bạch về tiêu chuẩn sơ tuyển, lịch thi đánh giá CA1/CA2 và truyền thống vẻ vang của “{product_name}”.",
            "distribution_strategy": f"🚚 Phát triển đồng bộ cơ sở đào tạo chính, hệ thống thao trường, trung tâm huấn luyện thực hành nghiệp vụ và mạng lưới liên kết thực tập tốt nghiệp tại Công an các đơn vị, địa phương.",
            "recommended_action": f"🚀 TẬP TRUNG HIỆN ĐẠI HÓA ĐÀO TẠO NGHIỆP VỤ & CHUẨN HÓA NGUỒN TUYỂN: “{product_name}” cần ưu tiên nâng cấp hạ tầng thực hành kỹ thuật hình sự - an ninh mạng và phối hợp sát với địa phương ngay từ khâu sơ tuyển.",
            "action_plan_30_60_90": intel["action_plan"],
            "specific_kpis": intel["kpis"],
        }
        _AI_SYNTHESIS_CACHE[cache_key] = result
        return result

    result = {
        "sub_sector_vi": ctx.get("label", category),
        "real_peers": peers,
        "ai_model_used": "MarketWise rule-based strategy engine",
        "executive_summary": (
            f"Đối với “{product_name}” trong lĩnh vực {ctx.get('label', category)} (Điểm tiềm năng: {potential_score}/100, "
            f"xu hướng dự báo 7 kỳ tới: {growth_pct:+.1f}%), trọng tâm chiến lược là {intel['focus']}. "
            f"{known_hint + ' ' if known_hint else ''}"
            f"Đặt trong tương quan cạnh tranh trực tiếp với {', '.join(peers[:5])}, đơn vị cần tối ưu hóa {intel['offer']}."
        ),
        "opportunities": [
            intel["market_gap"],
            f"Tận dụng xu hướng tăng trưởng ({growth_pct:+.1f}%) để mở rộng tiếp cận nhóm {intel['audience']}.",
            f"Gia tăng lợi thế cạnh tranh so với nhóm đối sánh ({', '.join(peers[:3])}) thông qua chuẩn hóa {intel['offer']}.",
        ],
        "risks": [r[1] for r in intel["risks_tuples"]],
        "target_segment": f"🎯 {intel['audience']}.",
        "product_strategy": f"📦 Tập trung nâng chuẩn {intel['offer']}; kiểm soát chất lượng đồng nhất và tạo khác biệt rõ nét so với {', '.join(peers[:3])}.",
        "pricing_strategy": f"💰 {intel['pricing_reason']}",
        "marketing_strategy": f"📢 Tập trung thông điệp làm rõ {intel['offer']}, triển khai đo lường chuyển đổi thực tế theo tuần và tối ưu chi phí thu hút trên từng nhóm đối tượng.",
        "distribution_strategy": f"🚚 Tối ưu hóa hệ thống kênh tiếp cận trọng điểm: {intel['channels']}.",
        "recommended_action": f"🚀 TRỌNG TÂM THỰC THI CHO {product_name.upper()}: Ưu tiên {intel['focus']}, kiểm soát chặt các chỉ số hiệu quả đơn vị trước khi mở rộng quy mô.",
        "action_plan_30_60_90": intel["action_plan"],
        "specific_kpis": intel["kpis"],
    }
    _AI_SYNTHESIS_CACHE[cache_key] = result
    return result


def ask_market_ai(
    product_name: str,
    category: str,
    question: str,
    potential_score: Optional[int] = None,
    growth_pct: Optional[float] = None,
    web_sources: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Interactive AI Q&A powered by `gemini-3.8-flash` & `gemini-3.5-flash-lite` to answer user questions
    about the analyzed keyword/entity using live web evidence and ML metrics.
    """
    q_text = (question or "").strip()
    score_text = f'{potential_score}/100' if potential_score is not None else 'chưa được cung cấp'
    growth_text = f'{growth_pct:+.1f}%' if growth_pct is not None else 'chưa được cung cấp'
    snippets = [f"- [{s.get('provider', 'Web')}] {s.get('title', '')}: {s.get('excerpt', '')[:160]}" for s in (web_sources or [])[:5]]
    context_str = "\n".join(snippets) if snippets else "Chưa có tài liệu nguồn kèm theo. Không tự tạo số liệu hoặc coi chỉ tiêu người dùng gửi là đã xác minh."

    if is_ai_configured() and q_text:
        prompt = (
            f"Bạn là trợ lý MarketWiseJu của nền tảng MarketWise.\n"
            f"Đối tượng đang phân tích: \"{product_name}\" (Ngành: {category}, Điểm tiềm năng: {score_text}, Tăng trưởng dự báo: {growth_text}).\n"
            f"Dữ liệu nguồn Web uy tín:\n{context_str}\n\n"
            f"Câu hỏi của người dùng: \"{q_text}\"\n\n"
            f"Hãy trả lời ngắn gọn, sắc bén, có số liệu dẫn chứng và đề xuất hành động cụ thể bằng tiếng Việt. "
            f"Trả về DUY NHẤT JSON: {{\"answer\": \"<câu trả lời chi tiết 3-5 câu>\", \"key_points\": [\"<ý chính 1>\", \"<ý chính 2>\", \"<ý chính 3>\"]}}"
        )
        parsed, model_label = call_gemini_json(prompt, timeout=8.0, preferred_model="gemini-3.6-flash")
        if parsed and parsed.get("answer"):
            return {
                "query": product_name,
                "product_name": product_name,
                "question": q_text,
                "answer": str(parsed["answer"]),
                "key_points": [str(x) for x in (parsed.get("key_points") or [])[:4]],
                "action_item": str(parsed.get("action_item") or f"Tập trung nâng cao năng lực cạnh tranh cốt lõi và chuyển đổi số cho {product_name}."),
                "confidence_pct": None,
                "model_used": model_label or "gemini-3.6-flash",
                "routing_model": None,
            }

    peers = get_domain_peers(product_name, category)
    return {
        "query": product_name,
        "product_name": product_name,
        "question": q_text,
        "answer": (
            f"Chưa tạo được câu trả lời AI cho câu hỏi về '{product_name}'. Đây là gợi ý theo quy tắc để tiếp tục kiểm tra. "
            f"Chỉ tiêu được cung cấp: điểm tiềm năng {score_text}, tăng trưởng {growth_text}. "
            "Cần đối chiếu số liệu với đúng đối tượng, nguồn và kỳ đo trước khi chọn chiến lược."
        ),
        "key_points": [
            f"Chỉ tiêu đầu vào: điểm tiềm năng {score_text}; tăng trưởng {growth_text}.",
            f"Gợi ý đối sánh cần kiểm tra mức phù hợp: {', '.join(peers[:4])}.",
            "Bổ sung dẫn chứng cụ thể cho câu hỏi; thử nghiệm phương án ở quy mô nhỏ trước khi mở rộng.",
        ],
        "action_item": f"Bổ sung dữ liệu có nguồn cho '{product_name}' và kiểm tra lại câu hỏi trước khi quyết định.",
        "confidence_pct": None,
        "model_used": "rule_based_advisor",
        "routing_model": None,
    }
