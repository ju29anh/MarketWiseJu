import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    ExtraTreesClassifier,
    AdaBoostClassifier,
)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.dummy import DummyClassifier
from sklearn.svm import SVC
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix
)
from sklearn.preprocessing import LabelEncoder, StandardScaler
from typing import Dict, Any, List


class MarketClassification:
    """
    Multi-Model Classification & Explainability Engine (9 Models)
    So sánh 9 mô hình phân loại (Logistic Regression, Decision Tree, Random Forest,
    Gradient Boosting, Extra Trees, AdaBoost, KNN, SVM, Gaussian Naive Bayes),
    trích xuất Confusion Matrix và Decision Rules giải thích (Explainability).
    """

    @staticmethod
    def _eval_classifier(y_true: np.ndarray, y_pred: np.ndarray, name: str, m_type: str) -> Dict[str, Any]:
        return {
            "name":      name,
            "accuracy":  round(float(accuracy_score(y_true, y_pred)), 4),
            "precision": round(float(precision_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
            "recall":    round(float(recall_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
            "f1_score":  round(float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 4),
            "type":      m_type
        }

    @classmethod
    def train_and_compare(
        cls,
        df: pd.DataFrame,
        target_col: str,
        feature_cols: List[str]
    ) -> Dict[str, Any]:
        n_samples = len(df)
        if n_samples < 5:
            raise ValueError(
                f"Không đủ mẫu dữ liệu ({n_samples}) để phân loại (Tối thiểu 5 mẫu)."
            )

        excluded_clf_cols = {"Lag_1_Demand", "Sector_Demand_Index", "Momentum_Demand", "Time_Step"}
        clean_cols = [c for c in feature_cols if c in df.columns and c not in excluded_clf_cols]
        if not clean_cols:
            clean_cols = [c for c in feature_cols if c in df.columns]
        feature_cols = clean_cols

        df_work = df[feature_cols].copy().astype(float)
        for pcol in ("Date", "Quarter", "Period", "Month", "date", "quarter", "period", "month"):
            if pcol in df.columns:
                n_periods = df[pcol].nunique()
                if 1 < n_periods <= n_samples // 2:
                    p_keys = df[pcol].astype(str)
                    for col_c in feature_cols:
                        g_mean = df_work[col_c].groupby(p_keys).transform("mean")
                        g_std = df_work[col_c].groupby(p_keys).transform("std").replace(0.0, 1.0).fillna(1.0)
                        df_work[col_c] = (df_work[col_c] - g_mean) / g_std
                    break

        X       = df_work.values.astype(float)
        raw_y   = df[target_col].astype(str).values

        le      = LabelEncoder()
        y       = le.fit_transform(raw_y)
        classes = [str(c) for c in le.classes_]

        # ── Time/Sequential Split 70% train / 30% test ──────────────────────
        split_idx = max(3, int(n_samples * 0.70))
        if split_idx >= n_samples:
            split_idx = n_samples - 1

        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]

        n_train_classes = len(np.unique(y_train))
        use_full_for_train = False  # Never include held-out rows in training.

        if use_full_for_train:
            X_fit, y_fit = X, y
        else:
            X_fit, y_fit = X_train, y_train

        has_test = len(X_test) > 0 and not use_full_for_train

        scaler         = StandardScaler()
        X_fit_scaled   = scaler.fit_transform(X_fit)
        X_all_scaled   = scaler.transform(X)
        X_test_scaled  = scaler.transform(X_test) if has_test else X_fit_scaled
        y_eval         = y_test if has_test else y_fit
        X_eval_raw     = X_test if has_test else X_fit

        # ── 1. Logistic Regression ───────────────────────────────────────────
        log_reg = LogisticRegression(max_iter=1000, solver="lbfgs", random_state=42)
        try:
            log_reg.fit(X_fit_scaled, y_fit)
            log_preds = log_reg.predict(X_test_scaled)
            y_eval_log = y_eval
        except Exception:
            log_reg = DummyClassifier(strategy="most_frequent")
            log_reg.fit(X_fit_scaled, y_fit)
            log_preds = log_reg.predict(X_test_scaled)
            y_eval_log = y_eval

        log_metrics = cls._eval_classifier(y_eval_log, log_preds, "Majority baseline" if isinstance(log_reg, DummyClassifier) else "Logistic Regression", "Linear Classifier")

        # ── 2. Decision Tree Classifier ──────────────────────────────────────
        tree_clf = DecisionTreeClassifier(max_depth=4, min_samples_leaf=1, random_state=42)
        tree_clf.fit(X_fit, y_fit)
        tree_preds = tree_clf.predict(X_eval_raw)
        tree_metrics = cls._eval_classifier(y_eval, tree_preds, "Decision Tree Classifier", "Tree-based Non-Linear")

        # ── 3–9. Các mô hình Phân loại hỗ trợ (Supporting Classification Ensemble) ──
        supporting_models: List[Dict[str, Any]] = [log_metrics, tree_metrics]
        n_neighbors_k = max(1, min(5, len(X_fit) - 1))
        extra_classifiers = [
            ("Random Forest Classifier", "Bagging Tree Ensemble", RandomForestClassifier(n_estimators=45, max_depth=5, random_state=42), False),
            ("Gradient Boosting Classifier", "Boosting Tree Ensemble", GradientBoostingClassifier(n_estimators=35, max_depth=3, random_state=42), False),
            ("Extra Trees Classifier", "Randomized Forest Ensemble", ExtraTreesClassifier(n_estimators=45, max_depth=5, random_state=42), False),
            ("AdaBoost Classifier", "Adaptive Boosting Ensemble", AdaBoostClassifier(n_estimators=35, random_state=42), False),
            ("K-Nearest Neighbors (KNN)", "Instance Similarity", KNeighborsClassifier(n_neighbors=n_neighbors_k), True),
            ("Support Vector Machine (SVC)", "RBF Kernel Hyperplane", SVC(kernel="rbf", probability=True, random_state=42), True),
            ("Gaussian Naive Bayes", "Probabilistic Bayes", GaussianNB(), True),
        ]

        latest_votes: List[str] = []
        for m_name, m_type, clf_inst, needs_scale in extra_classifiers:
            try:
                tr_x = X_fit_scaled if needs_scale else X_fit
                ev_x = X_test_scaled if needs_scale else X_eval_raw
                lat_x = X_all_scaled[-1].reshape(1, -1) if needs_scale else X[-1].reshape(1, -1)
                clf_inst.fit(tr_x, y_fit)
                preds = clf_inst.predict(ev_x)
                supporting_models.append(cls._eval_classifier(y_eval, preds, m_name, m_type))
                vote_lbl = str(le.inverse_transform(clf_inst.predict(lat_x))[0])
                latest_votes.append(vote_lbl)
            except Exception:
                continue

        # ── Confusion Matrix (mapped to known classes) ──────────────────────
        all_class_indices = list(range(len(classes)))
        label_names = classes
        if len(all_class_indices) <= 1:
            cm_list = [[int(len(y_eval))]]
        else:
            cm = confusion_matrix(y_eval, tree_preds, labels=all_class_indices)
            cm_list = cm.tolist()

        # ── Decision Tree Rules Extraction ───────────────────────────────────
        tree_rules_raw = export_text(tree_clf, feature_names=feature_cols)

        feature_importances: Dict[str, float] = {}
        for idx, feat in enumerate(feature_cols):
            feature_importances[feat] = round(float(tree_clf.feature_importances_[idx]), 4)

        sorted_features = sorted(feature_importances.items(), key=lambda x: x[1], reverse=True)

        human_rules = []
        for feat, imp in sorted_features:
            if imp > 0:
                human_rules.append({
                    "feature":        feat,
                    "importance_pct": round(imp * 100, 1),
                    "insight": (
                        f"Đặc trưng '{feat}' đóng góp {round(imp * 100, 1)}% vào "
                        f"việc phân loại mức tiềm năng thị trường. "
                        f"Đây là {'yếu tố then chốt' if imp > 0.3 else 'yếu tố bổ trợ'} "
                        f"trong tổ hợp 9 mô hình phân loại."
                    )
                })

        if not human_rules:
            human_rules.append({
                "feature":        feature_cols[0],
                "importance_pct": 0.0,
                "insight": (
                    "Chưa trích được yếu tố phân định có đóng góp đo được."
                )
            })

        # ── Dự đoán cho mẫu hiện tại (mẫu cuối cùng trong dataset) ─────────
        latest_sample    = X[-1].reshape(1, -1)
        latest_pred_tree = str(le.inverse_transform(tree_clf.predict(latest_sample))[0])
        latest_votes.append(latest_pred_tree)

        try:
            proba = tree_clf.predict_proba(latest_sample)
            latest_prob_tree = float(np.max(proba))
        except Exception:
            latest_prob_tree = 1.0

        best_clf = max(supporting_models, key=lambda item: item["f1_score"])

        return {
            "target_variable":               target_col,
            "classes":                       classes,
            "current_market_classification": latest_pred_tree,
            "classification_confidence":     round(latest_prob_tree * 100, 1),
            "best_classifier_name":          best_clf["name"],
            "models_comparison": [
                log_metrics,
                tree_metrics,
            ],
            "supporting_models": supporting_models,
            "confusion_matrix": {
                "labels": label_names,
                "matrix": cm_list
            },
            "feature_importances": feature_importances,
            "human_rules":         human_rules,
            "raw_tree_rules":      tree_rules_raw
        }
