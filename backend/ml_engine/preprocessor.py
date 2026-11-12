import pandas as pd
import numpy as np
from typing import Dict, Any, Optional

class DataPreprocessor:
    """
    Data Preprocessing & Feature Engineering Module
    Xử lý làm sạch, điền dữ liệu khuyết, mã hóa và chuẩn hóa ma trận đặc trưng.
    Đảm bảo LUÔN có tập đặc trưng hợp lệ cho mọi loại dataset.
    """

    @classmethod
    def clean_and_prepare(cls, df: pd.DataFrame, roles: Dict[str, Optional[str]]) -> pd.DataFrame:
        df_clean = df.copy()

        # 1. Loại bỏ duplicate
        df_clean = df_clean.drop_duplicates().reset_index(drop=True)

        # 2. Xử lý Missing values
        for col in df_clean.columns:
            if df_clean[col].isnull().sum() > 0:
                if np.issubdtype(df_clean[col].dtype, np.number):
                    median_val = df_clean[col].median()
                    df_clean[col] = df_clean[col].fillna(median_val if not np.isnan(median_val) else 0)
                else:
                    mode_val = df_clean[col].mode()
                    fill_val = mode_val[0] if not mode_val.empty else "Unknown"
                    df_clean[col] = df_clean[col].fillna(fill_val)

        # 3. Sắp xếp theo chuỗi thời gian nếu có cột thời gian
        date_col = roles.get("date_col")
        sort_col = "Date" if ("Date" in df_clean.columns and date_col != "Date") else date_col
        if sort_col and sort_col in df_clean.columns:
            try:
                raw_dates = df_clean[sort_col].astype(str).str.replace(r"^Q([1-4])[-\s]*(\d{4})$", r"\2-Q\1", regex=True)
                df_clean["_parsed_date"] = pd.to_datetime(raw_dates, errors="coerce", format="mixed")
                if df_clean["_parsed_date"].notnull().sum() > len(df_clean) * 0.7:
                    df_clean = df_clean.sort_values(by="_parsed_date", kind="mergesort").reset_index(drop=True)
                else:
                    df_clean["_sort_str"] = raw_dates
                    df_clean = df_clean.sort_values(by="_sort_str", kind="mergesort").drop(columns=["_sort_str"], errors="ignore").reset_index(drop=True)
                df_clean = df_clean.drop(columns=["_parsed_date"], errors="ignore")
            except Exception:
                try:
                    df_clean["_parsed_date"] = pd.to_datetime(df_clean[sort_col], errors="coerce")
                    if df_clean["_parsed_date"].notnull().sum() > len(df_clean) * 0.7:
                        df_clean = df_clean.sort_values(by="_parsed_date", kind="mergesort").reset_index(drop=True)
                    df_clean = df_clean.drop(columns=["_parsed_date"], errors="ignore")
                except Exception:
                    pass

        return df_clean

    @classmethod
    def extract_features(
        cls, 
        df: pd.DataFrame, 
        roles: Dict[str, Optional[str]],
        product_name: Optional[str] = None,
        web_signal_score: Optional[int] = None,
        peer_names: Optional[list] = None,
        allow_fallback_entity: bool = False
    ) -> Dict[str, Any]:
        """
        Trích xuất các tập đặc trưng (X) và biến mục tiêu (y) cho:
        - Regression (Linear Regression / Ridge): Cô lập chuỗi thời gian của sản phẩm được chọn để chống nhiễu đa sản phẩm
        - Classification (Logistic Regression, Decision Tree)
        - Clustering (K-Means)

        Đảm bảo LUÔN trả về feature lists hợp lệ, không rỗng và phân tích chính xác cho mọi từ khóa.
        """
        df_clean = cls.clean_and_prepare(df, roles)
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()

        # ── Tạo Time_Step nếu cần (luôn có ít nhất 1 feature) ───────────────
        if "Time_Step" not in df_clean.columns:
            df_clean["Time_Step"] = np.arange(1, len(df_clean) + 1, dtype=float)

        # Cập nhật sau khi thêm Time_Step
        numeric_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()

        # ── Target cho Regression: Sales/Demand hoặc Cột số đầu tiên ────────
        target_reg_col = roles.get("sales_col")
        excluded_reg_targets = {"month", "date", "year", "period", "time_step", "index", "id"}
        if roles.get("date_col"):
            excluded_reg_targets.add(roles["date_col"].lower())

        valid_targets = [c for c in numeric_cols if c.lower() not in excluded_reg_targets]

        if not target_reg_col or target_reg_col not in numeric_cols or target_reg_col.lower() in excluded_reg_targets:
            target_reg_col = valid_targets[0] if valid_targets else numeric_cols[0]

        # ── Tự động tính tốc độ tăng trưởng kỳ-trên-kỳ nếu chưa có cột growth ─
        if (not roles.get("growth_col") or roles.get("growth_col") not in df_clean.columns) and target_reg_col in df_clean.columns:
            pct = pd.to_numeric(df_clean[target_reg_col], errors="coerce").pct_change().replace([np.inf, -np.inf], 0.0).fillna(0.0) * 100.0
            df_clean["Growth_Rate_Derived"] = np.round(np.clip(pct, -100.0, 300.0), 2)
            roles["growth_col"] = "Growth_Rate_Derived"
            numeric_cols = df_clean.select_dtypes(include=[np.number]).columns.tolist()

        # ── Regression features: tất cả cột số trừ target và date index ────
        reg_feature_cols = [
            c for c in numeric_cols 
            if c != target_reg_col and c.lower() not in ["month", "year", "date", "period"]
        ]
        if not reg_feature_cols:
            if "Time_Step" not in df_clean.columns:
                df_clean["Time_Step"] = np.arange(1, len(df_clean) + 1, dtype=float)
            reg_feature_cols = ["Time_Step"]

        # ── Cô lập chuỗi thời gian cho sản phẩm cụ thể & hiệu chỉnh từ khóa mới ──
        df_reg = df_clean.copy()
        item_col = roles.get("item_col")
        if item_col and item_col in df_clean.columns:
            unique_items = df_clean[item_col].dropna().unique().tolist()
            if len(unique_items) >= 1:
                target_item = None
                if product_name:
                    from services.research import normalize
                    norm_p = normalize(product_name)
                    target_item = next((itm for itm in unique_items if normalize(itm) == norm_p), None)
                    if not target_item and allow_fallback_entity:
                        target_item = next(
                            (itm for itm in unique_items if norm_p and (norm_p in normalize(itm) or normalize(itm) in norm_p)),
                            None
                        )
                        if not target_item and len(unique_items) == 1:
                            target_item = unique_items[0]

                if target_item:
                    sub_item_df = df_clean[df_clean[item_col] == target_item].copy()
                    other_df = df_clean[df_clean[item_col] != target_item].copy()
                    if len(sub_item_df) < 4:
                        raise ValueError('Đối tượng đã chọn cần ít nhất 4 quan sát riêng để dự báo. Không dùng quan sát của đối tượng khác thay thế.')
                    if len(sub_item_df) >= 4:
                        if len(other_df) > 0:
                            date_c = "Date" if "Date" in df_clean.columns else roles.get("date_col")
                            if date_c and date_c in df_clean.columns:
                                df_clean["_is_target"] = (df_clean[item_col] == target_item).astype(int)
                                df_clean["_d_key"] = df_clean[date_c].astype(str).str.replace(r"^Q([1-4])[-\s]*(\d{4})$", r"\2-Q\1", regex=True)
                                df_clean = (
                                    df_clean.sort_values(by=["_d_key", "_is_target"], kind="mergesort")
                                    .drop(columns=["_is_target", "_d_key"], errors="ignore")
                                    .reset_index(drop=True)
                                )
                            else:
                                df_clean = pd.concat([other_df, sub_item_df], ignore_index=True)
                            df_clean["Time_Step"] = (df_clean.groupby(item_col).cumcount() + 1).astype(float)
                        sub_item_df["Time_Step"] = np.arange(1, len(sub_item_df) + 1, dtype=float)
                        df_reg = sub_item_df.reset_index(drop=True)
                        if len(other_df) > 0:
                            date_c = "Date" if "Date" in df_reg.columns else roles.get("date_col")
                            if date_c and date_c in df_reg.columns and date_c in other_df.columns:
                                peer_map = other_df.groupby(date_c)[target_reg_col].mean().to_dict()
                                df_reg["Sector_Demand_Index"] = np.round(
                                    df_reg[date_c].map(peer_map).ffill().bfill().fillna(0.0).astype(float), 4
                                )
                elif product_name and unique_items and not allow_fallback_entity:
                    raise ValueError('Đối tượng không có trong dữ liệu; không tạo hoặc đổi tên quan sát thay thế.')
                else:
                    df_clean["Time_Step"] = (df_clean.groupby(item_col).cumcount() + 1).astype(float)
                    df_reg = df_clean.copy()

        # ── Bổ sung đặc trưng trễ & động lượng cho dự báo chuỗi thời gian (df_reg) ──
        if len(df_reg) >= 8 and len(reg_feature_cols) >= 2 and target_reg_col in df_reg.columns:
            if item_col and item_col in df_reg.columns and df_reg[item_col].nunique() > 1:
                lag1_s = df_reg.groupby(item_col)[target_reg_col].shift(1).bfill()
                y_reg_vals = lag1_s.values.astype(float)
            else:
                y_raw = df_reg[target_reg_col].values.astype(float)
                first_lag = y_raw[0] - (y_raw[1] - y_raw[0]) if len(y_raw) > 1 else y_raw[0]
                y_reg_vals = np.r_[first_lag, y_raw[:-1]]
            df_reg["Lag_1_Demand"] = np.round(y_reg_vals, 4)
            if len(df_clean) == len(df_reg):
                df_clean["Lag_1_Demand"] = df_reg["Lag_1_Demand"].values
            growth_c = roles.get("growth_col")
            if growth_c and growth_c in df_reg.columns:
                g_vals = pd.to_numeric(df_reg[growth_c], errors="coerce").fillna(0.0).values.astype(float)
                df_reg["Momentum_Demand"] = np.round(y_reg_vals * (1.0 + g_vals / 100.0), 4)
                if len(df_clean) == len(df_reg):
                    df_clean["Momentum_Demand"] = df_reg["Momentum_Demand"].values
            for extra_c in ("Lag_1_Demand", "Sector_Demand_Index", "Momentum_Demand"):
                if extra_c in df_reg.columns and extra_c not in reg_feature_cols:
                    reg_feature_cols.append(extra_c)

        # ── Target cho Classification: Market Potential hoặc tự suy diễn ────
        target_clf_col = roles.get("target_col")
        if not target_clf_col or target_clf_col not in df_clean.columns:
            # Tự phân loại 3 mức dựa trên Growth hoặc Sales
            metric_for_class = roles.get("growth_col") or target_reg_col
            if metric_for_class and metric_for_class in df_clean.columns:
                series = df_clean[metric_for_class].dropna()
                q33 = series.quantile(0.33)
                q66 = series.quantile(0.66)

                def classify_row(v: float) -> str:
                    if v >= q66:
                        return "High"
                    elif v >= q33:
                        return "Medium"
                    else:
                        return "Low"

                df_clean["Market_Potential_Derived"] = (
                    df_clean[metric_for_class].apply(classify_row)
                )
                df_reg["Market_Potential_Derived"] = (
                    df_reg[metric_for_class].apply(classify_row) if metric_for_class in df_reg.columns else "Medium"
                )
                target_clf_col = "Market_Potential_Derived"
            else:
                df_clean["Market_Potential_Derived"] = "Medium"
                df_reg["Market_Potential_Derived"] = "Medium"
                target_clf_col = "Market_Potential_Derived"

        # ── Features cho Clustering ──────────────────────────────────────────
        cluster_feature_cols = [c for c in numeric_cols if c not in ("Time_Step", target_reg_col, "Month", "Date", "period")]
        if len(cluster_feature_cols) < 2:
            cluster_feature_cols = [c for c in numeric_cols if c not in ("Time_Step", "Month", "Date", "period")]
        if len(cluster_feature_cols) < 2:
            cluster_feature_cols = numeric_cols if len(numeric_cols) >= 2 else numeric_cols + ["Time_Step"]

        cluster_feature_cols = list(dict.fromkeys(cluster_feature_cols))

        return {
            "df_clean":            df_clean,
            "df_reg":              df_reg,
            "numeric_cols":        numeric_cols,
            "target_reg_col":      target_reg_col,
            "reg_feature_cols":    reg_feature_cols,
            "target_clf_col":      target_clf_col,
            "cluster_feature_cols": cluster_feature_cols
        }
