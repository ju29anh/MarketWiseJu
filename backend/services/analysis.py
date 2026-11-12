import uuid
import logging
from fastapi import HTTPException
from core.serialization import np_clean
from ml_engine.validator import DataValidator
from services.datasets import resolve_dataset, read_dataset
from services.analysis_context import describe_analysis_data
from schemas.analysis import AnalyzeRequest
from database import save_analysis_session
from ml_engine.preprocessor import DataPreprocessor
from ml_engine.regression import MarketRegression
from ml_engine.classification import MarketClassification
from ml_engine.clustering import MarketClustering
from ml_engine.scoring import MarketScorer
from ml_engine.strategy_engine import StrategyEngine
from services.research import normalize, discover
from services.catalog import classify_corpus_to_market
from services.ai_engine import (
    build_domain_specific_strategy,
    get_domain_peers,
    is_ai_configured,
)

logger = logging.getLogger(__name__)


def analyze(req: AnalyzeRequest, progress=lambda step, message: None):
    progress(0, 'Đang thu thập dữ liệu từ các nguồn Web uy tín & kiểm định chất lượng')
    effective_dataset_name = req.dataset_name
    effective_category = req.category
    benchmark_dataset_name = req.dataset_name
    is_custom_upload = effective_dataset_name.startswith("upload_") or bool(req.custom_roles)

    df_raw = read_dataset(resolve_dataset(effective_dataset_name))
    validation_result = DataValidator.validate_dataset(df_raw)
    if not validation_result["valid"]:
        error_msg = validation_result.get("error") or "Không thể phân tích do định dạng hoặc dữ liệu yêu cầu chưa hợp lệ."
        raise HTTPException(status_code=400, detail=error_msg)

    roles = {**validation_result["column_roles"], **(req.custom_roles or {})}
    national_reference = 'scope' in df_raw.columns and df_raw['scope'].eq('national_reference').all()
    observed_entities = df_raw['observed_entity'].dropna().astype(str).unique().tolist() if 'observed_entity' in df_raw.columns else []
    scope_label = ('Chỉ tiêu tham khảo quốc gia: ' + ', '.join(observed_entities or ['Việt Nam'])) if national_reference else effective_dataset_name

    if req.custom_roles:
        allowed = set(validation_result['column_roles'])
        if any(k not in allowed or (v is not None and v not in df_raw.columns) for k, v in req.custom_roles.items()):
            raise HTTPException(400, 'Ánh xạ cột không hợp lệ. Hãy kiểm tra lại tên cột.')

    item_col = roles.get('item_col')
    matched_exact = False
    if item_col and item_col in df_raw.columns:
        matched = df_raw[item_col].fillna('').astype(str).map(normalize) == normalize(req.product_name)
        if matched.any():
            matched_exact = True

    if item_col and not matched_exact and not is_custom_upload:
        raise HTTPException(422, 'Không tìm thấy đối tượng trong bộ dữ liệu đã chọn. Chọn đúng đối tượng hoặc tải dữ liệu riêng; không đổi tên quan sát của đối tượng khác.')

    # Thu thập dữ liệu từ các nguồn Web uy tín, Báo chí, Bách khoa & Nghiên cứu khoa học thời gian thực
    web_research = None
    web_signal_score = None
    web_sources = []
    web_synthesis_meta = None

    if not matched_exact or is_custom_upload:
        try:
            web_research = discover(req.product_name, fast=True)
            web_sources = web_research.get("sources") or []
            ma = web_research.get("market_analysis") or {}
            web_signal_score = (ma.get("market_signals") or {}).get("signal_score")
        except Exception:
            web_research = None

        # Tự động nhận diện đúng ngành hàng của từ khóa bằng ngữ cảnh Web + Gemini 3.5 Flash-Lite
        if not req.custom_roles and not effective_dataset_name.startswith("upload_"):
            try:
                corpus_txt = " ".join(f"{s.get('title', '')} {s.get('excerpt', '')}" for s in web_sources)
                detected_map, detected_kw = classify_corpus_to_market(req.product_name, corpus_txt)
                det_ds = detected_map.get("dataset")
                det_cat = detected_map.get("category")
                if detected_kw and det_cat:
                    effective_category = det_cat
                if detected_kw and det_ds:
                    benchmark_dataset_name = det_ds
            except Exception:
                pass

        if not req.custom_roles and not effective_dataset_name.startswith("upload_"):
            raise HTTPException(422, 'Từ khóa này chưa có quan sát trong bộ dữ liệu đã chọn. Hãy dùng Nghiên cứu & So sánh để tra cứu nguồn, hoặc tải lên dữ liệu định lượng đúng đối tượng. Không dùng dữ liệu khóa học trực tuyến để dự báo cho một trường đại học.')

    # Lấy danh sách đối thủ cùng ngành thực tế (peer_names)
    peer_names = None
    try:
        peer_names = get_domain_peers(req.product_name, effective_category)
    except Exception:
        peer_names = None

    progress(1, 'Đang làm sạch dữ liệu & trích xuất đặc trưng từ nguồn Web uy tín')
    # 3. Tiền xử lý & Trích xuất đặc trưng
    try:
        features_info = DataPreprocessor.extract_features(
            df_raw, roles, product_name=req.product_name, web_signal_score=web_signal_score,
            peer_names=peer_names, allow_fallback_entity=is_custom_upload
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    df_clean = features_info["df_clean"]
    df_reg = features_info.get("df_reg", df_clean)
    if len(df_reg) < 4:
        raise HTTPException(400, 'Cần ít nhất 4 quan sát khác nhau sau khi loại dòng trùng để dự báo.')

    progress(2, 'Đang ước lượng xu hướng và sai số dự báo')
    # 4. Huấn luyện Layer 1: Multi-Model Regression Ensemble (9 Models)
    try:
        regression_result = MarketRegression.train_and_forecast(
            df=df_reg,
            target_col=features_info["target_reg_col"],
            feature_cols=features_info["reg_feature_cols"],
            date_col=roles.get("date_col"),
            forecast_horizon=7
        )
    except Exception:
        logger.exception("Regression failed")
        raise HTTPException(status_code=500, detail="Chưa thể hoàn tất dự báo. Hãy kiểm tra lại bộ dữ liệu.")

    progress(3, 'Đang phân loại các quan sát')
    # 5. Huấn luyện Layer 2: Multi-Model Classification Ensemble (9 Models)
    try:
        classification_result = MarketClassification.train_and_compare(
            df=df_clean,
            target_col=features_info["target_clf_col"],
            feature_cols=features_info["reg_feature_cols"]
        )
    except Exception:
        logger.exception("Classification failed")
        raise HTTPException(status_code=500, detail="Chưa thể hoàn tất dự báo. Hãy kiểm tra lại bộ dữ liệu.")

    progress(4, 'Đang nhóm quan sát tương đồng và tìm ngoại lai')
    # 6. Huấn luyện Layer 3: Multi-Model Clustering & Anomaly Detection (6 Models)
    try:
        clustering_result = MarketClustering.fit_and_segment(
            df=df_clean,
            feature_cols=features_info["cluster_feature_cols"],
            n_clusters=3,
            item_col=roles.get("item_col")
        )
    except Exception:
        logger.exception("Clustering failed")
        raise HTTPException(status_code=500, detail="Chưa thể hoàn tất dự báo. Hãy kiểm tra lại bộ dữ liệu.")

    progress(5, 'Đang tính điểm tiềm năng thị trường đa chiều kết hợp tín hiệu Web')
    # 7. Tính Market Potential Score (0–100)
    potential_data = MarketScorer.calculate_potential_score(df_clean, roles)

    progress(6, 'Đang tổng hợp kết quả và khuyến nghị')
    # 8. Chạy Rule-based Strategy Engine + Gemini 3.8 Flash Domain Intelligence
    strategy_roadmap = StrategyEngine.generate_strategy(
        product_name=scope_label if national_reference else req.product_name,
        category=effective_category,
        potential_data=potential_data,
        regression_data=regression_result,
        classification_data=classification_result,
        clustering_data=clustering_result
    )

    ai_intel = None
    try:
        ai_intel = None if national_reference or not web_sources else build_domain_specific_strategy(
            product_name=req.product_name,
            category=effective_category,
            potential_score=int(potential_data.get("potential_score", 68)),
            growth_pct=float(regression_result.get("projected_growth_pct", 8.0)),
            cluster_name=str(clustering_result.get("current_item_cluster", {}).get("cluster_name", "Balanced Market")),
            web_sources=web_sources,
        )
        if ai_intel:
            if ai_intel.get("executive_summary"):
                strategy_roadmap["market_overview"] = ai_intel["executive_summary"]
            for k in ("target_segment", "product_strategy", "pricing_strategy", "marketing_strategy", "distribution_strategy", "recommended_action"):
                if ai_intel.get(k):
                    strategy_roadmap[k] = ai_intel[k]
            if isinstance(ai_intel.get("opportunities"), list) and len(ai_intel["opportunities"]) >= 2:
                strategy_roadmap["opportunities"] = [str(x) for x in ai_intel["opportunities"]]
            if isinstance(ai_intel.get("risks"), list) and len(ai_intel["risks"]) >= 2:
                strategy_roadmap["risks"] = [str(x) for x in ai_intel["risks"]]
    except Exception:
        logger.debug("AI enrichment fallback used")

    if web_research and web_sources:
        ma = web_research.get("market_analysis") or {}
        exec_sum = ma.get("executive_summary")
        if exec_sum and not (ai_intel and ai_intel.get("ai_model_used", "").startswith("Gemini")):
            strategy_roadmap["market_overview"] = f"{strategy_roadmap['market_overview']} • Bối cảnh thực tế đa nguồn: {exec_sum}"
        figs = (ma.get("market_signals") or {}).get("extracted_figures") or []
        if figs:
            strategy_roadmap["opportunities"].insert(
                0,
                f"Tín hiệu dữ liệu thực tế từ {len(web_sources)} nguồn Web & Báo chí uy tín ghi nhận các chỉ số nổi bật: {', '.join(figs[:4])}."
            )

    # Tổng hợp danh sách toàn bộ 28 mô hình AI & ML hỗ trợ đã kích hoạt
    reg_models = regression_result.get("supporting_models") or []
    clf_models = classification_result.get("supporting_models") or classification_result.get("models_comparison") or []
    clu_models = clustering_result.get("supporting_models") or []
    ai_model_used = (ai_intel or {}).get('ai_model_used') or 'MarketWise rule-based strategy engine'
    ai_models_list = [{'name': ai_model_used, 'model_id': ai_model_used,
        'category': 'Google Gemini AI', 'status': 'Executed'}] if ai_model_used.startswith('gemini-') else []

    supporting_models_summary = {
        "total_models_executed": len(reg_models) + len(clf_models) + len(clu_models) + len(ai_models_list),
        "ai_model_active": ai_model_used,
        "ai_configured": is_ai_configured(),
        "google_models_integrated": [
            "gemini-3.6-flash",
            "gemini-3.5-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.1-flash-lite",
            "gemini-3.8-flash-tts",
        ],
        "regression_models": reg_models,
        "classification_models": clf_models,
        "clustering_models": clu_models,
        "ai_models": ai_models_list,
        "web_synthesis_meta": web_synthesis_meta,
    }

    # 9. Đóng gói kết quả toàn diện
    from services.market_report import build_strategy
    from services.research_evidence import subject_context
    values = df_reg[features_info['target_reg_col']].dropna()
    observed_change = float((values.iloc[-1]/values.iloc[-2]-1)*100) if len(values)>1 and abs(values.iloc[-2])>1e-9 else None
    r2_val = regression_result['metrics']['r2_score']
    strategy_plan = build_strategy(
        req.product_name,
        subject_context(req.product_name, web_sources),
        web_sources,
        {'mode': 'national_reference' if national_reference else 'entity_observations' if matched_exact else 'dataset_observations', 'scope_label': scope_label},
        {'recent_change_pct': observed_change, 'validation': {'beats_baseline': r2_val is not None and r2_val > 0.35, 'r2': r2_val}},
        ai_intel=ai_intel,
    )
    session_id = f"mw_{uuid.uuid4().hex[:10]}"
    is_custom_keyword = web_synthesis_meta is not None or not (
        item_col and item_col in df_raw.columns and not web_synthesis_meta and matched_exact
    )
    final_payload = {
        "session_id": session_id,
        "product_name": req.product_name,
        "category": effective_category,
        "description": req.description,
        "dataset_name": effective_dataset_name,
        "benchmark_dataset": benchmark_dataset_name,
        "data_validation": validation_result,
        "data_context": describe_analysis_data(df_reg, features_info['target_reg_col'], roles),
        "quality_score": validation_result["quality_score"],
        "potential_score": potential_data["potential_score"],
        "potential_level": potential_data["potential_level"],
        "potential_level_vi": potential_data["potential_level_vi"],
        "badge_color": potential_data["badge_color"],
        "potential_breakdown": potential_data,
        "regression": regression_result,
        "trend_direction": regression_result["trend_direction"],
        "projected_growth_pct": regression_result["projected_growth_pct"],
        "regression_metrics": regression_result["metrics"],
        "classification": classification_result,
        "classification_metrics": classification_result["models_comparison"],
        "clustering": clustering_result,
        "clustering_info": clustering_result["current_item_cluster"],
        "strategy_recommendation": strategy_roadmap,
        "strategy_plan": strategy_plan,
        "supporting_models_summary": supporting_models_summary,
        "web_research": web_research,
        "evidence_scope": {
            "matched_item": not is_custom_keyword and not national_reference,
            "rows": len(df_reg),
            "dataset_rows": len(df_raw),
            "source_verified": False,
            "analysis_mode": "national_reference" if national_reference else "exact_item" if not is_custom_keyword else "dataset_observations",
            "scope_label": scope_label,
            "observed_entities": observed_entities,
            "web_sources_count": len(web_sources),
            "reputable_sources_count": (web_synthesis_meta or {}).get("reputable_sources_count", len(web_sources)),
            "benchmark_dataset": benchmark_dataset_name,
            "ai_model_used": supporting_models_summary["ai_model_active"],
            "total_models_count": supporting_models_summary["total_models_executed"],
        },
        "disclaimer": "Kết quả phụ thuộc dữ liệu đầu vào và phạm vi quan sát; kiểm định độ sạch không chứng minh dữ liệu đúng sự thật. Dự báo cần được đối chiếu trước khi ra quyết định."
    }

    final_payload_clean = np_clean(final_payload)
    save_analysis_session(final_payload_clean)
    return final_payload_clean
