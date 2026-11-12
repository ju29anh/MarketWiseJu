import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, AgglomerativeClustering, MiniBatchKMeans, Birch
from sklearn.mixture import GaussianMixture
from sklearn.ensemble import IsolationForest
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import Dict, Any, List, Optional


class MarketClustering:
    """
    Multi-Model Market & Product Segmentation Engine (6 Models)
    Phân nhóm sản phẩm/thị trường bằng K-Means, Mini-Batch K-Means, Agglomerative Hierarchical Clustering,
    Birch CF-Tree, Gaussian Mixture Model (GMM) và phát hiện ngoại lai bằng Isolation Forest.
    """

    @classmethod
    def fit_and_segment(
        cls,
        df: pd.DataFrame,
        feature_cols: List[str],
        n_clusters: int = 3,
        item_col: Optional[str] = None
    ) -> Dict[str, Any]:
        n_samples = len(df)
        if n_samples < 3:
            raise ValueError("Cần tối thiểu 3 mẫu để thực hiện phân cụm K-Means.")

        X = df[feature_cols].values.astype(float)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # ── Tự động tìm số cụm K tối ưu (Optimal K) tối đa hóa Silhouette Score ──
        candidate_ks = [k for k in [2, 3, 4] if 2 <= k < n_samples]
        if not candidate_ks:
            candidate_ks = [min(2, max(1, n_samples))]

        best_k = candidate_ks[0]
        best_labels = None
        best_sil = -2.0

        for k in candidate_ks:
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            cur_labels = km.fit_predict(X_scaled)
            if len(set(cur_labels)) > 1:
                try:
                    s = float(silhouette_score(X_scaled, cur_labels))
                except Exception:
                    s = 0.0
            else:
                s = 0.0
            if s > best_sil:
                best_sil = s
                best_k = k
                best_labels = cur_labels

        k_val = best_k
        labels = best_labels
        sil_score = float(np.clip(best_sil, -1.0, 1.0))

        # ── Huấn luyện 6 mô hình Phân cụm & Phát hiện Dị thường hỗ trợ ──
        supporting_models: List[Dict[str, Any]] = [
            {
                "name": "K-Means Clustering (Auto-Optimal K)",
                "type": "Centroid Partitioning",
                "silhouette_score": round(sil_score, 4),
                "clusters": int(k_val),
                "status": "Primary Active",
            }
        ]

        # 2. Mini-Batch K-Means
        try:
            mbk = MiniBatchKMeans(n_clusters=k_val, random_state=42, batch_size=max(6, min(32, n_samples)), n_init=5)
            mbk_labels = mbk.fit_predict(X_scaled)
            mbk_sil = float(silhouette_score(X_scaled, mbk_labels)) if len(set(mbk_labels)) > 1 else 0.0
            mbk_sil = float(np.clip(mbk_sil, -1.0, 1.0))
            supporting_models.append({
                "name": "Mini-Batch K-Means (Fast Centroid)",
                "type": "Stochastic Centroid",
                "silhouette_score": round(mbk_sil, 4),
                "clusters": int(k_val),
                "status": "Verified",
            })
        except Exception:
            pass

        # 3. Agglomerative Hierarchical Clustering
        try:
            agg = AgglomerativeClustering(n_clusters=k_val, linkage="ward")
            agg_labels = agg.fit_predict(X_scaled)
            agg_sil = float(silhouette_score(X_scaled, agg_labels)) if len(set(agg_labels)) > 1 else 0.0
            agg_sil = float(np.clip(agg_sil, -1.0, 1.0))
            supporting_models.append({
                "name": "Agglomerative Hierarchical Clustering",
                "type": "Ward Linkage Hierarchy",
                "silhouette_score": round(agg_sil, 4),
                "clusters": int(k_val),
                "status": "Verified",
            })
        except Exception:
            pass

        # 4. Birch CF-Tree Clustering
        try:
            birch = Birch(n_clusters=k_val, threshold=0.35)
            birch_labels = birch.fit_predict(X_scaled)
            birch_sil = float(silhouette_score(X_scaled, birch_labels)) if len(set(birch_labels)) > 1 else 0.0
            birch_sil = float(np.clip(birch_sil, -1.0, 1.0))
            supporting_models.append({
                "name": "BIRCH CF-Tree Clustering",
                "type": "Hierarchical Feature Tree",
                "silhouette_score": round(birch_sil, 4),
                "clusters": int(k_val),
                "status": "Verified",
            })
        except Exception:
            pass

        # 5. Gaussian Mixture Model (GMM Probabilistic Clustering)
        try:
            gmm = GaussianMixture(n_components=k_val, covariance_type="diag", random_state=42)
            gmm_labels = gmm.fit_predict(X_scaled)
            gmm_sil = float(silhouette_score(X_scaled, gmm_labels)) if len(set(gmm_labels)) > 1 else 0.0
            gmm_sil = float(np.clip(gmm_sil, -1.0, 1.0))
            supporting_models.append({
                "name": "Gaussian Mixture Model (GMM)",
                "type": "Probabilistic Soft Clustering",
                "silhouette_score": round(gmm_sil, 4),
                "clusters": int(k_val),
                "status": "Verified",
            })
        except Exception:
            pass

        # 6. Isolation Forest Anomaly Detection
        try:
            iso = IsolationForest(contamination=0.1, random_state=42)
            iso_preds = iso.fit_predict(X_scaled)
            inlier_ratio = float(np.mean(iso_preds == 1))
            supporting_models.append({
                "name": "Isolation Forest Anomaly Detector",
                "type": "Tree-based Outlier Detection",
                "silhouette_score": round(inlier_ratio, 4),
                "clusters": int(np.sum(iso_preds == -1)),
                "status": f"Chuẩn ổn định {round(inlier_ratio * 100, 1)}%",
            })
        except Exception:
            pass

        # 2D PCA projection for scatter chart
        n_pca_components = min(2, X_scaled.shape[1])
        pca   = PCA(n_components=n_pca_components, random_state=42)
        X_2d  = pca.fit_transform(X_scaled)
        if X_2d.shape[1] < 2:
            pad   = np.zeros((X_2d.shape[0], 2 - X_2d.shape[1]))
            X_2d  = np.hstack([X_2d, pad])

        # Tính trung bình đặc trưng theo từng cụm
        df_temp = df[feature_cols].copy().astype(float)
        df_temp["__Cluster__"] = labels
        cluster_means = df_temp.groupby("__Cluster__").mean()

        cluster_profiles = []
        for c_id in range(k_val):
            if c_id not in cluster_means.index:
                continue
            row_means    = cluster_means.loc[c_id].to_dict()
            cluster_count = int(np.sum(labels == c_id))
            cluster_pct  = round((cluster_count / n_samples) * 100, 1)

            summary_traits = []
            for col_name, val in row_means.items():
                col_avg = float(df[col_name].mean())
                if val > col_avg * 1.15:
                    summary_traits.append(f"High {col_name}")
                elif val < col_avg * 0.85:
                    summary_traits.append(f"Low {col_name}")
                else:
                    summary_traits.append(f"Moderate {col_name}")

            if any(
                "High" in t and any(kw in t.lower() for kw in ["unit", "sold", "sales", "order", "registration", "demand"])
                for t in summary_traits
            ):
                cluster_name = "Mass Market & High Volume"
                description  = "Phân khúc có quy mô lớn, độ phổ biến cao, yêu cầu năng lực vận hành và truyền thông mạnh mẽ."
                color        = "#0ea5e9"
            elif any(
                "High" in t and any(kw in t.lower() for kw in ["price", "cost", "retail", "fee"])
                for t in summary_traits
            ):
                cluster_name = "Premium & High Margin Niche"
                description  = "Phân khúc chất lượng cao, giá trị gia tăng lớn, đối tượng mục tiêu chú trọng uy tín và thương hiệu."
                color        = "#8b5cf6"
            elif any(
                "High" in t and any(kw in t.lower() for kw in ["search", "growth", "trend"])
                for t in summary_traits
            ):
                cluster_name = "Emerging & Rapid Growth"
                description  = "Phân khúc xu hướng đang tăng trưởng nhanh, nhiều cơ hội mở rộng quy mô cho đơn vị tiên phong."
                color        = "#10b981"
            else:
                cluster_name = f"Segment {c_id + 1}: Balanced Market"
                description  = "Phân khúc cân bằng về quy mô và chi phí, duy trì tính ổn định bền vững trong vận hành."
                color        = "#f59e0b"

            cluster_profiles.append({
                "cluster_id":      c_id,
                "cluster_name":    cluster_name,
                "sample_count":    cluster_count,
                "percentage":      cluster_pct,
                "description":     description,
                "color":           color,
                "feature_averages": {
                    col: round(float(val), 2) for col, val in row_means.items()
                }
            })

        scatter_points = []
        for i in range(n_samples):
            if item_col and item_col in df.columns:
                try:
                    item_title = str(df.iloc[i][item_col])
                except Exception:
                    item_title = f"Item {i + 1}"
            else:
                item_title = f"Item {i + 1}"

            c_id = int(labels[i])
            profile = next((p for p in cluster_profiles if p["cluster_id"] == c_id), None)
            c_name  = profile["cluster_name"] if profile else f"Cluster {c_id}"

            scatter_points.append({
                "id":           i,
                "name":         item_title,
                "cluster":      c_id,
                "cluster_name": c_name,
                "x":            round(float(X_2d[i, 0]), 3),
                "y":            round(float(X_2d[i, 1]), 3),
                "raw_values":   {
                    col: round(float(df.iloc[i][col]), 2)
                    for col in feature_cols[:4]
                }
            })

        current_cluster_id  = int(labels[-1])
        current_profile     = next(
            (p for p in cluster_profiles if p["cluster_id"] == current_cluster_id),
            cluster_profiles[0] if cluster_profiles else {
                "cluster_name": "Balanced Market",
                "description": "Phân khúc cân bằng."
            }
        )

        pca_variance = [round(float(v), 4) for v in pca.explained_variance_ratio_]
        if len(pca_variance) < 2:
            pca_variance.append(0.0)

        return {
            "model_name":        "K-Means Clustering",
            "supporting_models": supporting_models,
            "k_clusters":        k_val,
            "silhouette_score":  round(sil_score, 4),
            "features_used":     feature_cols,
            "cluster_profiles":  cluster_profiles,
            "current_item_cluster": {
                "cluster_id":   current_cluster_id,
                "cluster_name": current_profile["cluster_name"],
                "description":  current_profile["description"]
            },
            "scatter_points":     scatter_points,
            "pca_variance_ratio": pca_variance
        }
