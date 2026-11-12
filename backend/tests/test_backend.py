import os
import sys
import pandas as pd
import numpy as np
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from ml_engine.validator import DataValidator
from ml_engine.preprocessor import DataPreprocessor
from ml_engine.regression import MarketRegression
from ml_engine.classification import MarketClassification
from ml_engine.clustering import MarketClustering
from ml_engine.scoring import MarketScorer
from ml_engine.strategy_engine import StrategyEngine
from database import init_database, save_analysis_session, get_analysis_session_by_id, get_dashboard_summary
from main import search_market_data, app

def run_tests():
    print("=================================================================")
    print("       MARKETWISE COMPREHENSIVE VERIFICATION & TEST SUITE        ")
    print("=================================================================")
    init_database()

    datasets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets"))

    # ─────────────────────────────────────────────────────────────────────────
    # TEST SUITE 1: DATA VALIDATION & EDGE CASES
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- [TEST SUITE 1] Data Validation & Edge Cases ---")

    # 1.1 Empty CSV
    df_empty = pd.DataFrame()
    val_empty = DataValidator.validate_dataset(df_empty)
    assert val_empty["valid"] is False, "Empty dataframe should not be valid"
    assert val_empty["error"] == "No data available for this analysis."
    assert val_empty["quality_score"] == 0
    print("  [PASS 1.1] Empty Dataset handled: 'No data available for this analysis.'")

    # 1.2 Invalid CSV (No numeric features)
    df_invalid = pd.DataFrame({"Text_A": ["abc", "def", "ghi"], "Text_B": ["xyz", "uvw", "rst"]})
    val_invalid = DataValidator.validate_dataset(df_invalid)
    assert val_invalid["valid"] is False
    assert "Required features are missing" in val_invalid["error"]
    print("  [PASS 1.2] Invalid CSV (no numeric cols) handled: 'Required features are missing from this dataset.'")

    # 1.3 Small Dataset (< 5 rows)
    df_small = pd.DataFrame({"Price": [10, 20, 30], "Units": [100, 200, 300]})
    val_small = DataValidator.validate_dataset(df_small)
    assert val_small["valid"] is False
    print("  [PASS 1.3] Small Dataset (<5 rows) rejected for statistical validity")

    # 1.4 Dataset with Missing Values & Duplicates & Outliers
    df_messy = pd.DataFrame({
        "Price": [100.0, 105.0, 102.0, 101.0, 104.0, 103.0, np.nan, 1000.0, 100.0],
        "Units": [50.0, 52.0, 51.0, 50.0, 54.0, 53.0, 50.0, 5.0, 50.0],
        "Search": [10.0, 12.0, 11.0, 10.0, 13.0, 12.0, 11.0, 50.0, 10.0]
    })
    val_messy = DataValidator.validate_dataset(df_messy)
    assert val_messy["valid"] is True
    assert val_messy["missing_values_count"] > 0
    assert val_messy["duplicate_rows_count"] > 0
    assert val_messy["outlier_count"] > 0
    assert 0 <= val_messy["quality_score"] <= 100
    print(f"  [PASS 1.4] Messy data assessed correctly: Missing={val_messy['missing_pct']}%, Duplicates={val_messy['duplicate_rows_count']}, Outliers={val_messy['outlier_count']}, QualityScore={val_messy['quality_score']}/100")

    # ─────────────────────────────────────────────────────────────────────────
    # TEST SUITE 2: SEARCH & KEYWORD FUNCTIONALITY
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- [TEST SUITE 2] Search, Product & Keyword Functionality ---")

    # 2.1 Search by Category / Keyword (laptop)
    s_laptop = search_market_data("laptop")
    assert len(s_laptop["matched_datasets"]) > 0
    print(f"  [PASS 2.1] Search 'laptop': Found {len(s_laptop['matched_datasets'])} datasets (Direct match/Smart keyword)")

    # 2.2 Search by Specific Product Name in CSV (ROG Strix)
    s_product = search_market_data("ROG Strix")
    assert len(s_product["matched_products"]) > 0 or len(s_product["matched_datasets"]) > 0
    print(f"  [PASS 2.2] Search product 'ROG Strix': Matched across datasets")

    # 2.3 Search with Unmatched Query -> "No verified dataset available for this category."
    s_unknown = search_market_data("xyz999nonexistentitem")
    assert len(s_unknown["matched_datasets"]) == 0
    assert s_unknown["fallback_suggestion"] is not None
    assert "No verified dataset available for this category." in s_unknown["fallback_suggestion"]["text"]
    print("  [PASS 2.3] Unmatched Search: Returns 'No verified dataset available for this category.' with zero fake prediction")

    # ─────────────────────────────────────────────────────────────────────────
    # TEST SUITE 3: END-TO-END ML PIPELINE ON ALL 10 DATASETS
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- [TEST SUITE 3] End-to-End ML Pipeline on All 10 Datasets ---")

    all_dataset_files = [
        "technology_gaming_laptops.csv",
        "smartphones_market.csv",
        "fashion_apparel_trends.csv",
        "food_beverage_specialty_coffee.csv",
        "beauty_skincare_products.csv",
        "automotive_electric_vehicles.csv",
        "education_edtech_courses.csv",
        "healthcare_fitness_wearables.csv",
        "smart_home_iot_devices.csv",
        "digital_services_saas.csv"
    ]

    for fname in all_dataset_files:
        fpath = os.path.join(datasets_dir, fname)
        assert os.path.exists(fpath), f"File {fname} does not exist!"

        df = pd.read_csv(fpath)

        # 1. Validation
        val = DataValidator.validate_dataset(df)
        assert val["valid"] is True, f"Validation failed for {fname}"
        assert 0 <= val["quality_score"] <= 100

        # 2. Preprocessing & Feature Engineering
        roles = val["column_roles"]
        features = DataPreprocessor.extract_features(df, roles)
        df_clean = features["df_clean"]
        assert len(features["reg_feature_cols"]) >= 1

        # 3. Model 1: Linear Regression
        reg = MarketRegression.train_and_forecast(
            df=df_clean,
            target_col=features["target_reg_col"],
            feature_cols=features["reg_feature_cols"],
            date_col=roles.get("date_col"),
            forecast_horizon=7
        )
        assert "metrics" in reg
        assert "r2_score" in reg["metrics"]
        assert "mae" in reg["metrics"]
        assert "rmse" in reg["metrics"]
        assert len(reg["future_forecast"]) == 7
        assert reg["trend_direction"] in ["Increasing", "Decreasing"]

        # 4. Model 2 & 3: Logistic Regression & Decision Tree
        clf = MarketClassification.train_and_compare(
            df=df_clean,
            target_col=features["target_clf_col"],
            feature_cols=features["reg_feature_cols"]
        )
        assert len(clf["models_comparison"]) == 2
        assert "confusion_matrix" in clf
        assert "human_rules" in clf

        # 5. Model 4: K-Means Clustering
        clst = MarketClustering.fit_and_segment(
            df=df_clean,
            feature_cols=features["cluster_feature_cols"],
            n_clusters=3,
            item_col=roles.get("item_col")
        )
        assert "silhouette_score" in clst
        assert "current_item_cluster" in clst
        assert len(clst["cluster_profiles"]) >= 2

        # 6. Market Potential Score
        score_data = MarketScorer.calculate_potential_score(df_clean, roles)
        assert 0 <= score_data["potential_score"] <= 100
        assert score_data["potential_level"] in ["LOW", "MEDIUM", "HIGH"]

        # 7. Rule-Based Strategy Engine
        strat = StrategyEngine.generate_strategy(
            product_name="Product " + fname.split("_")[0].capitalize(),
            category=fname.replace(".csv", "").replace("_", " ").title(),
            potential_data=score_data,
            regression_data=reg,
            classification_data=clf,
            clustering_data=clst
        )
        assert "market_overview" in strat
        assert "trend_summary" in strat
        assert "opportunities" in strat and len(strat["opportunities"]) >= 2
        assert "risks" in strat and len(strat["risks"]) >= 1
        assert "target_segment" in strat
        assert "product_strategy" in strat
        assert "pricing_strategy" in strat
        assert "marketing_strategy" in strat
        assert "recommended_action" in strat

        # 8. Database Persistence Check
        test_session = {
            "session_id": f"test_{fname[:6]}_{abs(hash(fname)) % 10000}",
            "product_name": "Test " + fname.split("_")[0].capitalize(),
            "category": fname.replace(".csv", "").replace("_", " ").title(),
            "description": "Comprehensive Test",
            "dataset_name": fname,
            "quality_score": val["quality_score"],
            "potential_score": score_data["potential_score"],
            "potential_level": score_data["potential_level"],
            "trend_direction": reg["trend_direction"],
            "regression_metrics": reg["metrics"],
            "classification_metrics": clf["models_comparison"],
            "clustering_info": clst["current_item_cluster"],
            "strategy_recommendation": strat,
            "data_validation": val,
            "regression": reg,
            "classification": clf,
            "clustering": clst
        }
        save_analysis_session(test_session)
        retrieved = get_analysis_session_by_id(test_session["session_id"])
        assert retrieved is not None

        # Verify JSON serializability with zero NaN or Infinity
        dumped = json.dumps(test_session, default=str)
        assert "NaN" not in dumped and "Infinity" not in dumped

        print(f"  [PASS] {fname:38} | Score: {score_data['potential_score']:2d}/100 ({score_data['potential_level']:6}) | R2: {reg['metrics']['r2_score']:+.4f} | TreeAcc: {clf['models_comparison'][1]['accuracy']:.2f} | Sil: {clst['silhouette_score']:.4f}")

    # ─────────────────────────────────────────────────────────────────────────
    # TEST SUITE 4: DASHBOARD PERSISTENCE & STATS
    # ─────────────────────────────────────────────────────────────────────────
    print("\n--- [TEST SUITE 4] Dashboard Stats ---")
    dash = get_dashboard_summary()
    assert dash["total_sessions"] > 0
    assert 0 <= dash["avg_market_potential"] <= 100
    assert dash["total_datasets"] >= 10
    assert dash["total_categories"] >= 10
    print(f"  [PASS] Dashboard metrics: Total Sessions = {dash['total_sessions']}, Avg Potential = {dash['avg_market_potential']}/100, Total Datasets = {dash['total_datasets']}")

    print("\n=================================================================")
    print("   ALL 22 TESTING & VALIDATION REQUIREMENTS VERIFIED (100% PASS)  ")
    print("=================================================================")

if __name__ == "__main__":
    run_tests()

