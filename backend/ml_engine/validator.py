import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class DataValidator:
    """
    Data Quality Validation Engine
    Kiểm tra chất lượng dữ liệu, phát hiện outlier, tính toán Data Quality Score thực tế.
    """

    @staticmethod
    def identify_column_roles(df: pd.DataFrame) -> Dict[str, Optional[str]]:
        """Tự động nhận diện vai trò của các cột trong DataFrame dựa trên tên và kiểu dữ liệu chuẩn xác cao."""
        columns = df.columns.tolist()
        col_lower = {c: c.lower() for c in columns}
        roles = {
            "sales_col": None,
            "price_col": None,
            "search_col": None,
            "rating_col": None,
            "growth_col": None,
            "competition_col": None,
            "date_col": None,
            "item_col": None,
            "target_col": None
        }

        # 1. Date / Time (Ưu tiên cột có chứa 'date', 'quarter', 'year', 'period')
        for orig_col, low in col_lower.items():
            if any(k in low for k in ["date", "quarter", "year", "period", "timestamp"]) and not any(k in low for k in ["growth", "sales", "order"]):
                roles["date_col"] = orig_col
                break
        if not roles["date_col"]:
            for orig_col, low in col_lower.items():
                if "month" in low and not any(k in low for k in ["enroll", "sale", "order", "unit", "user", "sub", "reg", "ship", "book"]):
                    roles["date_col"] = orig_col
                    break

        # 2. Item / Product Name - Ưu tiên cột tên cụ thể nhất, tránh category/type
        specific_item_kw = [
            "product_name", "item_name", "model_name", "course_title", "tool_name",
            "device_model", "ev_model", "property_project", "audio_device",
            "fintech_service", "logistics_service", "service_name", "product_type", "title", "model",
            "research_query", "subject_name", "entity_name"
        ]
        for kw in specific_item_kw:
            for orig_col, low in col_lower.items():
                if kw in low and "category" not in low:
                    roles["item_col"] = orig_col
                    break
            if roles["item_col"]:
                break

        if not roles["item_col"]:
            general_item_kw = ["name", "item", "product", "course", "device", "brand", "project", "entity", "observed_entity"]
            for kw in general_item_kw:
                for orig_col, low in col_lower.items():
                    if kw in low and "category" not in low and "type" not in low:
                        roles["item_col"] = orig_col
                        break
                if roles["item_col"]:
                    break

        num_cols_set = set(df.select_dtypes(include=[np.number]).columns)
        num_col_lower = {
            c: low for c, low in col_lower.items()
            if c in num_cols_set and c != roles["date_col"]
        }

        # 3. Sales / Demand / Volume (chỉ ánh xạ cột kiểu số)
        sales_kw = [
            "unit", "sold", "sales", "order", "shipped", "registration", "enrollment",
            "active_user", "subscriber", "transaction", "shipment", "booking", "consumption",
            "demand", "volume", "revenue", "value", "doanh_so", "gia_tri"
        ]
        for kw in sales_kw:
            for orig_col, low in num_col_lower.items():
                if kw in low and not any(k in low for k in ["search", "price", "churn", "growth", "discount", "index"]):
                    roles["sales_col"] = orig_col
                    break
            if roles["sales_col"]:
                break

        # 4. Price / Cost / Fee (chỉ ánh xạ cột kiểu số)
        price_kw = ["price", "cost", "msrp", "retail", "sub_usd", "ticket", "fee", "rate_usd", "avg_price"]
        for kw in price_kw:
            for orig_col, low in num_col_lower.items():
                if kw in low and not any(k in low for k in ["growth", "churn", "discount", "tax"]):
                    roles["price_col"] = orig_col
                    break
            if roles["price_col"]:
                break

        # 5. Search Interest / Trend (chỉ ánh xạ cột kiểu số)
        for orig_col, low in num_col_lower.items():
            if any(k in low for k in ["search", "trend_score", "interest", "google_trend"]):
                roles["search_col"] = orig_col
                break

        # 6. Rating / Quality (chỉ ánh xạ cột kiểu số)
        for orig_col, low in num_col_lower.items():
            if any(k in low for k in ["rating", "quality", "review", "score"]) and not any(k in low for k in ["trend", "competition"]):
                roles["rating_col"] = orig_col
                break

        # 7. Growth (YoY, MoM) (chỉ ánh xạ cột kiểu số)
        for orig_col, low in num_col_lower.items():
            if any(k in low for k in ["growth", "yoy", "mom", "change_pct"]):
                roles["growth_col"] = orig_col
                break

        # 8. Competition / Market Share (chỉ ánh xạ cột kiểu số)
        for orig_col, low in num_col_lower.items():
            if any(k in low for k in ["competition", "competitor", "market_share"]):
                roles["competition_col"] = orig_col
                break

        # 9. Target / Classification
        for orig_col, low in col_lower.items():
            if any(k in low for k in ["market_potential", "potential", "label", "class", "target"]):
                roles["target_col"] = orig_col
                break

        # Fallback cho numerical nếu chưa map được (LOẠI TRỪ cột date/month)
        excluded_from_sales = {"month", "date", "year", "day", "time_step", "index", "id"}
        if roles["date_col"]:
            excluded_from_sales.add(roles["date_col"].lower())

        num_cols = [
            c for c in df.select_dtypes(include=[np.number]).columns
            if c.lower() not in excluded_from_sales
        ]
        if not roles["sales_col"] and len(num_cols) > 0:
            roles["sales_col"] = num_cols[0]
        if not roles["price_col"] and len(num_cols) > 1:
            roles["price_col"] = num_cols[1]

        return roles

    @classmethod
    def validate_dataset(cls, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Kiểm định toàn bộ dataset và tính toán Data Quality Score thực tế (0 - 100)
        """
        total_rows = len(df)
        total_cols = len(df.columns)

        if 'review_status' in df.columns:
            return {
                'valid': False,
                'error': 'Đây là bảng trích nguồn nghiên cứu, chưa phải bộ dữ liệu dự báo. Hãy xác minh từng quan sát rồi chuẩn hóa thành bảng có chỉ tiêu, đơn vị và kỳ thời gian nhất quán.',
                'quality_score': 0, 'total_rows': total_rows, 'total_columns': total_cols,
            }
        
        if total_rows == 0:
            return {
                "valid": False,
                "error": "No data available for this analysis.",
                "quality_score": 0,
                "total_rows": 0,
                "total_columns": total_cols
            }

        # 1. Missing values
        missing_per_col = df.isnull().sum().to_dict()
        total_missing_cells = sum(missing_per_col.values())
        total_cells = total_rows * total_cols
        missing_pct = round((total_missing_cells / total_cells) * 100, 2)

        # 2. Duplicate rows
        duplicate_rows = int(df.duplicated().sum())
        duplicate_pct = round((duplicate_rows / total_rows) * 100, 2)

        # 3. Numeric & Categorical columns
        numeric_df = df.select_dtypes(include=[np.number])
        numeric_cols = numeric_df.columns.tolist()
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        
        # 4. Outlier Detection (IQR Method)
        outlier_details = {}
        total_outliers = 0
        for col in numeric_cols:
            series = df[col].dropna()
            if len(series) >= 4:
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers = series[(series < lower_bound) | (series > upper_bound)]
                count = len(outliers)
                total_outliers += count
                outlier_details[col] = {
                    "count": count,
                    "lower_bound": round(float(lower_bound), 2),
                    "upper_bound": round(float(upper_bound), 2),
                    "min": round(float(series.min()), 2),
                    "max": round(float(series.max()), 2),
                    "mean": round(float(series.mean()), 2),
                    "std": round(float(series.std()), 2) if len(series) > 1 else 0
                }

        outlier_pct = round((total_outliers / (total_rows * max(1, len(numeric_cols)))) * 100, 2)

        # 5. Data Quality Score calculation
        score = 100.0
        explanations = []

        # Missing values penalty
        if missing_pct == 0:
            explanations.append("Dữ liệu đầy đủ 100% không bị khuyết thiếu (Missing values = 0%).")
        else:
            penalty = min(30.0, missing_pct * 1.5)
            score -= penalty
            explanations.append(f"Có {missing_pct}% ô dữ liệu bị thiếu (Đã trừ {round(penalty, 1)} điểm).")

        # Duplicate penalty
        if duplicate_rows == 0:
            explanations.append("Không có dòng trùng lặp (Duplicate = 0%).")
        else:
            penalty = min(20.0, duplicate_pct * 2.0)
            score -= penalty
            explanations.append(f"Phát hiện {duplicate_rows} dòng trùng lặp ({duplicate_pct}%, Đã trừ {round(penalty, 1)} điểm).")

        # Outlier penalty
        if outlier_pct <= 3.0:
            explanations.append(f"Tỷ lệ ngoại lai tự nhiên {outlier_pct}% (Đạt chuẩn phân phối thị trường).")
        else:
            penalty = min(15.0, (outlier_pct - 3.0) * 0.8)
            score -= penalty
            explanations.append(f"Phát hiện {total_outliers} điểm dữ liệu ngoại lai ({outlier_pct}%, Đã trừ {round(penalty, 1)} điểm).")

        # Sample size check
        if total_rows < 15:
            score -= 15.0
            explanations.append(f"Kích thước mẫu nhỏ ({total_rows} dòng). Nên bổ sung thêm để tăng độ tin cậy mô hình.")
        elif total_rows >= 30:
            explanations.append(f"Kích thước mẫu phù hợp ({total_rows} quan sát thị trường).")

        # Feature sufficiency check
        if len(numeric_cols) < 3:
            score -= 15.0
            explanations.append(f"Dataset có ít đặc trưng số học ({len(numeric_cols)} cột), cần tối thiểu 3 cột số để chạy đầy đủ các mô hình ML.")
        else:
            explanations.append(f"Tập đặc trưng số học phong phú ({len(numeric_cols)} cột số: {', '.join(numeric_cols[:4])}).")

        final_score = int(max(0, min(100, round(score))))
        roles = cls.identify_column_roles(df)
        is_valid = len(numeric_cols) >= 2 and total_rows >= 5
        error_msg = None if is_valid else (
            "Required features are missing from this dataset." if len(numeric_cols) < 2
            else "Dataset requires at least 5 rows for statistical analysis."
        )

        return {
            "valid": is_valid,
            "error": error_msg,
            "quality_score": final_score,
            "total_rows": total_rows,
            "total_columns": total_cols,
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
            "missing_values_count": total_missing_cells,
            "missing_pct": missing_pct,
            "duplicate_rows_count": duplicate_rows,
            "duplicate_pct": duplicate_pct,
            "outlier_count": total_outliers,
            "outlier_pct": outlier_pct,
            "outlier_details": outlier_details,
            "column_roles": roles,
            "explanations": explanations,
            "sample_data": df.head(5).to_dict(orient="records")
        }
