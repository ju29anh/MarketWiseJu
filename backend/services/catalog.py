from contextlib import closing
from pathlib import Path
import os
import json
import unicodedata
import numpy as np
from typing import Optional, Dict, Tuple
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from core.config import DATASETS_DIR, UPLOADS_DIR, settings
from core.serialization import np_clean
from database import get_db_connection, get_dashboard_summary
from ml_engine.validator import DataValidator
from services.datasets import resolve_dataset, read_dataset

def remove_accents(input_str: str) -> str:
    """Loại bỏ dấu tiếng Việt để tìm kiếm không phân biệt dấu và chữ hoa thường."""
    if not input_str:
        return ""
    s = unicodedata.normalize('NFD', str(input_str))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.replace('đ', 'd').replace('Đ', 'D').lower().strip()

KEYWORD_MAP = [
    # 1. Technology & Gaming
    {"kw": ["gaming", "game", "choi game", "chơi game", "tro choi", "trò chơi", "esports", "esport",
             "game thủ", "game thu", "laptop", "notebook", "asus", "rog", "lenovo", "legion", "acer", "predator",
             "dell", "alienware", "msi", "rtx", "gpu", "cpu", "pc", "máy tính", "may tinh",
             "máy tính chơi game", "máy tính xách tay", "phần cứng", "linh kiện", "hardware",
             "macbook", "thinkpad", "hp", "gigabyte", "razer", "ps5", "playstation", "xbox",
             "nintendo", "steam", "bàn phím", "chuột gaming", "màn hình", "monitor", "nvidia",
             "amd", "intel", "bán dẫn", "chip", "semiconductor", "card đồ họa"],
     "dataset": "technology_gaming_laptops.csv", "category": "Technology & Gaming"},

    # 2. Smartphones & Mobile
    {"kw": ["iphone", "samsung", "galaxy", "android", "smartphone", "điện thoại", "dien thoai",
             "mobile", "xiaomi", "oppo", "vivo", "realme", "pixel", "oneplus", "flagship",
             "midrange", "tầm trung", "bẻ gập", "fold", "flip", "ios", "di động",
             "redmi", "poco", "honor", "huawei", "nokia", "ipad", "tablet", "máy tính bảng",
             "sạc dự phòng", "ốp lưng", "5g"],
     "dataset": "smartphones_market.csv", "category": "Smartphones & Mobile"},

    # 3. Audio & Consumer Electronics
    {"kw": ["tai nghe", "tai nghe bluetooth", "earphone", "headphone", "airpod", "airpods", "tws",
             "wireless earbuds", "sony wh", "bose", "jabra", "samsung buds", "loa", "loa bluetooth",
             "marshall", "jbl", "soundbar", "loa kéo", "âm thanh", "loa thông minh", "am thanh",
             "sennheiser", "harman kardon", "edifier", "anker soundcore", "micro", "karaoke"],
     "dataset": "consumer_electronics_audio.csv", "category": "Audio & Consumer Electronics"},

    # 4. Fashion & E-Commerce
    {"kw": ["thời trang", "thoi trang", "quần áo", "quan ao", "áo", "quần", "váy",
             "đầm", "hoodie", "streetwear", "fashion", "clothing", "apparel", "athleisure",
             "sneaker", "giày", "dép", "túi xách", "túi", "ví", "ecommerce", "shopee", "lazada",
             "zara", "uniqlo", "h&m", "nike", "adidas", "quần bò", "áo khoác",
             "tiktok shop", "tiki", "shein", "local brand", "coolmate", "routine", "ivymoda",
             "puma", "converse", "vans", "gucci", "louis vuitton", "hermes", "trang sức", "kính mắt"],
     "dataset": "fashion_apparel_trends.csv", "category": "Fashion & E-Commerce"},

    # 5. Food & Beverage
    {"kw": ["phở", "pho", "bún", "bun", "bún bò", "bun bo", "cơm", "com", "ẩm thực", "am thuc",
             "món ăn", "mon an", "nhà hàng", "nha hang", "quán ăn", "quan an", "cà phê", "ca phe",
             "coffee", "trà", "tra", "trà sữa", "tra sua", "đồ uống", "do uong", "beverage", "rtd",
             "matcha", "cold brew", "nitro", "nước ép", "sinh tố", "juice", "smoothie", "nước ngọt",
             "f&b", "starbucks", "highland", "highlands", "trung nguyên", "phúc long", "phuc long",
             "quán cà phê", "specialty coffee", "arabica", "robusta", "phê la", "phe la", "katinat",
             "the coffee house", "cộng cà phê", "cong ca phe", "gong cha", "koi the", "mixue",
             "ding tea", "tocotoco", "cheese coffee", "bánh mì", "banh mi", "cơm tấm", "lẩu",
             "haidilao", "gà rán", "kfc", "lotteria", "jollibee", "pizza", "pizza 4p", "ô long",
             "oolong", "cà phê muối", "trà đào", "trà vải", "bia", "heineken", "sabeco"],
     "dataset": "food_beverage_specialty_coffee.csv", "category": "Food & Beverage"},

    # 6. FMCG & Consumer Goods
    {"kw": ["mì tôm", "mi tom", "mì ăn liền", "mì gói", "hảo hảo", "omachi", "bút", "but", "bút bi",
             "but bi", "bút chì", "văn phòng phẩm", "van phong pham", "sách", "sach", "vở", "vo",
             "tập", "tap", "sữa", "sua", "sữa tươi", "vinamilk", "th true milk", "bánh kẹo", "snack",
             "tiêu dùng", "hàng tiêu dùng", "fmcg", "gia vị", "dầu ăn", "nước mắm", "xà phòng", "dầu gội",
             "bột giặt", "đồ ăn", "thực phẩm đóng gói", "bánh quy", "oreo", "red bull", "nước tăng lực",
             "masan", "acecook", "kokomi", "chinsu", "nam ngư", "unilever", "p&g", "nestle", "pepsi",
             "coca cola", "bách hóa xanh", "winmart", "siêu thị", "tạp hóa", "thiên long"],
     "dataset": "fmcg_packaged_goods.csv", "category": "FMCG & Consumer Goods"},

    # 7. Beauty & Skincare
    {"kw": ["skincare", "serum", "mỹ phẩm", "my pham", "kem", "kem chống nắng", "chống nắng",
             "sunscreen", "beauty", "makeup", "son", "son môi", "trang điểm", "dưỡng da",
             "moisturizer", "toner", "sữa rửa mặt", "centella", "niacinamide", "retinol",
             "vitamin c", "collagen", "loreal", "innisfree", "the ordinary", "dược mỹ phẩm",
             "romand", "3ce", "black rouge", "mac", "dior", "chanel", "maybelline", "cocoon",
             "la roche-posay", "cerave", "bioderma", "vichy", "paula choice", "obagi", "klairs",
             "anessa", "skin1004", "hasaki", "sociolla", "watsons", "guardian", "spa", "thẩm mỹ",
             "nước hoa", "perfume", "chăm sóc da", "làm đẹp"],
     "dataset": "beauty_skincare_products.csv", "category": "Beauty & Skincare"},

    # 8. Electric Vehicles
    {"kw": ["xe điện", "xe dien", "electric vehicle", "ev", "tesla", "vinfast", "ô tô", "o to",
             "car", "xe hơi", "xe hoi", "charging", "sạc xe", "trạm sạc", "byd", "hyundai ioniq",
             "kia ev", "xe xanh", "xe máy điện", "pin xe điện", "xe tự lái",
             "vf3", "vf 3", "vf5", "vf 5", "vf6", "vf 6", "vf7", "vf 7", "vf8", "vf 8", "vf9", "vf 9",
             "vfe34", "xanh sm", "gsm", "wuling", "dat bike", "yadea", "pega", "feliz", "klara",
             "ô tô điện", "hybrid", "toyota", "honda", "mazda", "ford", "mercedes", "bmw"],
     "dataset": "automotive_electric_vehicles.csv", "category": "Electric Vehicles"},

    # 9. Education & EdTech
    {"kw": ["khóa học", "khoa hoc", "course", "edtech", "học trực tuyến", "hoc truc tuyen",
             "online learning", "udemy", "coursera", "lập trình", "lap trinh", "programming",
             "coding", "ai course", "chứng chỉ", "certificate", "tiếng anh", "ielts", "stem",
             "e-learning", "giáo dục", "education", "đào tạo", "gia sư",
             "đại học", "dai hoc", "trường", "truong", "trường đại học", "cao đẳng", "học viện",
             "thủ dầu một", "thu dau mot", "tdmu", "bách khoa", "kinh tế", "sư phạm", "quốc gia",
             "fpt", "rmit", "hutech", "tôn đức thắng", "văn lang", "sinh viên", "tuyển sinh",
             "học phí", "học bổng", "university", "college", "school", "academy", "toeic", "du học"],
     "dataset": "education_edtech_courses.csv", "category": "Education & EdTech"},

    # 10. Healthcare & Fitness
    {"kw": ["smartwatch", "đồng hồ thông minh", "dong ho thong minh", "đồng hồ", "wearable",
             "fitness", "gym", "sức khỏe", "suc khoe", "healthcare", "apple watch", "garmin",
             "fitbit", "mi band", "heart rate", "nhịp tim", "vòng tay", "health tracker",
             "y tế", "thuốc", "dược phẩm", "bệnh viện", "thực phẩm chức năng", "chăm sóc sức khỏe",
             "long châu", "pharmacity", "an khang", "tâm anh", "vinmec", "medlatec", "vnvc",
             "vaccine", "vắc xin", "vitamin", "whey", "yoga", "pilates", "chạy bộ", "pickleball",
             "cầu lông", "thể thao", "nhà thuốc", "phòng khám", "nha khoa"],
     "dataset": "healthcare_fitness_wearables.csv", "category": "Healthcare & Fitness"},

    # 11. Smart Home & IoT
    {"kw": ["robot hút bụi", "robot vacuum", "roborock", "irobot", "nhà thông minh", "nha thong minh",
             "smart home", "iot", "camera an ninh", "camera wifi", "bóng đèn thông minh", "smart bulb",
             "khóa cửa thông minh", "cảm biến", "máy giặt", "tủ lạnh", "quạt thông minh", "nồi chiên không dầu",
             "gia dụng", "đồ gia dụng", "ecovacs", "dreame", "xiaomi home", "ezviz", "imou",
             "máy lọc không khí", "máy lọc nước", "karofi", "kangaroo", "sunhouse", "lock&lock",
             "philips", "panasonic", "daikin", "điều hòa", "máy lạnh"],
     "dataset": "smart_home_iot_devices.csv", "category": "Smart Home & IoT"},

    # 12. Digital Services & SaaS
    {"kw": ["saas", "phần mềm", "phan mem", "software", "cloud", "ai tool", "công cụ ai",
             "chatgpt", "openai", "notion", "slack", "figma", "canva", "digital service",
             "subscription", "thuê bao", "api", "platform", "dịch vụ số", "crm", "erp",
             "điện toán đám mây", "claude", "gemini", "copilot", "midjourney", "fpt software",
             "viettel", "vnpt", "vng", "zalo", "misa", "base.vn", "kiotviet", "sapo", "haravan",
             "aws", "azure", "google cloud", "an ninh mạng", "cybersecurity", "dữ liệu", "big data",
             "trí tuệ nhân tạo", "chuyển đổi số", "website", "hosting", "domain"],
     "dataset": "digital_services_saas.csv", "category": "Digital Services & SaaS"},

    # 13. Real Estate & Housing
    {"kw": ["bất động sản", "bat dong san", "bđs", "nhà đất", "nha dat", "căn hộ", "can ho",
             "chung cư", "chung cu", "đất nền", "dat nen", "biệt thự", "biet thu", "nhà phố",
             "vinhomes", "novaland", "proptech", "thuê nhà", "mua nhà", "đô thị", "dự án", "địa ốc",
             "ecopark", "masterise", "khang điền", "nam long", "đất xanh", "sungroup", "bất động sản công nghiệp",
             "nhà ở xã hội", "văn phòng cho thuê", "shophouse", "condotel", "quy hoạch", "xây dựng"],
     "dataset": "real_estate_proptech.csv", "category": "Real Estate & Housing"},

    # 14. Tourism & Hospitality
    {"kw": ["du lịch", "du lich", "khách sạn", "khach san", "tour", "vé máy bay", "ve may bay",
             "travel", "tourism", "resort", "nghỉ dưỡng", "homestay", "phú quốc", "đà nẵng",
             "nha trang", "đà lạt", "hạ long", "hàng không", "booking", "agoda", "vé tham quan",
             "du thuyền", "vietnam airlines", "vietjet", "bamboo airways", "traveloka", "klook",
             "vinpearl", "sun world", "sapa", "hội an", "huế", "vũng tàu", "phan thiết", "quy nhơn",
             "lữ hành", "visa", "khách quốc tế"],
     "dataset": "tourism_travel_hospitality.csv", "category": "Tourism & Hospitality"},

    # 15. FinTech & Digital Finance
    {"kw": ["fintech", "ví điện tử", "vi dien tu", "ngân hàng", "ngan hang", "ngân hàng số",
             "momo", "zalopay", "vnpay", "thanh toán", "thanh toan", "chuyển tiền", "thẻ tín dụng",
             "cho vay", "tài chính", "tai chinh", "chứng khoán", "cổ phiếu", "bảo hiểm", "đầu tư",
             "cake", "timo", "vietcombank", "techcombank", "mbbank", "vpbank", "acb", "bidv",
             "vietinbank", "tpbank", "vib", "hdbank", "ssi", "vndirect", "tcbs", "vnindex",
             "trái phiếu", "vàng", "vàng sjc", "bitcoin", "crypto", "lãi suất", "tỷ giá",
             "manulife", "prudential", "bảo việt"],
     "dataset": "fintech_digital_banking.csv", "category": "FinTech & Digital Finance"},

    # 16. Logistics & Supply Chain
    {"kw": ["logistics", "giao hàng", "giao hang", "vận chuyển", "van chuyen", "chuyển phát nhanh",
             "kho bãi", "kho van", "supply chain", "chuỗi cung ứng", "shopee express", "ghtk",
             "ghn", "dhl", "fedex", "vận tải", "bưu điện", "fulfillment", "chặng cuối", "last mile",
             "viettel post", "j&t", "ninja van", "grabexpress", "ahamove", "lalamove", "cảng biển",
             "xuất nhập khẩu", "hải quan", "container", "vận tải biển", "kho lạnh"],
     "dataset": "logistics_supply_chain.csv", "category": "Logistics & Supply Chain"}
]


def classify_corpus_to_market(query: str, corpus_text: str = "") -> Tuple[Dict[str, str], Optional[str]]:
    """
    Phân loại ngữ nghĩa kết hợp từ khóa truy vấn và nội dung văn bản thu thập từ Web/Wikipedia
    để xác định chính xác danh mục thị trường & bộ dữ liệu chuẩn cho mọi từ khóa bất kỳ.
    """
    mapping, matched_kw = find_best_market_mapping(query)
    if matched_kw:
        return mapping, matched_kw

    if not corpus_text or not corpus_text.strip():
        return mapping, None

    c_low = corpus_text.lower()
    c_no_acc = remove_accents(c_low)
    c_tokens = set(c_no_acc.split())

    best_mapping = None
    best_kw = None
    best_score = 0

    for item in KEYWORD_MAP:
        cat_score = 0
        top_kw_for_cat = None
        for kw in item["kw"]:
            k_low = kw.lower().strip()
            k_no_acc = remove_accents(k_low)
            if len(k_no_acc) < 3:
                continue
            if " " in k_no_acc:
                if k_low in c_low or k_no_acc in c_no_acc:
                    cat_score += 25 + len(k_no_acc)
                    if not top_kw_for_cat:
                        top_kw_for_cat = kw
            else:
                if k_no_acc in c_tokens:
                    cat_score += 12 + len(k_no_acc)
                    if not top_kw_for_cat:
                        top_kw_for_cat = kw
        if cat_score > best_score:
            best_score = cat_score
            best_mapping = {"dataset": item["dataset"], "category": item["category"]}
            best_kw = top_kw_for_cat

    if best_mapping and best_score >= 15:
        return best_mapping, best_kw

    try:
        from services.ai_engine import classify_query_with_ai
        ai_cls = classify_query_with_ai(query, corpus_text)
        if ai_cls and ai_cls.get("dataset") and ai_cls.get("category"):
            return {"dataset": ai_cls["dataset"], "category": ai_cls["category"]}, query
    except Exception:
        pass

    return mapping, matched_kw

_GENERIC_TOKENS = {
    "mot", "hai", "ba", "bon", "nam", "sau", "bay", "tam", "chin", "muoi",
    "dau", "nha", "khong", "may", "nuoc", "moi", "cao", "thap", "tot", "dep",
    "pro", "max", "plus", "ultra", "mini", "air", "new", "the", "and", "for",
    "with", "smart", "home", "viet", "nam", "thanh", "pho", "tinh", "quan"
}

def find_best_market_mapping(raw_query: str) -> Tuple[Dict[str, str], str]:
    """
    Ánh xạ từ khóa tìm kiếm sang danh mục & dataset phù hợp nhất với độ chính xác cao:
    - Loại bỏ dấu tiếng Việt (remove_accents)
    - Đối chiếu cụm từ đa từ chính xác (Phrase / Full-Subset Match) tránh nhiễu từ đơn lẻ
    - Cộng điểm tích lũy theo danh mục khi khớp nhiều từ khóa cùng ngành
    - Tìm kiếm trong danh sách sản phẩm thực tế của 16 file CSV
    - Fallback Universal có căn cứ (FMCG hoặc ngành phù hợp)
    """
    if not raw_query:
        return {"dataset": "fmcg_packaged_goods.csv", "category": "FMCG & Consumer Goods"}, raw_query

    q_low = raw_query.lower().strip()
    q_no_acc = remove_accents(q_low)
    q_tokens = set(q_low.split())
    q_tokens_no_acc = set(q_no_acc.split())

    best_mapping = None
    best_kw = None
    best_score = 0

    # 1. Tìm kiếm trong KEYWORD_MAP (chấm điểm theo cả từ khóa tốt nhất + điểm cộng dồn toàn ngành)
    for mapping in KEYWORD_MAP:
        cat_best_score = 0
        cat_best_kw = None
        cat_bonus = 0

        for kw in mapping["kw"]:
            k_low = kw.lower().strip()
            k_no_acc = remove_accents(k_low)
            k_tokens = set(k_low.split())
            k_tokens_no_acc = set(k_no_acc.split())

            score = 0
            if q_low == k_low or q_no_acc == k_no_acc:
                score = 150 + len(k_no_acc) * 2
            elif len(k_tokens_no_acc) >= 2:
                # Cụm từ nhiều từ: Phải chứa nguyên cụm từ hoặc toàn bộ các từ của cụm nằm trong câu truy vấn
                if k_low in q_low or k_tokens.issubset(q_tokens):
                    score = 95 + len(k_tokens) * 18 + len(k_no_acc)
                elif k_no_acc in q_no_acc or k_tokens_no_acc.issubset(q_tokens_no_acc):
                    score = 80 + len(k_tokens_no_acc) * 15 + len(k_no_acc)
                elif len(q_tokens_no_acc) >= 2 and q_tokens_no_acc.issubset(k_tokens_no_acc):
                    score = 65 + len(q_tokens_no_acc) * 12
            else:
                # Từ khóa đơn (1 từ): Phải khớp chính xác theo ranh giới token
                if k_low in q_tokens:
                    score = 75 + len(k_no_acc) * 2
                elif k_no_acc in q_tokens_no_acc and k_no_acc not in _GENERIC_TOKENS:
                    score = 60 + len(k_no_acc) * 2
                elif len(k_no_acc) >= 5 and len(q_no_acc) >= 5:
                    if k_low in q_low or k_no_acc in q_no_acc:
                        score = 35 + len(k_no_acc)

            if score > 0:
                cat_bonus += min(25, score // 4)
                if score > cat_best_score:
                    cat_best_score = score
                    cat_best_kw = kw

        total_cat_score = (cat_best_score + min(60, cat_bonus)) if cat_best_score > 0 else 0
        if total_cat_score > best_score:
            best_score = total_cat_score
            best_mapping = mapping
            best_kw = cat_best_kw

    # 2. Tìm kiếm trong tên sản phẩm/model thực tế trong 16 file CSV nếu chưa tìm thấy
    if not best_mapping or best_score < 50:
        with closing(get_db_connection()) as conn, conn:
            cursor = conn.cursor()
            cursor.execute("SELECT filename, category FROM datasets")
            all_ds_rows = cursor.fetchall()

        for r in all_ds_rows:
            fpath = os.path.join(DATASETS_DIR, r["filename"])
            if os.path.exists(fpath):
                try:
                    df_sample = read_dataset(Path(fpath))
                    for col in df_sample.columns:
                        if any(k in col.lower() for k in ["name", "item", "product", "model", "title", "service", "device", "course"]):
                            for item_val in df_sample[col].dropna().astype(str).unique():
                                itm_low = item_val.lower().strip()
                                itm_no_acc = remove_accents(itm_low)
                                itm_tokens = {t for t in itm_no_acc.split() if len(t) >= 3 and t not in _GENERIC_TOKENS}
                                meaningful_q_tokens = {t for t in q_tokens_no_acc if len(t) >= 3 and t not in _GENERIC_TOKENS}
                                itm_score = 0

                                if q_no_acc == itm_no_acc:
                                    itm_score = 120
                                elif len(q_no_acc) >= 5 and (q_no_acc in itm_no_acc or itm_no_acc in q_no_acc):
                                    itm_score = 85
                                elif meaningful_q_tokens and (meaningful_q_tokens & itm_tokens):
                                    overlap = meaningful_q_tokens & itm_tokens
                                    if len(overlap) >= 2 or any(len(tok) >= 5 for tok in overlap):
                                        itm_score = 45 + len(overlap) * 18

                                if itm_score > best_score:
                                    best_score = itm_score
                                    best_mapping = {"dataset": r["filename"], "category": r["category"]}
                                    best_kw = item_val
                except Exception:
                    pass

    # 3. Fallback Universal: Ghép vào FMCG & Consumer Goods
    if not best_mapping:
        best_mapping = {
            "dataset": "fmcg_packaged_goods.csv",
            "category": "FMCG & Consumer Goods"
        }
        best_kw = None

    return best_mapping, best_kw

def get_categories():
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories")
        categories = [dict(r) for r in cursor.fetchall()]
    return {"categories": categories}

def get_datasets():
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM datasets ORDER BY id ASC")
        datasets = [dict(r) for r in cursor.fetchall()]
    return {"datasets": datasets}

def search_market_data(q: Optional[str] = ""):
    query = q.strip().lower() if q else ""
    query_no_acc = remove_accents(query)
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM datasets")
        all_datasets = [dict(r) for r in cursor.fetchall()]
        cursor.execute("SELECT * FROM categories")
        all_categories = [dict(r) for r in cursor.fetchall()]

    if not query:
        return {
            "query": q,
            "matched_datasets": all_datasets,
            "matched_categories": all_categories,
            "matched_products": [],
            "smart_match": None,
            "suggestions": ["iPhone", "Gaming Laptop", "Tai nghe", "Skincare", "Tesla EV", "Cà phê", "Mì Hảo Hảo", "Bất động sản", "Khóa học AI", "Smartwatch", "Robot hút bụi", "SaaS"]
        }

    matched_ds = []
    seen_filenames = set()
    matched_products = []

    # 1. Tìm khớp trực tiếp trong title/category/source của dataset (cả có dấu và không dấu)
    for ds in all_datasets:
        text_corpus = f"{ds['title']} {ds['category']} {ds['source']} {ds['filename']} {ds.get('description','')}".lower()
        text_corpus_no_acc = remove_accents(text_corpus)
        if query in text_corpus or query_no_acc in text_corpus_no_acc:
            matched_ds.append(ds)
            seen_filenames.add(ds["filename"])

    matched_cats = [c for c in all_categories if (
        query in f"{c['name']} {c['name_vi']} {c.get('description','')}".lower() or
        query_no_acc in remove_accents(f"{c['name']} {c['name_vi']} {c.get('description','')}")
    )]

    # 2. Tìm kiếm trong các dòng sản phẩm thực tế của từng dataset CSV
    for ds in all_datasets:
        ds_file = os.path.join(DATASETS_DIR, ds["filename"])
        if not os.path.exists(ds_file):
            ds_file = os.path.join(UPLOADS_DIR, ds["filename"])
        if os.path.exists(ds_file):
            try:
                df_sample = read_dataset(Path(ds_file))
                name_cols = [c for c in df_sample.columns if any(
                    kw in c.lower() for kw in [
                        "product_name", "product", "name", "item", "model", "course",
                        "brand", "ev_model", "service", "project", "audio_device", "type"
                    ]
                )]
                for col in name_cols:
                    prods = df_sample[col].dropna().astype(str).unique()
                    for p in prods:
                        p_lower = p.lower()
                        p_no_acc = remove_accents(p)
                        if (query in p_lower or p_lower in query or
                            query_no_acc in p_no_acc or p_no_acc in query_no_acc):
                            matched_products.append({
                                "product_name": p,
                                "category": ds["category"],
                                "dataset_filename": ds["filename"],
                                "dataset_title": ds["title"]
                            })
                            if ds["filename"] not in seen_filenames:
                                matched_ds.append(ds)
                                seen_filenames.add(ds["filename"])
            except Exception:
                pass

    # 3. Smart Keyword Match — ánh xạ từ khóa tự nhiên và không dấu
    smart_match = None
    best_map, best_kw = find_best_market_mapping(raw_query=q)
    if best_map and best_kw:
        target_ds = next((d for d in all_datasets if d["filename"] == best_map["dataset"]), None)
        smart_match = {
            "matched_keyword": best_kw or q,
            "category": best_map["category"],
            "dataset_filename": best_map["dataset"],
            "dataset_title": target_ds["title"] if target_ds else best_map["dataset"],
            "display_text": f"Gợi ý ngành tham khảo cho '{q}'; chưa xác nhận dữ liệu riêng của đối tượng."
        }
        if target_ds and target_ds["filename"] not in seen_filenames:
            matched_ds.insert(0, target_ds)
            seen_filenames.add(target_ds["filename"])

    return {
        "query": q,
        "matched_datasets": matched_ds,
        "matched_categories": matched_cats,
        "matched_products": matched_products[:15],
        "smart_match": smart_match,
        "fallback_suggestion": None if matched_ds else {
            "text": "No verified dataset available for this category. Chưa có dữ liệu xác minh cho đối tượng này. Dùng Nghiên cứu & So sánh để tìm nguồn hoặc tải dữ liệu riêng.",
            "action": "upload"
        },
        "suggestions": ["iPhone", "Gaming Laptop", "Tai nghe", "Skincare", "Tesla EV", "Cà phê", "Mì Hảo Hảo", "Bất động sản", "Khóa học AI", "Smartwatch"]
    }

def get_dataset_products(filename: str):
    """Trả về danh sách sản phẩm thực tế có trong dataset CSV."""
    file_path = resolve_dataset(filename)
    try:
        df = read_dataset(file_path)
        roles = DataValidator.identify_column_roles(df)
        item_col = roles.get("item_col")
        if item_col and item_col in df.columns:
            products = [str(x) for x in df[item_col].dropna().unique().tolist()]
            return {"products": products, "item_col": item_col}
        return {"products": [], "item_col": None}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Không thể đọc dataset. Vui lòng chọn lại dữ liệu.")

_WIKI_CACHE: Dict[str, Optional[Dict]] = {}


def _fetch_wiki_summary(raw_query: str) -> Optional[Dict]:
    if not settings.enable_wikipedia or not raw_query:
        return None
    cache_key = raw_query.strip().lower()
    if cache_key in _WIKI_CACHE:
        return _WIKI_CACHE[cache_key]

    import urllib.request
    import urllib.parse
    from html import unescape
    import re

    summary = None
    for lang in ("vi", "en"):
        try:
            encoded = urllib.parse.quote(raw_query.replace(" ", "_"))
            url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            req = urllib.request.Request(url, headers={"User-Agent": "MarketWise/2.5"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                wiki_json = json.loads(resp.read().decode("utf-8"))
                if wiki_json.get("extract"):
                    summary = {
                        "title": wiki_json.get("title", raw_query),
                        "extract": wiki_json.get("extract", ""),
                        "page_url": wiki_json.get("content_urls", {}).get("desktop", {}).get("page", ""),
                        "thumbnail": wiki_json.get("thumbnail", {}).get("source", None)
                    }
                    break
        except Exception:
            try:
                search_url = f"https://{lang}.wikipedia.org/w/rest.php/v1/search/page?" + urllib.parse.urlencode({"q": raw_query, "limit": 1})
                req_s = urllib.request.Request(search_url, headers={"User-Agent": "MarketWise/2.5"})
                with urllib.request.urlopen(req_s, timeout=1.5) as resp_s:
                    s_data = json.loads(resp_s.read().decode("utf-8"))
                    pages = s_data.get("pages") or []
                    if pages:
                        p = pages[0]
                        excerpt = unescape(re.sub(r"<[^>]*>", "", str(p.get("excerpt") or ""))).strip()
                        key = str(p.get("key") or "")
                        if excerpt and key:
                            summary = {
                                "title": str(p.get("title") or raw_query),
                                "extract": excerpt,
                                "page_url": f"https://{lang}.wikipedia.org/wiki/{urllib.parse.quote(key, safe='')}",
                                "thumbnail": (p.get("thumbnail") or {}).get("url")
                            }
                            break
            except Exception:
                continue

    _WIKI_CACHE[cache_key] = summary
    return summary


def get_market_overview(q: str = ""):
    """
    Tóm tắt dữ liệu hiện có, phân biệt kết quả khớp với gợi ý ngành tham khảo:
    1. Ánh xạ từ khóa (tiếng Việt có dấu / không dấu / tiếng Anh / thương hiệu)
    2. Tích hợp ngữ cảnh từ Wikipedia/Web để phân loại chính xác mọi thương hiệu/từ khóa mới
    3. Đối soát dữ liệu thực tế từ 16 bộ dữ liệu chuẩn quốc tế
    4. Đảm bảo LUÔN có bộ dữ liệu hợp lệ (dataset_filename) để người dùng chạy mô hình Machine Learning ngay lập tức.
    """
    raw_query = q.strip() if q else ""
    query = raw_query.lower()
    query_no_acc = remove_accents(query)

    if not query:
        return {
            "query": q,
            "found": False,
            "source": None,
            "market_data": None,
            "wiki_summary": None,
            "suggestions": ["iPhone", "Gaming Laptop", "Tai nghe", "Skincare", "Tesla EV",
                            "Cà phê", "Mì Hảo Hảo", "Bất động sản", "Khóa học AI", "Smartwatch"]
        }

    from services.research_evidence import subject_context
    ctx = subject_context(raw_query)
    if ctx['category'] == 'Education & EdTech' and ctx.get('label') == 'Giáo dục đại học & tuyển sinh':
        return JSONResponse(content={'query': q, 'found': False, 'source': None, 'market_data': None,
            'wiki_summary': None, 'suggestions': [], 'notice': 'Trường đại học cần dữ liệu tuyển sinh và đào tạo riêng. Hãy mở Nghiên cứu & So sánh để tra cứu nguồn.'})

    # ─── BƯỚC 1: Tìm kiếm chính xác với find_best_market_mapping + ngữ cảnh Wiki & AI ──
    matched_mapping, matched_kw = find_best_market_mapping(raw_query)
    wiki_summary = _fetch_wiki_summary(raw_query)
    if not matched_kw:
        wiki_text = f"{wiki_summary.get('title', '')} {wiki_summary.get('extract', '')}" if wiki_summary else ""
        matched_mapping, matched_kw = classify_corpus_to_market(raw_query, wiki_text)

    # ─── BƯỚC 2: Kéo số liệu thống kê chuẩn xác từ file CSV ─────────────────────
    source_type = "csv_dataset" if matched_kw else ("wikipedia" if wiki_summary else "fallback_nearest")
    dataset_file = os.path.join(DATASETS_DIR, matched_mapping["dataset"])
    if not os.path.exists(dataset_file):
        dataset_file = os.path.join(UPLOADS_DIR, matched_mapping["dataset"])

    market_data = None

    # Lấy thông tin nguồn uy tín từ Database
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM datasets WHERE filename = ?", (matched_mapping["dataset"],))
        ds_row = cursor.fetchone()

    source_citation = (ds_row["source"] + ' (metadata chưa xác minh độc lập)') if ds_row else "Chưa xác minh nguồn"
    dataset_title = ds_row["title"] if ds_row else matched_mapping["dataset"]

    try:
        df = read_dataset(Path(dataset_file))
        roles = DataValidator.identify_column_roles(df)

        name_col = roles.get("item_col")
        orig_top_items = []
        matched_item = None
        if name_col and name_col in df.columns:
            orig_top_items = [str(x) for x in df[name_col].dropna().unique().tolist()]
            exact = df[name_col].fillna('').astype(str).map(remove_accents) == query_no_acc
            if exact.any():
                df = df.loc[exact].copy()
                matched_item = str(df[name_col].iloc[0])
            else:
                kw_no_acc = remove_accents(matched_kw) if matched_kw else ""
                for itm in orig_top_items:
                    itm_no_acc = remove_accents(itm)
                    if (query_no_acc and (query_no_acc in itm_no_acc or itm_no_acc in query_no_acc)) or (
                        kw_no_acc and (kw_no_acc in itm_no_acc or itm_no_acc in kw_no_acc)
                    ):
                        matched_item = itm
                        break

        price_col = roles.get("price_col")
        growth_col = roles.get("growth_col")
        rating_col = roles.get("rating_col")
        sales_col = roles.get("sales_col")

        # Top sản phẩm/mẫu trong dataset + Đưa sản phẩm khớp lên vị trí ưu tiên
        top_items = []
        if matched_item:
            top_items.append(matched_item)
        for itm in orig_top_items:
            if itm not in top_items and len(top_items) < 6:
                top_items.append(itm)

        target_product_name = matched_item or (orig_top_items[0] if orig_top_items else raw_query.title())

        # Giá trung bình & khoảng
        if price_col and price_col in df.columns and np.issubdtype(df[price_col].dtype, np.number):
            price_stats = {
                "avg": float(round(float(df[price_col].mean()), 2)),
                "min": float(round(float(df[price_col].min()), 2)),
                "max": float(round(float(df[price_col].max()), 2)),
                "currency": "VND" if 'vnd' in price_col.lower() else ('USD' if 'usd' in price_col.lower() else 'Chưa xác định đơn vị')
            }
        else:
            price_stats = None

        # Tăng trưởng trung bình
        avg_growth = None
        if growth_col and growth_col in df.columns:
            try:
                avg_growth = float(round(float(df[growth_col].mean()), 1))
            except Exception:
                avg_growth = None

        # Rating trung bình
        avg_rating = None
        if rating_col and rating_col in df.columns:
            try:
                avg_rating = float(round(float(df[rating_col].mean()), 1))
            except Exception:
                avg_rating = None

        # Tổng quy mô/nhu cầu
        total_sales = None
        if sales_col and sales_col in df.columns:
            try:
                total_sales = int(df[sales_col].sum())
            except Exception:
                total_sales = None

        # Phân bố tiềm năng
        potential_dist = {}
        target_col = roles.get("target_col")
        if target_col and target_col in df.columns:
            counts = df[target_col].value_counts().to_dict()
            total = len(df)
            potential_dist = {str(k): float(round(int(v) / total * 100, 1)) for k, v in counts.items()}

        market_data = {
            "category": matched_mapping["category"],
            "dataset_filename": matched_mapping["dataset"],
            "dataset_title": dataset_title,
            "source_citation": source_citation,
            "total_records": int(len(df)),
            "columns": [str(c) for c in df.columns],
            "top_items": top_items,
            "target_product_name": target_product_name,
            "custom_query_name": raw_query,
            "is_exact_product": bool(matched_item),
            "price_stats": price_stats,
            "avg_growth_pct": avg_growth,
            "avg_rating": avg_rating,
            "total_demand": total_sales,
            "market_potential_distribution": potential_dist,
            "matched_keyword": str(matched_kw) if matched_kw else raw_query,
            "description": (
                f"Dữ liệu thị trường ngành {matched_mapping['category']} dựa trên {int(len(df))} "
                f"bản ghi trong dataset; nguồn được khai báo: {source_citation}. "
                f"Thích hợp phân tích xu hướng tăng trưởng và chiến lược tiếp thị cho '{raw_query}'."
            )
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(404, 'Không đọc được dữ liệu thị trường. Hãy chọn dataset khác hoặc tải dữ liệu của bạn.')

    result = {
        "query": q,
        "found": True,
        "source": source_type,
        "market_data": market_data,
        "wiki_summary": wiki_summary,
        "suggestions": ["iPhone", "Gaming Laptop", "Tai nghe", "Skincare", "Tesla EV",
                        "Cà phê", "Mì Hảo Hảo", "Bất động sản", "Khóa học AI", "Smartwatch"]
    }
    return JSONResponse(content=np_clean(result))

def get_dashboard():
    return get_dashboard_summary()
