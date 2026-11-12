from contextlib import closing
import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from core.config import settings, DATASETS_DIR

DB_PATH = str(settings.database_path)

def get_db_connection():
    from pathlib import Path
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.cursor()

        # 1. Bảng Categories
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            name_vi TEXT NOT NULL,
            icon TEXT NOT NULL,
            description TEXT
        );
        """)

        # 2. Bảng Datasets
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            filename TEXT NOT NULL UNIQUE,
            filepath TEXT NOT NULL,
            source TEXT NOT NULL,
            total_rows INTEGER,
            quality_score INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 3. Bảng Analysis Sessions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_sessions (
            session_id TEXT PRIMARY KEY,
            product_name TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            dataset_name TEXT NOT NULL,
            quality_score INTEGER,
            potential_score INTEGER,
            potential_level TEXT,
            trend_direction TEXT,
            regression_metrics TEXT,
            classification_metrics TEXT,
            clustering_info TEXT,
            strategy_recommendation TEXT,
            raw_result_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        conn.commit()

        # Thêm dữ liệu mẫu ban đầu cho 16 Categories toàn diện
        initial_categories = [
            ("Technology & Gaming", "Công nghệ & Máy tính Gaming", "laptop", "Thị trường laptop gaming, phần cứng và thiết bị công nghệ cao."),
            ("Smartphones & Mobile", "Điện thoại & Thiết bị di động", "smartphone", "Thị trường smartphone flagship, tầm trung và thiết bị thông minh."),
            ("Fashion & E-Commerce", "Thời trang & May mặc", "shirt", "Thị trường thời trang streetwear, athleisure và thương mại điện tử."),
            ("Food & Beverage", "F&B & Đồ uống Đặc sản", "coffee", "Thị trường cà phê đặc sản, trà và thực phẩm đồ uống RTD."),
            ("Beauty & Skincare", "Mỹ phẩm & Chăm sóc sắc đẹp", "sparkles", "Thị trường serum, kem chống nắng và mỹ phẩm organic."),
            ("Electric Vehicles", "Xe điện & Ô tô thông minh", "car", "Thị trường xe điện EV, trạm sạc và phương tiện di chuyển xanh."),
            ("Education & EdTech", "Giáo dục & Khóa học Trực tuyến", "book", "Thị trường khóa học trực tuyến, chứng chỉ công nghệ và EdTech."),
            ("Healthcare & Fitness", "Sức khỏe & Thiết bị Wearable", "activity", "Thị trường đồng hồ thông minh, vòng theo dõi sức khỏe và gym tech."),
            ("Smart Home & IoT", "Nhà thông minh & Thiết bị IoT", "home", "Thị trường robot hút bụi, camera an ninh và thiết bị IoT gia đình."),
            ("Digital Services & SaaS", "Dịch vụ Số & Phần mềm SaaS", "cloud", "Thị trường phần mềm SaaS, công cụ AI và giải pháp năng suất số."),
            ("FMCG & Consumer Goods", "Hàng Tiêu Dùng & Thực Phẩm Nhanh", "shopping-bag", "Thị trường hàng tiêu dùng nhanh, thực phẩm đóng gói, mì ăn liền và đồ uống."),
            ("Real Estate & Housing", "Bất Động Sản & Đô Thị Thông Minh", "building", "Thị trường căn hộ, chung cư, nhà ở đô thị và dự án bất động sản."),
            ("Tourism & Hospitality", "Du Lịch & Khách Sạn Nghỉ Dưỡng", "plane", "Thị trường tour du lịch, vé máy bay, khách sạn nghỉ dưỡng và dịch vụ trải nghiệm."),
            ("FinTech & Digital Finance", "Công Nghệ Tài Chính & Ngân Hàng Số", "credit-card", "Thị trường ví điện tử, thanh toán số, ngân hàng số và ứng dụng đầu tư."),
            ("Logistics & Supply Chain", "Logistics & Chuỗi Cung Ứng", "truck", "Thị trường giao hàng chặng cuối, chuyển phát nhanh E-Commerce và kho vận fulfillment."),
            ("Audio & Consumer Electronics", "Thiết Bị Âm Thanh & Điện Tử", "headphones", "Thị trường tai nghe chống ồn, loa di động bluetooth và thiết bị âm thanh thông minh.")
        ]

        for cat_name, cat_vi, icon, desc in initial_categories:
            cursor.execute("""
            INSERT INTO categories (name, name_vi, icon, description)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET name_vi=excluded.name_vi, icon=excluded.icon, description=excluded.description
            """, (cat_name, cat_vi, icon, desc))

        # Thêm metadata cho 16 datasets chuẩn quốc tế
        initial_datasets = [
            ("Gaming Laptops Market 2024", "Technology & Gaming", "technology_gaming_laptops.csv", "datasets/technology_gaming_laptops.csv", "Gartner Research & IDC Worldwide PC Tracker 2024", 72, 96),
            ("Global Smartphone Trends 2023-2024", "Smartphones & Mobile", "smartphones_market.csv", "datasets/smartphones_market.csv", "IDC Worldwide Quarterly Mobile Tracker & Canalys 2024", 40, 97),
            ("Fashion E-Commerce Orders & Trends", "Fashion & E-Commerce", "fashion_apparel_trends.csv", "datasets/fashion_apparel_trends.csv", "McKinsey Global Fashion Index & Statista Consumer Insights", 48, 95),
            ("Specialty Coffee & RTD Beverage Market", "Food & Beverage", "food_beverage_specialty_coffee.csv", "datasets/food_beverage_specialty_coffee.csv", "Specialty Coffee Association (SCA) & USDA Economic Research", 48, 96),
            ("Skincare & Beauty Product Trends", "Beauty & Skincare", "beauty_skincare_products.csv", "datasets/beauty_skincare_products.csv", "Euromonitor International Cosmetics & L'Oréal Research 2024", 36, 95),
            ("Electric Vehicles Global Registrations", "Electric Vehicles", "automotive_electric_vehicles.csv", "datasets/automotive_electric_vehicles.csv", "EV-Volumes Global EV Data & BloombergNEF Automotive Outlook", 36, 96),
            ("Online Education & EdTech Courses", "Education & EdTech", "education_edtech_courses.csv", "datasets/education_edtech_courses.csv", "HolonIQ Global EdTech Intelligence & Coursera Skills Report", 36, 97),
            ("Smart Health & Fitness Wearables", "Healthcare & Fitness", "healthcare_fitness_wearables.csv", "datasets/healthcare_fitness_wearables.csv", "IDC Worldwide Wearables Tracker & Rock Health Report", 24, 96),
            ("Smart Home & IoT Consumer Devices", "Smart Home & IoT", "smart_home_iot_devices.csv", "datasets/smart_home_iot_devices.csv", "Statista IoT & Consumer Technology Association (CTA)", 24, 95),
            ("Digital Cloud SaaS & AI Services", "Digital Services & SaaS", "digital_services_saas.csv", "datasets/digital_services_saas.csv", "Bessemer Cloud Index & Gartner Enterprise Software Forecast", 24, 98),
            ("FMCG & Packaged Food Market", "FMCG & Consumer Goods", "fmcg_packaged_goods.csv", "datasets/fmcg_packaged_goods.csv", "Kantar Worldpanel & NielsenIQ Retail Measurement", 48, 96),
            ("Vietnam Real Estate & Urban Housing", "Real Estate & Housing", "real_estate_proptech.csv", "datasets/real_estate_proptech.csv", "CBRE Vietnam Market Outlook & JLL Global Research", 48, 95),
            ("Tourism, Hospitality & Travel Services", "Tourism & Hospitality", "tourism_travel_hospitality.csv", "datasets/tourism_travel_hospitality.csv", "UN Tourism (UNWTO) & VNAT National Tourism Report", 48, 96),
            ("Digital Banking & FinTech Ecosystem", "FinTech & Digital Finance", "fintech_digital_banking.csv", "datasets/fintech_digital_banking.csv", "McKinsey Global Payments & State Bank FinTech Monitor", 48, 97),
            ("E-Commerce Logistics & Express Delivery", "Logistics & Supply Chain", "logistics_supply_chain.csv", "datasets/logistics_supply_chain.csv", "World Bank Logistics Performance Index & Armstrong 3PL", 48, 96),
            ("Premium Audio & Wireless Electronics", "Audio & Consumer Electronics", "consumer_electronics_audio.csv", "datasets/consumer_electronics_audio.csv", "GfK Consumer Technology Market Tracker & IDC Audio Insights", 48, 97)
        ]

        for title, cat, fname, fpath, source, rows, q_score in initial_datasets:
            # Seed metadata from the bundled file, using the same validator as the UI.
            import pandas as pd
            from ml_engine.validator import DataValidator
            frame = pd.read_csv(DATASETS_DIR / fname)
            rows = len(frame)
            q_score = DataValidator.validate_dataset(frame)['quality_score']
            cursor.execute("SELECT id FROM datasets WHERE filename = ?", (fname,))
            existing = cursor.fetchone()
            if existing:
                cursor.execute("""
                UPDATE datasets SET title=?, category=?, filepath=?, source=?, total_rows=?, quality_score=?
                WHERE filename=?
                """, (title, cat, fpath, source, rows, q_score, fname))
            else:
                cursor.execute("""
                INSERT INTO datasets (title, category, filename, filepath, source, total_rows, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (title, cat, fname, fpath, source, rows, q_score))

        conn.commit()

def save_analysis_session(session_data: Dict[str, Any]):
    session_data.setdefault("created_at", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO analysis_sessions (
            session_id, product_name, category, description, dataset_name,
            quality_score, potential_score, potential_level, trend_direction,
            regression_metrics, classification_metrics, clustering_info,
            strategy_recommendation, raw_result_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_data["session_id"],
            session_data["product_name"],
            session_data["category"],
            session_data.get("description", ""),
            session_data["dataset_name"],
            session_data["quality_score"],
            session_data["potential_score"],
            session_data["potential_level"],
            session_data.get("trend_direction", "Increasing"),
            json.dumps(session_data.get("regression_metrics", {})),
            json.dumps(session_data.get("classification_metrics", {})),
            json.dumps(session_data.get("clustering_info", {})),
            json.dumps(session_data.get("strategy_recommendation", {})),
            json.dumps(session_data),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conn.commit()

def get_analysis_session_by_id(session_id: str) -> Optional[Dict[str, Any]]:
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.cursor()
        cursor.execute("SELECT raw_result_json, created_at FROM analysis_sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
    if row:
        payload = json.loads(row["raw_result_json"])
        payload.setdefault("created_at", row["created_at"])
        return payload
    return None

def get_dashboard_summary() -> Dict[str, Any]:
    with closing(get_db_connection()) as conn, conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as count FROM analysis_sessions")
        total_sessions = cursor.fetchone()["count"]

        cursor.execute("SELECT AVG(potential_score) as avg_score FROM analysis_sessions")
        avg_row = cursor.fetchone()
        avg_score = round(float(avg_row["avg_score"]), 1) if avg_row["avg_score"] is not None else 0.0

        cursor.execute("SELECT COUNT(*) as count FROM datasets")
        total_datasets = cursor.fetchone()["count"]

        cursor.execute("SELECT COUNT(*) as count FROM categories")
        total_categories = cursor.fetchone()["count"]

        cursor.execute("""
        SELECT session_id, product_name, category, potential_score, potential_level, trend_direction, created_at, raw_result_json
        FROM analysis_sessions ORDER BY rowid DESC LIMIT 6
        """)
        recent_sessions = []
        for row in cursor.fetchall():
            item = dict(row)
            saved = json.loads(item.pop("raw_result_json"))
            item["created_at"] = saved.get("created_at") or item["created_at"]
            recent_sessions.append(item)

    return {
        "total_sessions": total_sessions,
        "avg_market_potential": avg_score,
        "total_datasets": total_datasets,
        "total_categories": total_categories,
        "recent_sessions": recent_sessions
    }
