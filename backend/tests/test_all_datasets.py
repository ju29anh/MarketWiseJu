import os
import sys
import json
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml_engine.validator import DataValidator
from ml_engine.preprocessor import DataPreprocessor
from ml_engine.regression import MarketRegression
from ml_engine.classification import MarketClassification
from ml_engine.clustering import MarketClustering
from ml_engine.scoring import MarketScorer
from ml_engine.strategy_engine import StrategyEngine

datasets_to_test = [
    'food_beverage_specialty_coffee.csv',
    'technology_gaming_laptops.csv',
    'smartphones_market.csv',
    'fashion_apparel_trends.csv',
    'beauty_skincare_products.csv',
    'automotive_electric_vehicles.csv',
    'education_edtech_courses.csv',
    'healthcare_fitness_wearables.csv',
    'smart_home_iot_devices.csv',
    'digital_services_saas.csv',
    'fmcg_packaged_goods.csv',
    'real_estate_proptech.csv',
    'tourism_travel_hospitality.csv',
    'fintech_digital_banking.csv',
    'logistics_supply_chain.csv',
    'consumer_electronics_audio.csv'
]


def run_all_datasets():
    print('[1] All ML modules imported OK')
    errors = []
    datasets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets"))
    for ds_file in datasets_to_test:
        try:
            df = pd.read_csv(os.path.join(datasets_dir, ds_file))
            val = DataValidator.validate_dataset(df)
            roles = val['column_roles']
            fi = DataPreprocessor.extract_features(df, roles)
            df_c = fi['df_clean']
            df_r = fi.get('df_reg', df_c)
            reg = MarketRegression.train_and_forecast(
                df=df_r,
                target_col=fi['target_reg_col'],
                feature_cols=fi['reg_feature_cols'],
                date_col=roles.get('date_col')
            )
            clf = MarketClassification.train_and_compare(
                df=df_c,
                target_col=fi['target_clf_col'],
                feature_cols=fi['reg_feature_cols']
            )
            clust = MarketClustering.fit_and_segment(
                df=df_c,
                feature_cols=fi['cluster_feature_cols']
            )
            score = MarketScorer.calculate_potential_score(df_c, roles)
            strat = StrategyEngine.generate_strategy(
                'Test Product', 'Test Category', score, reg, clf, clust
            )
            # Check no NaN/Infinity
            combined = {'reg': reg, 'clf': clf, 'clust': clust, 'score': score, 'strat': strat}
            j = json.dumps(combined, default=str)
            if 'NaN' in j or 'Infinity' in j:
                raise AssertionError('NaN/Infinity found in result')

            sc = score['potential_score']
            tr = reg['trend_direction']
            cn = clust['current_item_cluster']['cluster_name']
            r2 = reg['metrics']['r2_score']
            mae = reg['metrics']['mae']
            print(f"  OK: {ds_file:36} | score={sc:2} | trend={tr:10} | r2={r2:.4f} | mae={mae:8.2f} | cluster={cn[:22]}")
        except Exception as e:
            errors.append(ds_file + ': ' + str(e))
            print('  FAIL: ' + ds_file + ' -- ' + str(e))

    print()
    if errors:
        print('=== FAILED: ' + str(len(errors)) + ' datasets ===')
        for e in errors:
            print('  - ' + e)
        sys.exit(1)
    else:
        print(f'=== ALL {len(datasets_to_test)} DATASETS PASSED - ZERO ERRORS ===')


if __name__ == '__main__':
    run_all_datasets()
