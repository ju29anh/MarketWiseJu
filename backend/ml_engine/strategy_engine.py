from typing import Dict, Any, List

class StrategyEngine:
    """
    Rule-Based Business Strategy Engine
    Tổng hợp kết quả từ 4 mô hình Machine Learning và Market Potential Score
    để đưa ra 10 đề mục chiến lược kinh doanh thực thi (5 trụ cột chiến lược).
    """

    @classmethod
    def generate_strategy(
        cls,
        product_name: str,
        category: str,
        potential_data: Dict[str, Any],
        regression_data: Dict[str, Any],
        classification_data: Dict[str, Any],
        clustering_data: Dict[str, Any]
    ) -> Dict[str, Any]:

        score            = int(potential_data.get("potential_score", 50))
        level            = str(potential_data.get("potential_level", "MEDIUM"))
        trend_direction  = str(regression_data.get("trend_direction", "Increasing"))
        growth_pct       = float(regression_data.get("projected_growth_pct", 5.0))
        r2_score         = float(regression_data.get("metrics", {}).get("r2_score", 0.8))
        current_cluster  = clustering_data.get("current_item_cluster", {})
        cluster_name     = str(current_cluster.get("cluster_name", "Balanced Market"))
        clf_confidence   = float(
            classification_data.get("classification_confidence", 80.0)
        )

        # Xác định confidence tier dựa vào R² và clf_confidence
        high_confidence  = r2_score >= 0.75 and clf_confidence >= 75.0
        model_confidence = "Cao" if high_confidence else ("Trung bình" if r2_score >= 0.5 else "Thấp")

        # ── 1. Market Overview ─────────────────────────────────────────────
        growth_sign = "+" if growth_pct >= 0 else ""
        overview = (
            f"Thị trường '{category}' dành cho sản phẩm '{product_name}' đang ghi nhận "
            f"mức tăng trưởng dự báo {growth_sign}{growth_pct:.1f}% trong 7 kỳ tiếp theo. "
            f"Sản phẩm được phân loại thuộc phân khúc '{cluster_name}' với mức tiềm năng "
            f"Market Potential Score {score}/100 ({level}). "
            f"Độ tin cậy tổng hợp của hệ thống mô hình ML: {model_confidence} "
            f"(R² = {r2_score}, Confidence phân loại = {clf_confidence:.1f}%)."
        )

        # ── 2. Trend Summary ────────────────────────────────────────────────
        if trend_direction == "Increasing":
            trend_summary = (
                f"🔺 Xu hướng thị trường đang TĂNG TRƯỞNG TÍCH CỰC ({growth_sign}{growth_pct:.1f}%). "
                f"Đồ thị Linear Regression cho thấy nhu cầu và độ quan tâm người tiêu dùng "
                f"có động lực mở rộng liên tục qua các kỳ. "
                f"{'Đây là tín hiệu rất thuận lợi để gia tăng đầu tư và mở rộng thị phần.' if growth_pct > 10 else 'Tốc độ tăng ổn định, phù hợp để giữ vững và mở rộng thận trọng.'}"
            )
        else:
            trend_summary = (
                f"🔻 Xu hướng thị trường có dấu hiệu CHẬM LẠI ({growth_sign}{growth_pct:.1f}%). "
                f"Cần thận trọng với biến động dung lượng thị trường, "
                f"tập trung giữ chân khách hàng hiện hữu và tối ưu chi phí vận hành. "
                f"{'Sụt giảm nghiêm trọng, cần xem xét tái định vị chiến lược ngay.' if growth_pct < -15 else 'Mức giảm vừa phải, có thể phục hồi bằng chiến lược marketing đúng đắn.'}"
            )

        # ── 3. Opportunities ────────────────────────────────────────────────
        opportunities: List[str] = []
        if score >= 70:
            opportunities.append(
                "Nhu cầu thị trường đang ở mức cao, thuận lợi để gia tăng thị phần nhanh chóng — "
                "cơ hội chiếm lĩnh trước khi đối thủ phản ứng kịp."
            )
            opportunities.append(
                "Khối lượng tìm kiếm và mức độ quan tâm của người tiêu dùng liên tục tạo đỉnh mới, "
                "phù hợp để đẩy mạnh nội dung và chiến dịch truyền thông."
            )
            opportunities.append(
                "Khả năng hấp thụ sản phẩm mới tốt — người tiêu dùng sẵn sàng chi trả "
                "cho những giá trị khác biệt vượt trội so với lựa chọn hiện có."
            )
            if growth_pct > 10:
                opportunities.append(
                    f"Tốc độ tăng trưởng {growth_pct:.1f}% tạo dư địa để mở rộng kênh phân phối "
                    "mới hoặc thâm nhập phân khúc địa lý/nhân khẩu học chưa được khai thác."
                )
        elif score >= 40:
            opportunities.append(
                "Thị trường ổn định với tập khách hàng cốt lõi trung thành — "
                "nền tảng vững chắc để gia tăng doanh thu qua upsell và cross-sell."
            )
            opportunities.append(
                "Có cơ hội khai thác thị trường ngách (niche market) chưa bị các thương hiệu "
                "lớn chiếm lĩnh hoàn toàn, đặc biệt ở các tệp khách hàng đặc thù."
            )
            opportunities.append(
                "Tối ưu hóa biên lợi nhuận thông qua tinh chỉnh gói sản phẩm, "
                "dịch vụ đi kèm và chương trình khách hàng thân thiết."
            )
        else:
            opportunities.append(
                "Cơ hội tái định vị sang phân khúc giá rẻ hoặc mô hình dịch vụ tinh gọn "
                "để tiếp cận tệp khách hàng nhạy cảm về giá."
            )
            opportunities.append(
                "Khai thác các phân khúc ngách bị đối thủ bỏ quên để duy trì dòng tiền "
                "trong giai đoạn thị trường chưa phục hồi."
            )
            opportunities.append(
                "Đầu tư vào R&D và đổi mới sản phẩm để thoát khỏi vòng xoáy cạnh tranh giá, "
                "tạo lợi thế dài hạn khi thị trường hồi phục."
            )

        # ── 4. Risks ────────────────────────────────────────────────────────
        risks: List[str] = []
        if "High Volume" in cluster_name or score >= 70:
            risks.append(
                "Áp lực cạnh tranh cao từ các thương hiệu lớn đã có chỗ đứng vững — "
                "cần xây dựng rào cản cạnh tranh rõ ràng (brand equity, switching cost)."
            )
            risks.append(
                "Rủi ro chi phí chuyển đổi của khách hàng thấp nếu sản phẩm "
                "không có điểm khác biệt rõ ràng so với đối thủ cùng phân khúc."
            )
            if score >= 80:
                risks.append(
                    "Thị trường tăng trưởng nóng có thể thu hút nhiều đối thủ mới gia nhập, "
                    "gây phân tán nhu cầu và giảm thị phần trong trung hạn."
                )
        elif "Premium" in cluster_name:
            risks.append(
                "Quy mô tập khách hàng tiềm năng bị giới hạn ở phân khúc thu nhập cao, "
                "chu kỳ ra quyết định mua hàng kéo dài và yêu cầu trải nghiệm vượt trội."
            )
            risks.append(
                "Nhạy cảm cao với biến động kinh tế vĩ mô — suy thoái kinh tế "
                "có thể làm giảm đột ngột sức mua của tệp khách hàng mục tiêu."
            )
        else:
            risks.append(
                "Tăng trưởng chậm có thể dẫn đến cuộc chiến giá (Price War) khốc liệt, "
                "bào mòn biên lợi nhuận của toàn ngành."
            )
            risks.append(
                "Chi phí thu hút khách hàng mới (CAC) có xu hướng gia tăng khi thị trường "
                "bão hòa — cần tập trung vào retention thay vì acquisition."
            )

        if trend_direction == "Decreasing":
            risks.append(
                f"Xu hướng giảm {growth_pct:.1f}% cần được theo dõi sát — "
                "nếu tiếp tục quá 2 kỳ, cần xem xét điều chỉnh chiến lược toàn diện."
            )

        # ── 5. Target Segment Profile ────────────────────────────────────────
        if "Premium" in cluster_name:
            target_segment = (
                "🎯 Khách hàng phân khúc cao cấp (25-45 tuổi, thu nhập trên trung bình): "
                "chú trọng chất lượng vượt trội, thiết kế tinh xảo và dịch vụ hậu mãi uy tín. "
                "Ưu tiên trải nghiệm thương hiệu độc quyền và tính exclusivity."
            )
        elif "Mass Market" in cluster_name:
            target_segment = (
                "🎯 Tập khách hàng đại chúng (18-40 tuổi, mọi mức thu nhập): "
                "người tiêu dùng trẻ hoặc người mua đề cao tính ứng dụng, "
                "hiệu năng trên giá thành (P/P ratio) và sự tiện lợi trong sử dụng hàng ngày."
            )
        elif "Emerging" in cluster_name:
            target_segment = (
                "🎯 Nhóm Early Adopters và Tech-forward Consumers (20-35 tuổi): "
                "đam mê xu hướng mới, sẵn sàng thử nghiệm các giải pháp sáng tạo "
                "và chia sẻ trải nghiệm qua mạng xã hội — kênh marketing tự nhiên hiệu quả."
            )
        else:
            target_segment = (
                "🎯 Nhóm khách hàng thực dụng (25-50 tuổi): "
                "tìm kiếm sự cân bằng giữa chất lượng đáng tin cậy và mức giá hợp lý. "
                "Quyết định mua hàng dựa trên review, word-of-mouth và tính năng cụ thể."
            )

        # ── 6. Product Strategy ──────────────────────────────────────────────
        if score >= 70:
            product_strategy = (
                "📦 Đẩy nhanh hoàn thiện tính năng cốt lõi (Core Features), tập trung nâng cao "
                "trải nghiệm người dùng (UX/UI) và duy trì chuẩn chất lượng cao nhất. "
                "Xem xét ra mắt phiên bản Pro/Premium để capture giá trị cao hơn từ tệp sẵn sàng chi trả."
            )
        elif score >= 40:
            product_strategy = (
                "📦 Xây dựng 1-2 tính năng tạo điểm nhấn khác biệt (Unique Selling Points) "
                "rõ ràng so với đối thủ. Tránh dàn trải tính năng làm tăng chi phí R&D và "
                "gây khó khăn trong truyền thông. Ưu tiên cải thiện retention trước acquisition."
            )
        else:
            product_strategy = (
                "📦 Đơn giản hóa dòng sản phẩm — loại bỏ các biến thể kém hiệu quả, "
                "tập trung tối ưu hóa chi phí sản xuất và vận hành. "
                "Xem xét mô hình SaaS/subscription để tạo dòng tiền ổn định và dự đoán được."
            )

        # ── 7. Pricing Strategy ──────────────────────────────────────────────
        if "Premium" in cluster_name:
            pricing_strategy = (
                "💰 Chiến lược Value-based Pricing hoặc Skimming Pricing: "
                "duy trì mức giá cao đi kèm bảo hành mở rộng, hỗ trợ ưu tiên và dịch vụ độc quyền. "
                "Tránh discount quá mức — sẽ làm mất định vị thương hiệu cao cấp."
            )
        elif score >= 70:
            pricing_strategy = (
                "💰 Chiến lược Competitive Pricing kết hợp Early-bird Offer: "
                "định giá cạnh tranh với đối thủ chính, kết hợp gói dùng thử hoặc ưu đãi "
                "giai đoạn đầu để mở rộng thị phần nhanh. Cân nhắc bundling để tăng AOV."
            )
        elif score >= 40:
            pricing_strategy = (
                "💰 Chiến lược Tiered Pricing — cung cấp 2-3 mức gói (Basic/Standard/Pro) "
                "phù hợp với từng tệp khách hàng. Kết hợp khuyến mãi theo mùa vụ và "
                "chương trình loyalty để giảm churn rate."
            )
        else:
            pricing_strategy = (
                "💰 Chiến lược Penetration Pricing hoặc Freemium Model: "
                "hạ thấp rào cản thử nghiệm để tăng trial rate. "
                "Sau khi có tập người dùng, dần nâng giá với các tier tính năng cao hơn."
            )

        # ── 8. Marketing Strategy ────────────────────────────────────────────
        if score >= 70:
            marketing_strategy = (
                "📢 Đầu tư mạnh vào Digital Marketing đa kênh: Performance Ads (Meta/Google/TikTok), "
                "Influencer/KOL review có ảnh hưởng lớn trong ngành, và Social Commerce. "
                "Đo lường chặt chẽ ROAS và CAC theo từng kênh để tối ưu ngân sách."
            )
        elif score >= 40:
            marketing_strategy = (
                "📢 Tập trung Content Marketing chuyên sâu, SEO ngách dài hạn "
                "và kích hoạt cộng đồng người dùng thân thiết (Community Marketing). "
                "Email marketing và retargeting để tối ưu conversion rate và giảm CAC."
            )
        else:
            marketing_strategy = (
                "📢 Tối ưu hóa chuyển đổi tại điểm bán (POS marketing), "
                "sử dụng tiếp thị liên kết (Affiliate/Referral) và bán hàng trực tiếp (Direct Sales). "
                "Ưu tiên word-of-mouth và testimonial từ khách hàng hiện hữu."
            )

        # ── 9. Distribution Channel Strategy (5th Pillar) ───────────────────
        if "Mass Market" in cluster_name or score >= 70:
            distribution_strategy = (
                "🚚 Mở rộng đa kênh phân phối: kết hợp Online (website, marketplace: Shopee/Lazada/Tiki) "
                "và Offline (đại lý, chuỗi bán lẻ). "
                "Ưu tiên O2O (Online-to-Offline) để tối đa hóa điểm tiếp xúc với khách hàng. "
                "Xem xét mô hình D2C (Direct-to-Consumer) để kiểm soát trải nghiệm và margin."
            )
        elif "Premium" in cluster_name:
            distribution_strategy = (
                "🚚 Phân phối chọn lọc qua kênh cao cấp: showroom/flagship store, "
                "đối tác phân phối uy tín và website thương mại riêng để bảo vệ brand equity. "
                "Hạn chế xuất hiện trên marketplace đại trà để tránh ảnh hưởng định vị."
            )
        else:
            distribution_strategy = (
                "🚚 Tối ưu hóa kênh phân phối hiện có — tập trung vào các kênh có ROI cao nhất. "
                "Cân nhắc hợp tác với đối tác phân phối để giảm chi phí logistics. "
                "Thử nghiệm dropshipping hoặc fulfillment outsourcing để giảm vốn tồn kho."
            )

        # ── 10. Recommended Action ───────────────────────────────────────────
        if score >= 75 and trend_direction == "Increasing" and growth_pct > 5:
            recommended_action = (
                "🚀 TẬP TRUNG TĂNG TỐC ĐẦU TƯ: Đây là thời điểm vàng để mở rộng. "
                "Đẩy mạnh tung sản phẩm ra thị trường, tăng ngân sách tiếp thị 20-30% "
                "và củng cố kênh phân phối ngay trong quý tới. "
                f"Dự báo tăng trưởng {growth_pct:.1f}% tạo lợi thế người tiên phong rõ ràng."
            )
        elif score >= 55 and trend_direction == "Increasing":
            recommended_action = (
                "✅ THỬ NGHIỆM CÓ KIỂM SOÁT: Triển khai thử nghiệm sản phẩm ở quy mô vừa (MVP/Pilot) "
                "trong 1-2 thị trường địa phương trước khi mở rộng toàn diện. "
                "Theo dõi chỉ số CAC, LTV và Churn Rate theo tuần để điều chỉnh kịp thời."
            )
        elif score >= 40:
            recommended_action = (
                "⚖️ GIỮ VỮNG VÀ TỐI ƯU: Không ưu tiên mở rộng lớn — tập trung giữ vững thị phần "
                "hiện có, tối ưu hóa chi phí vận hành và cải thiện trải nghiệm khách hàng. "
                "Phân bổ ngân sách nghiên cứu thị trường để xác định cơ hội ngách tiếp theo."
            )
        else:
            recommended_action = (
                "⚠️ TÁI CƠ CẤU VÀ THẬN TRỌNG: Không ưu tiên mở rộng vốn lớn trong giai đoạn này. "
                "Rà soát toàn bộ chi phí vận hành, xác định sản phẩm/dịch vụ có biên lợi nhuận "
                "dương và tập trung nguồn lực vào những hạng mục đó. "
                "Xem xét pivot sang mô hình kinh doanh mới nếu thị trường tiếp tục suy giảm."
            )

        # Model output describes the supplied observations, not verified market facts.
        overview = (
            f"Trên bộ dữ liệu đã chọn cho '{product_name}', mô hình ước lượng thay đổi "
            f"{growth_sign}{growth_pct:.1f}% trong 7 kỳ tiếp theo; điểm tổng hợp {score}/100 ({level}). "
            f"R² kiểm định = {r2_score}; độ tin cậy theo tiêu chí nội bộ: {model_confidence}. "
            "Các chỉ số này chưa xác nhận quy mô, thị phần hoặc tăng trưởng thực tế của thị trường."
        )
        trend_summary = (
            f"Chỉ tiêu trong dữ liệu có hướng dự báo {growth_sign}{growth_pct:.1f}%. "
            "Đây là ước lượng có sai số; cần kiểm tra quan sát mới và phương án cơ sở trước khi sử dụng."
        )
        opportunities = ['Giả thuyết cần kiểm nghiệm: ' + item for item in opportunities]
        recommended_action = (
            "THỬ NGHIỆM CÓ KIỂM SOÁT: Đối chiếu dự báo với quan sát mới, xác định chi phí và "
            "giới hạn ngân sách cho một thử nghiệm nhỏ; chỉ mở rộng khi kết quả thực tế đạt mục tiêu."
            if high_confidence else
            "ƯU TIÊN XÁC MINH DỮ LIỆU: Mức hỗ trợ dự báo còn hạn chế. Bổ sung quan sát, "
            "so sánh sai số với phương án cơ sở và thử nghiệm nhỏ trước khi quyết định mở rộng."
        )
        return {
            "market_overview":           overview,
            "trend_summary":             trend_summary,
            "potential_score_display":   f"{score}/100 ({level})",
            "model_confidence":          model_confidence,
            "opportunities":             opportunities,
            "risks":                     risks,
            "target_segment":            target_segment,
            "product_strategy":          product_strategy,
            "pricing_strategy":          pricing_strategy,
            "marketing_strategy":        marketing_strategy,
            "distribution_strategy":     distribution_strategy,
            "recommended_action":        recommended_action
        }
