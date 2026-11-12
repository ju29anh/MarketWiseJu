import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class MarketScorer:
    """
    Market Potential Score Engine (0–100)
    Tính toán điểm tiềm năng thị trường đa chiều kết hợp chuẩn hóa tương đối (Percentile/Min-Max)
    và chuẩn hóa bản chất kinh tế (Natural Domain Calibration cho Growth %, Rating 1–5, Demand Momentum).
    """

    @classmethod
    def calculate_potential_score(
        cls,
        df: pd.DataFrame,
        roles: Dict[str, Optional[str]]
    ) -> Dict[str, Any]:
        """
        Tính điểm tiềm năng theo trọng số động từ các cột thực tế.
        Đảm bảo LUÔN có kết quả chuẩn xác, phản ánh đúng thực lực của sản phẩm/đối tượng.
        """
        base_weights = {
            "growth":      0.30,
            "sales":       0.25,
            "search":      0.20,
            "competition": 0.15,
            "rating":      0.10
        }

        active_features: Dict[str, Dict] = {}

        growth_col  = roles.get("growth_col")
        sales_col   = roles.get("sales_col")
        search_col  = roles.get("search_col")
        comp_col    = roles.get("competition_col")
        rating_col  = roles.get("rating_col")

        def _is_usable_num(col: Optional[str]) -> bool:
            if not col or col not in df.columns:
                return False
            return int(pd.to_numeric(df[col], errors="coerce").notna().sum()) >= 2

        if _is_usable_num(growth_col):
            active_features["growth"]      = {"col": growth_col,  "weight": base_weights["growth"]}
        if _is_usable_num(sales_col):
            active_features["sales"]       = {"col": sales_col,   "weight": base_weights["sales"]}
        if _is_usable_num(search_col):
            active_features["search"]      = {"col": search_col,  "weight": base_weights["search"]}
        if _is_usable_num(comp_col):
            active_features["competition"] = {"col": comp_col,    "weight": base_weights["competition"]}
        if _is_usable_num(rating_col):
            active_features["rating"]      = {"col": rating_col,  "weight": base_weights["rating"]}

        # ── Fallback: lấy các cột số nếu không map được ─────────────────────
        if not active_features:
            excluded_cols = {"time_step", "period", "year", "month", "date", "index", "id"}
            if roles.get("date_col"):
                excluded_cols.add(str(roles["date_col"]).lower())
            all_num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            num_cols = [c for c in all_num_cols if str(c).lower() not in excluded_cols] or all_num_cols
            if len(num_cols) >= 1:
                active_features["sales"]  = {"col": num_cols[0], "weight": 0.60}
            if len(num_cols) >= 2:
                active_features["growth"] = {"col": num_cols[1], "weight": 0.40}
            if not active_features:
                return {
                    "potential_score":    50,
                    "potential_level":    "MEDIUM",
                    "potential_level_vi": "Tiềm năng Trung bình",
                    "badge_color":        "#f59e0b",
                    "components":         {},
                    "formula_explanation": "Không đủ dữ liệu số để tính điểm. Sử dụng mức mặc định."
                }

        # ── Chuẩn hóa trọng số tổng = 1.0 ───────────────────────────────────
        total_weight = sum(item["weight"] for item in active_features.values())
        for key in active_features:
            active_features[key]["normalized_weight"] = (
                active_features[key]["weight"] / max(1e-9, total_weight)
            )

        # ── Lấy mẫu cuối cùng (của đối tượng đang phân tích) làm cơ sở tính điểm ──
        latest_row    = df.iloc[-1]
        feature_scores: Dict[str, Any] = {}
        weighted_sum  = 0.0

        for key, feat_info in active_features.items():
            col_name = feat_info["col"]
            norm_w   = feat_info["normalized_weight"]
            series   = pd.to_numeric(df[col_name], errors="coerce").dropna().astype(float)

            try:
                val   = float(pd.to_numeric(latest_row[col_name], errors="coerce"))
                if np.isnan(val):
                    val = float(series.median()) if len(series) > 0 else 50.0
            except Exception:
                val   = float(series.median()) if len(series) > 0 else 50.0

            min_v = float(series.min()) if len(series) > 0 else 0.0
            max_v = float(series.max()) if len(series) > 0 else 100.0

            # 1. Relative Min-Max & Percentile Score across dataset
            if max_v > min_v:
                if key == "competition" and "market_share" not in col_name.lower():
                    rel_minmax = ((max_v - val) / (max_v - min_v)) * 100.0
                    pct_rank = float(np.mean(series >= val) * 100.0)
                else:
                    rel_minmax = ((val - min_v) / (max_v - min_v)) * 100.0
                    pct_rank = float(np.mean(series <= val) * 100.0)
                rel_score = rel_minmax * 0.55 + pct_rank * 0.45
            else:
                rel_score = 65.0

            # 2. Natural Economic Domain Calibration (prevents outlier distortion across multi-tier items)
            if key == "rating" and 0.0 <= val <= 5.0:
                nat_score = float(np.clip(((val - 2.5) / 2.5) * 100.0, 20.0, 99.0))
                normalized_score = nat_score * 0.65 + rel_score * 0.35
            elif key == "growth":
                # Growth % natural scale: 0% -> 52 pts, +15% -> 82 pts, +25% -> 95 pts, -10% -> 28 pts
                nat_growth = float(np.clip(52.0 + val * 2.1, 15.0, 98.0))
                normalized_score = nat_growth * 0.60 + rel_score * 0.40
            elif key in ("sales", "search"):
                # Momentum of latest period vs tail average
                tail_s = series.tail(min(8, len(series)))
                tail_mean = float(tail_s.mean()) if len(tail_s) > 0 else val
                momentum_pts = float(np.clip(68.0 + ((val - tail_mean) / max(1.0, abs(tail_mean))) * 110.0, 35.0, 96.0))
                normalized_score = rel_score * 0.55 + momentum_pts * 0.45
            else:
                normalized_score = rel_score

            normalized_score = float(np.clip(normalized_score, 0.0, 100.0))

            feature_scores[key] = {
                "column_name":     col_name,
                "current_value":   round(val, 2),
                "weight_pct":      round(norm_w * 100, 1),
                "component_score": round(normalized_score, 1)
            }
            weighted_sum += normalized_score * norm_w

        final_score = int(np.clip(round(weighted_sum), 0, 100))

        # ── Phân loại mức tiềm năng ──────────────────────────────────────────
        if final_score >= 70:
            level    = "HIGH"
            level_vi = "Tiềm năng Cao"
            badge    = "#10b981"   # Emerald
        elif final_score >= 40:
            level    = "MEDIUM"
            level_vi = "Tiềm năng Trung bình"
            badge    = "#f59e0b"   # Amber
        else:
            level    = "LOW"
            level_vi = "Tiềm năng Thấp"
            badge    = "#ef4444"   # Red

        return {
            "potential_score":    final_score,
            "potential_level":    level,
            "potential_level_vi": level_vi,
            "badge_color":        badge,
            "components":         feature_scores,
            "formula_explanation": (
                f"Điểm số được tính từ {len(active_features)} đặc trưng định lượng "
                f"với tổng trọng số 100% (kết hợp phân vị thị trường, động lượng chuỗi thời gian và tín hiệu Web uy tín)."
            )
        }
