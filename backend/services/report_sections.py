"""Keyword-aware market, pricing, risk, and 30-60-90 strategy intelligence with explicit evidence limits."""
from services.research_evidence import key, extract_observations


def _source_digest(query, sources):
    obs = extract_observations(query, sources or [])
    figures = list(dict.fromkeys(r['raw_value'] for r in obs if r.get('raw_value')))[:4]
    titles = [s.get('title', '').strip() for s in (sources or [])[:3] if s.get('title')]
    snippets = []
    for s in (sources or [])[:3]:
        ex = (s.get('excerpt') or '').strip()
        if ex:
            first_sent = ex.split('. ')[0].strip()
            if len(first_sent) > 25:
                snippets.append(f"“{first_sent[:160]}” ({s.get('provider') or 'Nguồn tra cứu'})")
    return {
        'figures': figures,
        'titles': titles,
        'snippets': snippets,
        'figure_note': f" Ghi nhận số liệu trong trích đoạn: {', '.join(figures)}." if figures else "",
        'title_note': f" Tài liệu đối chiếu tiêu biểu: {'; '.join(titles[:2])}." if titles else "",
    }


def get_keyword_intelligence(query, context, sources=()):
    q = key(query)
    cat = context.get('category', 'General Research')
    digest = _source_digest(query, sources)
    fig_note = digest['figure_note']

    is_police_military = any(t in q for t in (
        'canh sat', 'an ninh nhan dan', 'phong chay', 'pccc', 'quan doi', 'quan y',
        'ky thuat quan su', 'bien phong', 'hau can', 'luc quan', 'hai quan', 'khong quan', 'kiem sat', 'toa an'
    ))
    is_university = cat == 'Education & EdTech' and (is_police_military or any(t in q for t in (
        'dai hoc', 'truong dh', 'university', 'hoc vien', 'cao dang', 'college',
        'bach khoa', 'su pham', 'y duoc', 'ngoai thuong', 'tdmu', 'bdu', 'hutech', 'ueh', 'rmit'
    )))

    if is_police_military:
        peers = "Học viện Cảnh sát nhân dân, Trường Đại học An ninh nhân dân, Học viện An ninh nhân dân, Trường Đại học Phòng cháy chữa cháy"
        return {
            'sub_type': 'police_military_academy',
            'peers': peers,
            'audience': f"Thí sinh đăng ký sơ tuyển khối trường Công an nhân dân / Quân đội tại các địa phương, học viên chuyên ngành nghiệp vụ tại {query} và Công an các đơn vị, địa phương tiếp nhận biên chế",
            'offer': f"chương trình đào tạo sĩ quan nghiệp vụ chính quy của {query}, phương thức thi Đánh giá năng lực Bộ Công an (CA1, CA2) kết hợp điểm thi THPT, chế độ miễn 100% học phí - cấp sinh hoạt phí và phân công công tác theo biên chế ngành sau tốt nghiệp",
            'focus': f"công tác tuyển sinh theo chỉ tiêu phân vùng địa bàn, huấn luyện nghiệp vụ chuyên sâu và chuẩn hóa chất lượng đào tạo sĩ quan tại {query}",
            'channels': f"Cổng thông tin điện tử chính thức của {query}, Ban Tuyển sinh Công an các tỉnh/thành phố, Công an cấp quận/huyện/thị xã nơi thí sinh đăng ký sơ tuyển và hệ thống truyền thông ngành",
            'demand_analysis': (
                f"Phân tích số lượng thí sinh đăng ký sơ tuyển so với chỉ tiêu biên chế giao cho {query} theo từng địa bàn tuyển sinh, "
                f"từng nhóm ngành nghiệp vụ (Điều tra hình sự, Quản lý hành chính về TTXH, Cảnh sát giao thông, Kỹ thuật hình sự...) và tỷ lệ phân bổ Nam/Nữ.{fig_note}"
            ),
            'competition_analysis': (
                f"Đối chiếu điểm chuẩn tổ hợp CA1, CA2 và tỷ lệ chọi của {query} với các trường cùng khối lực lượng vũ trang "
                f"({peers}) theo cùng năm tuyển sinh và phân vùng địa lý."
            ),
            'market_gap': (
                f"Khoảng trống thông tin cần giải quyết: nhu cầu hướng dẫn chi tiết cho thí sinh về tiêu chuẩn sơ tuyển (chính trị, sức khỏe, thị lực, chiều cao/cân nặng), "
                f"cấu trúc bài thi đánh giá Bộ Công an (CA1, CA2) và định hướng rèn luyện nội trú tại {query}."
            ),
            'pricing_reason': (
                f"Đối với cơ sở đào tạo lực lượng vũ trang công lập đặc thù như {query}, học viên hệ chính quy trong ngành được Nhà nước và Bộ chủ quản đài thọ 100% học phí, "
                f"bố trí ký túc xá nội trú và cấp phụ cấp sinh hoạt phí theo niên hạn; đối chiếu định mức ngân sách đào tạo và chế độ đãi ngộ học viên theo quy định hiện hành."
            ),
            'pricing_methods': [
                {'name': 'Chế độ miễn học phí & phụ cấp học viên', 'action': f'Công khai đầy đủ quyền lợi học viên chính quy tại {query}: miễn 100% học phí, trang cấp quân trang, ăn ở nội trú và hưởng phụ cấp theo cấp bậc hàm học viên.'},
                {'name': 'Định mức kinh phí đào tạo & thao trường', 'action': f'Phân bổ ngân sách đào tạo cho phòng thí nghiệm kỹ thuật hình sự, trường bắn, thao trường chiến thuật, chuyển đổi số học liệu và nghiên cứu khoa học tại {query}.'},
                {'name': 'Quỹ khen thưởng & đãi ngộ học viên giỏi', 'action': f'Thiết lập chế độ khen thưởng học viên đạt thành tích xuất sắc trong học tập, rèn luyện điều lệnh, nghiên cứu khoa học và hội thi nghiệp vụ tại {query}.'},
            ],
            'required_inputs': [
                f'Đề án tuyển sinh và chỉ tiêu biên chế phân bổ cho {query} theo năm học',
                'Quy định tiêu chuẩn sơ tuyển sức khỏe, chính trị và cấu trúc bài thi đánh giá Bộ Công an (CA1, CA2)',
                'Chế độ phụ cấp sinh hoạt phí, định mức đào tạo và quy chế quản lý học viên nội trú',
                'Số liệu điểm chuẩn theo tổ hợp/địa bàn và kết quả phân công công tác sau tốt nghiệp',
            ],
            'risks_tuples': [
                ('Tuyển sinh, sơ tuyển & chỉ tiêu biên chế', f'Biến động số lượng thí sinh đạt chuẩn sơ tuyển sức khỏe, chính trị hoặc chênh lệch điểm chuẩn giữa các địa bàn xét tuyển vào {query}.', 'Theo dõi số hồ sơ đủ điều kiện sơ tuyển tại Công an các tỉnh/thành phố và phổ điểm bài thi đánh giá CA1, CA2.', f'Phối hợp chặt chẽ với Công an địa phương hướng dẫn sơ tuyển sớm và công bố đề án tuyển sinh của {query} đúng quy chế.'),
                ('Kỷ luật điều lệnh & thích nghi môi trường nội trú', f'Cường độ huấn luyện võ thuật, thể lực, điều lệnh nội vụ và kỷ luật vũ trang tại {query} đòi hỏi khả năng thích nghi cao của tân học viên.', 'Theo dõi kết quả huấn luyện đầu khóa, thể lực và mức độ chấp hành điều lệnh của học viên.', 'Tăng cường công tác tư tưởng, đồng hành tâm lý và nâng cấp điều kiện sinh hoạt, học tập tại khu nội trú.'),
                ('Chất lượng, kiểm định & chuẩn đầu ra nghiệp vụ', f'Sự phát triển của tội phạm công nghệ cao và yêu cầu chuyển đổi số đòi hỏi chương trình đào tạo và kiểm định chất lượng tại {query} phải cập nhật liên tục.', 'Kiểm tra văn bản kiểm định chương trình đào tạo, thời lượng thực hành nghiệp vụ và phản hồi từ đơn vị tiếp nhận.', 'Cập nhật giáo trình điều tra số, tăng cường thực tập tại Công an cơ sở và thực hiện kiểm định chất lượng đào tạo định kỳ.'),
            ],
            'action_plan': [
                {
                    'period': 'Ngày 1–30',
                    'goal': f'Chuẩn hóa dữ liệu đề án tuyển sinh, chỉ tiêu địa bàn & năng lực đào tạo của {query}',
                    'actions': [
                        f'Tổng hợp đề án tuyển sinh chính thức của {query}: chỉ tiêu phân bổ theo từng chuyên ngành nghiệp vụ, vùng tuyển sinh và tỷ lệ Nam/Nữ.',
                        f'Rà soát tiêu chuẩn sơ tuyển (chính trị, sức khỏe, học lực THPT) và cấu trúc đề thi Đánh giá năng lực Bộ Công an (CA1, CA2) áp dụng tại {query}.',
                        f'Hệ thống hóa dữ liệu về quy mô học viên, đội ngũ giảng viên (Tiến sĩ, Phó Giáo sư), hạ tầng phòng thực hành nghiệp vụ và kết quả kiểm định của {query}.',
                    ],
                    'owner': 'Phòng Quản lý Đào tạo & Ban Tuyển sinh',
                    'deliverable': f'Bộ hồ sơ dữ liệu tuyển sinh, phổ điểm chuẩn 3 năm gần nhất và báo cáo năng lực đào tạo của {query}',
                    'gate': 'Số liệu khớp với đề án công bố chính thức của Bộ chủ quản và nhà trường.',
                },
                {
                    'period': 'Ngày 31–60',
                    'goal': f'Đẩy mạnh công tác hướng dẫn sơ tuyển & hiện đại hóa huấn luyện nghiệp vụ tại {query}',
                    'actions': [
                        f'Phối hợp Công an các tỉnh/thành phố truyền thông rõ quy trình sơ tuyển, lịch thi đánh giá CA1/CA2 và giải đáp trực tiếp tiêu chuẩn xét tuyển vào {query}.',
                        f'Nâng cấp học liệu số và mô hình thực hành diễn tập tình huống nghiệp vụ (Điều tra hình sự, Kỹ thuật hình sự, Quản lý hành chính, CSGT) tại {query}.',
                        f'Theo dõi tiến độ hồ sơ đăng ký sơ tuyển theo từng tỉnh/thành hàng tuần để hỗ trợ giải đáp kịp thời các vướng mắc về thủ tục.',
                    ],
                    'owner': 'Ban Tuyển sinh, Khoa Nghiệp vụ & Phòng Công tác Học viên',
                    'deliverable': 'Báo cáo tiến độ hồ sơ sơ tuyển theo địa bàn và bộ tài liệu hướng dẫn ôn tập - huấn luyện nghiệp vụ chuẩn hóa',
                    'gate': 'Đảm bảo 100% thông tin tư vấn tuyển sinh tuân thủ quy chế công khai của ngành.',
                },
                {
                    'period': 'Ngày 61–90',
                    'goal': f'Đối chiếu phổ điểm trúng tuyển, kiểm định chuẩn đầu ra & điều phối đào tạo khóa mới tại {query}',
                    'actions': [
                        f'Phân tích phổ điểm trúng tuyển thực tế vào {query} theo từng tổ hợp (CA1, CA2) và địa bàn để đánh giá chất lượng nguồn tuyển đầu vào.',
                        f'Thu thập phản hồi từ Công an các đơn vị, địa phương tiếp nhận học viên tốt nghiệp {query} nhằm cập nhật chuẩn đầu ra sát thực tiễn chiến đấu.',
                        f'Hoàn thiện kế hoạch huấn luyện đầu khóa, phân bổ giảng viên hướng dẫn nghiên cứu khoa học và lịch kiểm định chương trình đào tạo năm học mới.',
                    ],
                    'owner': 'Ban Giám hiệu, Hội đồng Tuyển sinh & Phòng Đảm bảo Chất lượng',
                    'deliverable': f'Báo cáo tổng kết tuyển sinh, kế hoạch đào tạo năm học mới và lộ trình nâng chuẩn kiểm định của {query}',
                    'gate': 'Hoàn tất đối chiếu dữ liệu nhập học thực tế và phê duyệt kế hoạch năm học.',
                },
            ],
            'kpis': [
                {'name': 'Tỷ lệ hoàn thành chỉ tiêu biên chế tuyển sinh', 'formula': 'Số học viên trúng tuyển nhập học hợp lệ / tổng chỉ tiêu Bộ giao', 'target': 'Đạt 100% chỉ tiêu biên chế theo đúng cơ cấu vùng và ngành', 'frequency': 'Theo kỳ tuyển sinh năm'},
                {'name': 'Chất lượng nguồn tuyển đầu vào (CA1/CA2 & THPT)', 'formula': 'Điểm trung bình trúng tuyển của học viên khóa mới theo từng tổ hợp xét tuyển', 'target': 'Duy trì hoặc tăng so với mặt bằng điểm chuẩn 3 năm gần nhất', 'frequency': 'Mỗi kỳ tuyển sinh'},
                {'name': 'Tỷ lệ học phần nghiệp vụ ứng dụng công nghệ & thực hành', 'formula': 'Số giờ thực hành diễn tập nghiệp vụ, kỹ thuật hình sự, điều tra số / tổng thời lượng chương trình', 'target': 'Tối ưu hóa tỷ trọng thực hành theo chuẩn đào tạo sĩ quan hiện đại', 'frequency': 'Mỗi học kỳ'},
                {'name': 'Mức độ đáp ứng yêu cầu công tác tại đơn vị tiếp nhận', 'formula': 'Số học viên tốt nghiệp hoàn thành tốt nhiệm vụ tại Công an đơn vị, địa phương / tổng số khảo sát', 'target': 'Trên 95% đơn vị tiếp nhận đánh giá đạt và vượt chuẩn nghiệp vụ', 'frequency': 'Định kỳ hàng năm'},
            ],
        }

    if is_university:
        region_hint = (
            "tại Bình Dương và vùng Đông Nam Bộ" if any(x in q for x in ('thu dau mot', 'binh duong', 'mien dong', 'tdmu', 'bdu'))
            else "tại TP.HCM và khu vực phía Nam" if any(x in q for x in ('tphcm', 'sai gon', 'hutech', 'van lang', 'ton duc thang', 'ueh'))
            else "tại Việt Nam"
        )
        peers = "ĐH Quốc gia TP.HCM, ĐH Thủ Dầu Một (TDMU), ĐH Kinh tế TP.HCM (UEH), ĐH FPT, ĐH Công nghiệp TP.HCM (IUH), ĐH Bình Dương"
        return {
            'sub_type': 'university_higher_ed',
            'peers': peers,
            'audience': f"Học sinh THPT xét tuyển đại học (qua điểm thi THPT, Đánh giá năng lực ĐHQG, học bạ), học viên cao học và doanh nghiệp liên kết tuyển dụng nhân sự từ {query}",
            'offer': f"danh mục ngành đào tạo ứng dụng, biểu học phí theo tín chỉ - chính sách học bổng, chuẩn kiểm định chất lượng (AUN-QA/ABET/Bộ GD&ĐT) và cam kết thực tập - việc làm sau tốt nghiệp của {query}",
            'focus': f"tuyển sinh đa phương thức, nâng chuẩn kiểm định chương trình đào tạo và đẩy mạnh học kỳ doanh nghiệp (Co-op) cho {query}",
            'channels': f"Cổng tuyển sinh trực tuyến của {query}, chuỗi Ngày hội Tư vấn Tuyển sinh - Hướng nghiệp (Open Day) tại các trường THPT, kênh TikTok/Facebook/YouTube học thuật và mạng lưới doanh nghiệp đối tác thực tập",
            'demand_analysis': (
                f"Đánh giá nhu cầu đăng ký nguyện vọng vào {query} {region_hint} theo từng nhóm ngành (Công nghệ thông tin - AI, Kỹ thuật - Bán dẫn, Kinh tế - Logistics, Ngôn ngữ, Sư phạm), "
                f"tương quan giữa mức học phí thực trả/năm học với tỷ lệ sinh viên có việc làm đúng chuyên ngành sau tốt nghiệp.{fig_note}"
            ),
            'competition_analysis': (
                f"Đối chiếu điểm chuẩn các phương thức (THPT, ĐGNL, Học bạ), học phí tín chỉ, số chương trình đạt chuẩn kiểm định và chính sách học bổng của {query} "
                f"với nhóm trường cùng phân khúc ({peers})."
            ),
            'market_gap': (
                f"Khoảng trống chiến lược cho {query}: phát triển các chương trình đào tạo tích hợp chứng chỉ nghề quốc tế, học kỳ doanh nghiệp thực chiến tại các khu công nghiệp/tập đoàn "
                f"và công cụ tính toán lộ trình học phí - học bổng minh bạch ngay từ khâu tư vấn tuyển sinh."
            ),
            'pricing_reason': (
                f"So sánh học phí trên mỗi tín chỉ/học kỳ của {query} theo từng khối ngành, hệ đào tạo (chính quy chuẩn, chất lượng cao, liên kết quốc tế) và quỹ học bổng khuyến tài; "
                f"không định giá thương mại bản thân trường đại học."
            ),
            'pricing_methods': [
                {'name': 'Đối chiếu học phí theo tín chỉ & khối ngành', 'action': f'Bóc tách biểu học phí từng tín chỉ, tổng số tín chỉ toàn khóa và các lệ phí bắt buộc của {query}; chuẩn hóa về mức thực đóng trung bình mỗi học kỳ/năm học.'},
                {'name': 'Định vị giá trị đào tạo & đầu ra việc làm', 'action': f'Đặt mức học phí của {query} tương xứng với chuẩn kiểm định (AUN-QA/Bộ GD&ĐT), chất lượng phòng Lab thực hành và thu nhập khởi điểm của cựu sinh viên.'},
                {'name': 'Quỹ học bổng khuyến tài & hỗ trợ tài chính', 'action': f'Thiết kế gói học bổng tân sinh viên (25%–100% học phí theo điểm đầu vào), học bổng doanh nghiệp tài trợ và chính sách giãn tiến độ đóng học phí tại {query}.'},
            ],
            'required_inputs': [
                f'Biểu học phí tín chỉ và tổng số tín chỉ từng ngành đào tạo của {query} theo năm học',
                'Chỉ tiêu tuyển sinh, điểm chuẩn và tỷ lệ nhập học thực tế theo từng phương thức xét tuyển',
                'Danh sách chương trình đạt kiểm định chất lượng (Bộ GD&ĐT, AUN-QA, ABET, FIBAA)',
                'Báo cáo khảo sát tỷ lệ sinh viên có việc làm trong 12 tháng sau tốt nghiệp kèm cỡ mẫu',
            ],
            'risks_tuples': [
                ('Tuyển sinh & dịch chuyển cơ cấu ngành', f'Thí sinh có xu hướng dồn nguyện vọng vào một số ngành hot trong khi các ngành cơ bản tại {query} có nguy cơ thiếu hụt chỉ tiêu.', 'Theo dõi tỷ lệ đăng ký nguyện vọng 1, tỷ lệ xác nhận nhập học (Yield Rate) và điểm chuẩn từng ngành.', f'Tái cấu trúc chương trình theo hướng liên ngành (tích hợp AI, Chuyển đổi số) và đẩy mạnh tư vấn hướng nghiệp thực tế cho {query}.'),
                ('Khả năng chi trả & biến động học phí', f'Lộ trình điều chỉnh học phí theo cơ chế tự chủ đại học có thể tạo áp lực tài chính cho sinh viên khu vực tỉnh theo học tại {query}.', 'Theo dõi tỷ lệ thí sinh trúng tuyển nhưng không nhập học do chi phí và tỷ lệ sinh viên bảo lưu.', f'Công khai lộ trình trần học phí toàn khóa của {query}, mở rộng quỹ học bổng doanh nghiệp và tín dụng sinh viên.'),
                ('Chất lượng, kiểm định & chuẩn đầu ra việc làm', f'Yêu cầu khắt khe về tỷ lệ giảng viên trình độ Tiến sĩ, công bố khoa học quốc tế và kiểm định chương trình đào tạo của {query}.', 'Kiểm tra văn bản kiểm định định kỳ, tỷ lệ sinh viên thực tập tại doanh nghiệp và cỡ mẫu khảo sát việc làm.', 'Chỉ công bố số liệu việc làm có báo cáo ba công khai xác thực; tăng cường học kỳ doanh nghiệp (Co-op) với các đối tác tuyển dụng.'),
            ],
            'action_plan': [
                {
                    'period': 'Ngày 1–30',
                    'goal': f'Rà soát dữ liệu Ba công khai, phổ điểm chuẩn & biểu học phí của {query}',
                    'actions': [
                        f'Thu thập đề án tuyển sinh, chỉ tiêu, điểm chuẩn 3 năm gần nhất (THPT, ĐGNL, Học bạ) và biểu học phí tín chỉ theo từng ngành của {query}.',
                        f'Khảo sát học sinh lớp 12, phụ huynh và cựu sinh viên về 3 tiêu chí quyết định khi chọn {query} (chất lượng giảng dạy, học phí, cơ hội việc làm).',
                        f'Đối chiếu danh mục ngành đạt kiểm định chất lượng (Bộ GD&ĐT, AUN-QA) và mạng lưới doanh nghiệp ký kết hợp tác thực tập với {query}.',
                    ],
                    'owner': 'Phòng Tuyển sinh - Truyền thông & Phòng Đảm bảo Chất lượng',
                    'deliverable': f'Bảng đối chiếu cạnh tranh học phí - điểm chuẩn - kiểm định của {query} và chân dung thí sinh mục tiêu',
                    'gate': '100% số liệu trích xuất từ Đề án tuyển sinh và Báo cáo Ba công khai chính thức.',
                },
                {
                    'period': 'Ngày 31–60',
                    'goal': f'Triển khai chiến dịch tuyển sinh đa phương thức & học kỳ doanh nghiệp cho {query}',
                    'actions': [
                        f'Vận hành công cụ tra cứu học phí toàn khóa, học bổng và cơ hội nghề nghiệp từng ngành trên cổng tuyển sinh của {query}.',
                        f'Tổ chức chuỗi Open Day trải nghiệm phòng Lab/campus và phiên livestream tư vấn xét tuyển trực tiếp cùng giảng viên, sinh viên tiêu biểu của {query}.',
                        f'Mở rộng ký kết học kỳ doanh nghiệp (Co-op/Internship) với các doanh nghiệp trong vùng để bảo đảm đầu ra thực tập có lương cho sinh viên {query}.',
                    ],
                    'owner': 'Trung tâm Tuyển sinh, Khoa chuyên môn & Trung tâm Hợp tác Doanh nghiệp',
                    'deliverable': 'Báo cáo chuyển đổi hồ sơ xét tuyển theo tuần và danh mục vị trí thực tập doanh nghiệp cam kết',
                    'gate': 'Chi phí thu hút mỗi hồ sơ nhập học (Cost per Enrolled Student) nằm trong ngưỡng ngân sách duyệt.',
                },
                {
                    'period': 'Ngày 61–90',
                    'goal': f'Tối ưu tỷ lệ nhập học thực tế (Yield Rate) & nâng chuẩn kiểm định tại {query}',
                    'actions': [
                        f'Đánh giá tỷ lệ thí sinh trúng tuyển xác nhận nhập học thực tế theo từng phương thức và từng khoa/ngành của {query}.',
                        f'Điều chỉnh phân bổ chỉ tiêu, chính sách học bổng khuyến tài cho các ngành mũi nhọn (Công nghệ, Kỹ thuật, Kinh tế số) dựa trên dữ liệu nhập học.',
                        f'Cập nhật bộ dữ liệu theo dõi sinh viên tốt nghiệp có việc làm sau 6–12 tháng và hoàn thiện hồ sơ kiểm định chất lượng chu kỳ tiếp theo cho {query}.',
                    ],
                    'owner': 'Ban Giám hiệu, Phòng Đào tạo & Phòng Công tác Sinh viên',
                    'deliverable': f'Kế hoạch chỉ tiêu năm học mới, báo cáo kiểm định và ngân sách học bổng tối ưu của {query}',
                    'gate': 'Có đầy đủ dữ liệu đối chiếu ít nhất 2 kỳ tuyển sinh trước khi mở ngành hoặc tăng quy mô.',
                },
            ],
            'kpis': [
                {'name': 'Tỷ lệ xác nhận nhập học thực tế (Enrollment Yield Rate)', 'formula': 'Số tân sinh viên hoàn tất nhập học / tổng số thí sinh đủ điều kiện trúng tuyển', 'target': 'Đạt ≥ 85% chỉ tiêu đề án tuyển sinh theo từng khối ngành', 'frequency': 'Hàng tuần trong mùa tuyển sinh'},
                {'name': 'Tỷ lệ chương trình đào tạo đạt chuẩn kiểm định', 'formula': 'Số chương trình đạt kiểm định (Bộ GD&ĐT, AUN-QA, ABET, FIBAA) / tổng số ngành đào tạo', 'target': 'Tăng trưởng lộ trình kiểm định hàng năm theo chiến lược nhà trường', 'frequency': 'Mỗi học kỳ / năm học'},
                {'name': 'Chi phí thu hút mỗi tân sinh viên nhập học', 'formula': 'Tổng ngân sách truyền thông & tư vấn tuyển sinh / số sinh viên nhập học thực tế', 'target': 'Tối ưu trong trần ngân sách tuyển sinh được duyệt', 'frequency': 'Hàng tháng'},
                {'name': 'Tỷ lệ sinh viên có việc làm đúng/liên quan chuyên ngành', 'formula': 'Số sinh viên có việc làm trong 12 tháng sau tốt nghiệp / tổng sinh viên phản hồi khảo sát', 'target': 'Công bố minh bạch kèm cỡ mẫu khảo sát theo chuẩn Ba công khai', 'frequency': 'Định kỳ hàng năm'},
            ],
        }

    if cat == 'Smartphones & Mobile':
        is_imported = any(t in q for t in ('nhap khau', 'trung quoc', 'xach tay', 'noi dia'))
        peers = "Xiaomi 14 / Redmi Note Series, OPPO Reno / Find Series, Vivo X Series, Realme GT, Samsung Galaxy A/S Series, iPhone chính hãng VN/A"
        if is_imported:
            return {
                'sub_type': 'imported_mobile',
                'peers': peers,
                'audience': f"Người tiêu dùng ưu tiên hiệu năng/giá thành (P/P ratio), game thủ di động, người dùng trẻ yêu công nghệ và hệ thống đại lý phân phối {query}",
                'offer': f"lợi thế cấu hình phần cứng vượt tầm giá (vi xử lý Snapdragon/Dimensity, pin Silicon-Carbon 5500–6500mAh, sạc siêu nhanh 80W–120W, màn hình AMOLED 120Hz), nguồn gốc nhập khẩu hợp quy và chế độ bảo hành nguồn/màn hình cho {query}",
                'focus': f"chuẩn hóa nguồn cung nhập khẩu chính ngạch, tối ưu định giá theo phân khúc cấu hình và xóa bỏ rào cản tâm lý về bảo hành/phần mềm đối với {query}",
                'channels': f"Chuỗi bán lẻ di động (Thế Giới Di Động, FPT Shop, CellphoneS, Hoàng Hà Mobile, Di Động Việt), gian hàng Shopee Mall / TikTok Shop / Lazada Mall và các kênh review công nghệ (YouTube, TikTok)",
                'demand_analysis': (
                    f"Phân tích sức mua {query} theo 3 phân khúc giá (phổ thông 3–6 triệu, tầm trung 7–12 triệu, cận cao cấp >13 triệu VNĐ), "
                    f"nhu cầu sạc nhanh - pin lớn - màn hình tần số quét cao và sự dịch chuyển từ hàng xách tay tiểu ngạch sang hàng nhập khẩu chính ngạch có chứng nhận hợp quy.{fig_note}"
                ),
                'competition_analysis': (
                    f"Đối chiếu thông số kỹ thuật, giá thực bán sau trừ quà, chính sách thu cũ đổi mới (Trade-in) và thời hạn bảo hành (12–24 tháng) của {query} "
                    f"so với nhóm đối thủ trực tiếp ({peers})."
                ),
                'market_gap': (
                    f"Khoảng trống thị trường cho {query}: người mua muốn hưởng mức giá/cấu hình tốt của các hãng điện thoại Trung Quốc nhưng đòi hỏi sẵn ROM Quốc tế ổn định, "
                    f"không trễ thông báo, hỗ trợ đầy đủ 5G/NFC sinh trắc học ngân hàng tại Việt Nam và bảo hành 1 đổi 1 minh bạch."
                ),
                'pricing_reason': (
                    f"Định giá {query} cần tính đủ giá vốn nhập khẩu (FOB/CIF), thuế VAT, phí kiểm định hợp quy Cục Viễn thông, chi phí bảo hành dự phòng (RMA) "
                    f"và biên độ trượt giá nhanh theo chu kỳ ra mắt sản phẩm mới (6 tháng/thế hệ)."
                ),
                'pricing_methods': [
                    {'name': 'Định giá theo tỷ lệ Hiệu năng/Giá (P/P Ratio)', 'action': f'Neo giá bán {query} thấp hơn 10%–20% so với các mẫu máy cùng cấu hình chip/RAM/camera của đối thủ truyền thống để tạo lợi thế cạnh tranh trực diện.'},
                    {'name': 'Tách gói giá máy trần & gói Bảo hành Vàng', 'action': f'Cung cấp mức giá khởi điểm hấp dẫn cho {query}, đồng thời bán kèm (upsell) gói bảo hành toàn diện nguồn, màn hình, rơi vỡ 12–24 tháng.'},
                    {'name': 'Trợ giá Thu cũ đổi mới (Trade-in) & Trả góp 0%', 'action': f'Hợp tác cổng thanh toán/tài chính tiêu dùng hỗ trợ trả góp 0% lãi suất và trợ giá thu máy cũ lên đời {query} để kích cầu phân khúc trên 8 triệu đồng.'},
                ],
                'required_inputs': [
                    f'Danh mục mã máy (SKU), cấu hình RAM/ROM và bảng giá nhập FOB/chính ngạch của {query}',
                    'Chi phí logistics, thuế nhập khẩu/VAT, phí đo kiểm chứng nhận hợp quy (CR) và tỷ lệ dự phòng bảo hành',
                    'Giá bán thực tế của các mẫu Xiaomi, OPPO, Vivo, Realme, Samsung cùng tầm giá tại các chuỗi lớn',
                    'Tốc độ vòng quay hàng tồn kho (Inventory Aging) và lịch ra mắt thế hệ kế nhiệm của hãng',
                ],
                'risks_tuples': [
                    ('Chính sách khóa mạng (Region Lock) & Phần mềm', f'Các dòng máy nội địa/xách tay trong nhóm {query} có rủi ro bị hãng khóa SIM ngoài lãnh thổ, chậm thông báo hoặc lỗi NFC ngân hàng.', 'Theo dõi tỷ lệ đổi trả do lỗi phần mềm, khóa SIM và phản hồi của người dùng sau cập nhật OTA.', f'Ưu tiên phân phối phiên bản Quốc tế/Chính ngạch của {query} đã được chứng nhận hợp quy và kiểm thử tương thích nhà mạng Việt Nam.'),
                    ('Biến động tỷ giá, chuỗi cung ứng & التزام hải quan', f'Thay đổi quy định kiểm soát nhập khẩu, tỷ giá CNY/USD/VND hoặc tắc nghẽn biên giới làm biến động giá vốn của {query}.', 'Theo dõi chi phí logistics/đơn vị, thời gian thông quan và chênh lệch tỷ giá theo tuần.', 'Đa dạng hóa nhà phân phối ủy quyền (Digiworld, Synnex FPT, Viettel) và chuẩn hóa đầy đủ chứng từ hóa đơn VAT, hợp quy.'),
                    ('Tụt giá chu kỳ ngắn & chi phí bảo hành phần cứng', f'Chu kỳ ra mắt máy mới dày đặc (4–6 tháng) khiến tồn kho {query} đời cũ nhanh mất giá; rủi ro lỗi màn hình/nguồn làm ăn mòn biên lợi nhuận.', 'Đo số ngày tồn kho bình quân (DSI) từng SKU và tỷ lệ máy bảo hành (RMA Rate).', 'Giới hạn tồn kho tối đa 25–30 ngày bán hàng cho mỗi mã máy; đàm phán cơ chế Price Protection (bảo vệ giá) với nhà cung cấp.'),
                ],
                'action_plan': [
                    {
                        'period': 'Ngày 1–30',
                        'goal': f'Chuẩn hóa danh mục SKU, pháp lý nhập khẩu hợp quy & cấu trúc giá vốn cho {query}',
                        'actions': [
                            f'Lập bảng đối chiếu 10–15 mẫu máy chủ lực thuộc nhóm {query} theo 3 phân khúc giá, so sánh chi tiết chip, pin, sạc nhanh, màn hình và giá bán với đối thủ.',
                            f'Kiểm tra toàn diện hồ sơ chứng nhận hợp quy (CR), hóa đơn VAT, khả năng tương thích 5G Việt Nam, NFC đọc CCCD gắn chip cho từng dòng máy {query}.',
                            f'Tính toán chi tiết giá vốn (Landed Cost), biên đóng góp mục tiêu và trích lập quỹ dự phòng bảo hành 1 đổi 1.',
                        ],
                        'owner': 'Bộ phận Ngành hàng Di động (Category Management) & Xuất nhập khẩu',
                        'deliverable': f'Ma trận SKU chiến lược, bảng tính Unit Economics và bộ tiêu chuẩn kiểm định chất lượng {query}',
                        'gate': 'Chỉ nhập và mở bán các mã máy có đầy đủ chứng từ hợp lệ và vượt qua bài kiểm thử ROM/5G/NFC.',
                    },
                    {
                        'period': 'Ngày 31–60',
                        'goal': f'Thử nghiệm bán hàng đa kênh (O2O), gói bảo hành uy tín & chiến dịch review thực tế cho {query}',
                        'actions': [
                            f'Triển khai mở bán {query} trên gian hàng Shopee Mall / TikTok Shop kết hợp trải nghiệm thực tế tại cửa hàng với cam kết “Lỗi 1 đổi 1 trong 30 ngày - Bảo hành 18 tháng”.',
                            f'Hợp tác Reviewer công nghệ thực hiện các bài test thực chiến (chơi game nặng đo FPS/nhiệt độ, sạc nhanh, độ bền pin, chụp ảnh) cho {query}.',
                            f'Áp dụng chương trình Thu cũ đổi mới (Trade-in) và trả góp 0% để tăng tỷ lệ chốt đơn ở phân khúc máy tầm trung và cận cao cấp.',
                        ],
                        'owner': 'Đội ngũ Thương mại Điện tử, Marketing Công nghệ & Vận hành Bán lẻ',
                        'deliverable': 'Báo cáo doanh số theo SKU, ROAS quảng cáo, tỷ lệ chuyển đổi và chi phí thu hút khách hàng (CAC)',
                        'gate': 'Đạt biên lợi nhuận gộp mục tiêu và tỷ lệ khiếu nại/hoàn đơn dưới ngưỡng 2%.',
                    },
                    {
                        'period': 'Ngày 61–90',
                        'goal': f'Tối ưu vòng quay tồn kho, dịch vụ hậu mãi & mở rộng thị phần {query}',
                        'actions': [
                            f'Phân tích tốc độ bán ra (Sell-through rate) và số ngày tồn kho (DSI) của từng mẫu máy {query} qua 2 chu kỳ tháng.',
                            f'Tăng hạn mức nhập hàng cho các mã máy Hero SKU có vòng quay nhanh; xả hàng sớm các model chuẩn bị có bản kế nhiệm để tránh lỗ tồn kho.',
                            f'Chuẩn hóa trung tâm bảo hành - sửa chữa nhanh và chương trình khách hàng thân thiết để tăng tỷ lệ giới thiệu truyền miệng.',
                        ],
                        'owner': 'Giám đốc Kinh doanh, Quản lý Chuỗi cung ứng & Trung tâm Bảo hành',
                        'deliverable': f'Kế hoạch nhập hàng quý tiếp theo, báo cáo vòng quay vốn và bảng đánh giá nhà cung cấp {query}',
                        'gate': 'Vòng quay tồn kho dưới 30 ngày và biên lợi nhuận ròng sau bảo hành đạt chuẩn phê duyệt.',
                    },
                ],
                'kpis': [
                    {'name': 'Số ngày tồn kho bình quân (Days Sales of Inventory - DSI)', 'formula': '(Giá trị tồn kho bình quân / Giá vốn hàng bán) × 30 ngày', 'target': '≤ 25–30 ngày để tránh rủi ro tụt giá công nghệ', 'frequency': 'Hàng tuần'},
                    {'name': 'Biên lợi nhuận gộp sau dự phòng bảo hành', 'formula': '(Doanh thu thuần − Giá vốn nhập khẩu − Chi phí bảo hành RMA) / Doanh thu thuần', 'target': 'Đạt ngưỡng biên mục tiêu theo từng phân khúc máy (12%–18%)', 'frequency': 'Hàng tuần / Hàng tháng'},
                    {'name': 'Tỷ lệ máy bảo hành / đổi trả (RMA & Return Rate)', 'formula': 'Số máy phát sinh lỗi phần cứng hoặc đổi trả trong 30 ngày / tổng số máy bán ra', 'target': '< 1.5% trên tổng sản lượng bán ra', 'frequency': 'Hàng tuần'},
                    {'name': 'Tỷ lệ chuyển đổi đa kênh & Tỷ trọng gói Bảo hành mở rộng', 'formula': 'Số đơn hàng thành công (và số đơn mua kèm gói BH Vàng) / tổng lượt tiếp cận', 'target': 'Tỷ lệ gắn kèm gói bảo hành/phụ kiện (Attach Rate) ≥ 25%', 'frequency': 'Hàng tuần'},
                ],
            }

    if cat == 'Food & Beverage':
        is_juice = any(t in q for t in ('nuoc ep', 'dong chai', 'juice', 'detox', 'kombucha'))
        is_veg = any(t in q for t in ('chay', 'vegan', 'vegetarian', 'thuc duong'))
        peers = (
            "TrueJuice, Các thương hiệu Cold-Pressed Juice nội địa, Phúc Long, Highlands Coffee, Boost Juice"
            if is_juice else
            "Hum Vegetarian, Chay Garden, Ưu Đàm Chay, chuỗi buffet/nhà hàng chay địa phương"
            if is_veg else
            "Phê La, Highlands Coffee, Katinat Saigon Kafe, Phúc Long, The Coffee House, Cộng Cà Phê"
        )
        offer_detail = (
            f"công thức nước ép lạnh (Cold-pressed) giữ nguyên dưỡng chất tự nhiên không đường tinh luyện, bao bì đóng chai tiện lợi và gói đặt lịch giao định kỳ (Subscription) cho khách văn phòng của {query}"
            if is_juice else
            f"thực đơn ẩm thực chay thanh đạm giàu dinh dưỡng, nguồn nguyên liệu nấm - rau củ tươi sạch truy xuất nguồn gốc và không gian thưởng thức tĩnh tại của {query}"
            if is_veg else
            f"dòng thức uống chủ lực (Signature drink từ trà Ô Long đặc sản / cà phê hạt rang mộc), định lượng nguyên liệu chuẩn hóa và trải nghiệm không gian điểm bán lẫn giao hàng trực tuyến của {query}"
        )
        return {
            'sub_type': 'food_beverage',
            'peers': peers,
            'audience': f"Khách hàng nhân viên văn phòng, giới trẻ đô thị (Gen Z, Millennials), gia đình có tần suất tiêu dùng đồ uống/ẩm thực cao và nhóm khách đặt qua ứng dụng giao đồ ăn đối với {query}",
            'offer': offer_detail,
            'focus': f"tối ưu cấu trúc thực đơn (Menu Engineering), kiểm soát chặt tỷ lệ giá vốn nguyên liệu (Food Cost / COGS) và gia tăng tần suất mua lặp lại (Retention) cho {query}",
            'channels': f"Điểm bán trực tiếp (Dine-in / Take-away Kiosk), ứng dụng giao đồ ăn (GrabFood, ShopeeFood, BeFood), kênh đặt hàng trực tiếp (Zalo OA / Mini App) và đơn hàng B2B văn phòng cho {query}",
            'demand_analysis': (
                f"Đánh giá nhu cầu tiêu thụ {query} theo khung giờ cao điểm (sáng 7h–9h, trưa 11h30–14h, chiều 15h–17h hoặc ngày Rằm/Mùng 1), "
                f"sự dịch chuyển sang nguyên liệu tự nhiên ít ngọt/tốt cho sức khỏe và độ nhạy cảm với phí giao hàng.{fig_note}"
            ),
            'competition_analysis': (
                f"Đối chiếu mức giá trung bình mỗi ly/phần ăn (35.000đ–75.000đ), chất lượng nguyên liệu cốt lõi, mật độ điểm bán và ưu đãi combo trên FoodApps của {query} "
                f"với các thương hiệu cùng phân khúc ({peers})."
            ),
            'market_gap': (
                f"Khoảng trống cần khai thác cho {query}: tối ưu hóa dòng sản phẩm Signature có biên lợi nhuận cao (>68%), đóng gói giữ nhiệt/giữ lạnh chuẩn vị khi giao xa "
                f"và gói đặt hàng theo nhóm văn phòng (Group Order / Weekly Subscription) giúp giảm chi phí chiết khấu sàn."
            ),
            'pricing_reason': (
                f"Giá bán đề xuất cho {query} phải tính toán trên định mức nguyên liệu tiêu chuẩn (BOM/Recipe Cost), chi phí bao bì, chiết khấu nền tảng giao đồ ăn (20%–25%), "
                f"chi phí mặt bằng/nhân sự theo ca và mức sẵn lòng chi trả tại khu vực mục tiêu."
            ),
            'pricing_methods': [
                {'name': 'Theo định mức giá vốn (Food Cost / BOM)', 'action': f'Thiết lập bảng định lượng chuẩn cho từng món của {query}, giữ tỷ lệ giá vốn nguyên liệu + bao bì ở ngưỡng 28%–35% giá bán thực thu.'},
                {'name': 'Thiết kế thực đơn theo tầng giá (Menu Engineering)', 'action': f'Phân nhóm món dẫn khách (chim mồi), món chủ lực biên lợi nhuận cao (Star items) và thiết kế Combo/Upsell size hoặc topping để tăng giá trị đơn hàng trung bình (AOV) cho {query}.'},
                {'name': 'Phân tách cấu trúc giá tại quán & kênh FoodApp', 'action': f'Cân đối biểu giá và chương trình khuyến mãi trên GrabFood/ShopeeFood cho {query} sao cho sau khi trừ chiết khấu nền tảng vẫn bảo toàn biên đóng góp dương.'},
            ],
            'required_inputs': [
                f'Bảng định mức nguyên liệu (Recipe BOM) và chi phí bao bì chi tiết cho từng món của {query}',
                'Chi phí cố định hàng tháng (thuê mặt bằng, nhân sự cơ bản, điện nước, khấu hao thiết bị pha chế/bếp)',
                'Mức giá niêm yết và chương trình combo của 5 đối thủ trực tiếp trong bán kính 2km hoặc cùng ngách',
                'Tỷ trọng doanh thu giữa kênh tại chỗ (Dine-in/Take-away) và kênh ứng dụng giao hàng (Delivery)',
            ],
            'risks_tuples': [
                ('An toàn thực phẩm & bảo quản nguyên liệu', f'Chất lượng nguyên liệu tươi (trái cây, sữa, cốt trà, rau nấm), nhiệt độ bảo quản lạnh (2–6°C) và hạn sử dụng ngắn của {query} cần kiểm soát nghiêm ngặt.', 'Theo dõi sổ kiểm thực 3 bước, nhiệt độ tủ mát, hạn dùng theo ca và phản hồi cảm quan của khách.', f'Chuẩn hóa quy trình SOP pha chế/chế biến, kiểm định nguồn cung đạt chuẩn VSATTP và truy xuất lô nguyên liệu cho {query}.'),
                ('Giá nguyên liệu biến động & hao hụt hủy hàng', f'Biến động giá nông sản/nguyên liệu theo mùa và tỷ lệ hủy hàng cuối ngày có thể làm xói mòn biên đóng góp của {query}.', 'Đo tỷ lệ Food Cost thực tế so với định mức lý thuyết (Variance) và tỷ lệ hủy nguyên liệu mỗi ca.', 'Áp dụng dự báo lượng bán theo ngày trong tuần/thời tiết để chuẩn bị cốt nguyên liệu vừa đủ và ký hợp đồng bao tiêu giá với nhà cung cấp.'),
                ('Nhu cầu mua lặp lại & lệ thuộc chiết khấu FoodApp', f'Khách hàng thử nghiệm {query} giai đoạn đầu vì khuyến mãi nhưng tỷ lệ quay lại thấp hoặc biên lợi nhuận bị bào mòn bởi phí sàn giao đồ ăn.', 'Theo dõi tỷ lệ khách mua lại trong 30 ngày (Retention Rate), CAC và biên đóng góp ròng theo từng kênh.', 'Chuyển đổi khách từ sàn FoodApp sang kênh thành viên riêng (Zalo Mini App / Thẻ tích điểm) và thử nghiệm quy mô nhỏ trước khi mở thêm điểm bán.'),
            ],
            'action_plan': [
                {
                    'period': 'Ngày 1–30',
                    'goal': f'Chuẩn hóa công thức định lượng (BOM), kiểm định ATVSTP & điểm hòa vốn cho {query}',
                    'actions': [
                        f'Hoàn thiện bảng định mức nguyên liệu (Recipe Costing), quy trình bảo quản lạnh và hồ sơ chứng nhận An toàn thực phẩm cho {query}.',
                        f'Khảo sát thực tế 30–50 khách hàng mục tiêu (thử mù hương vị - Blind Taste Test, độ ngọt, bao bì, mức giá chấp nhận) đối với dòng món chủ lực của {query}.',
                        f'Tính toán chính xác biên đóng góp trên mỗi đơn hàng (sau khi trừ bao bì và phí sàn FoodApp) cùng sản lượng hòa vốn theo ngày.',
                    ],
                    'owner': 'Bộ phận R&D Pha chế/Bếp, Quản lý Chất lượng & Tài chính',
                    'deliverable': f'Bộ SOP công thức chuẩn, bảng tính giá vốn BOM và mô hình điểm hòa vốn của {query}',
                    'gate': 'Tỷ lệ giá vốn nguyên liệu chuẩn ≤ 32% và hoàn tất đầy đủ tiêu chuẩn vệ sinh an toàn thực phẩm.',
                },
                {
                    'period': 'Ngày 31–60',
                    'goal': f'Thử nghiệm bán hàng thực tế, tối ưu Menu Combo & kênh giao hàng cho {query}',
                    'actions': [
                        f'Triển khai bán thử nghiệm tại khu vực mục tiêu (tại điểm bán và trên GrabFood/ShopeeFood/Zalo OA) tập trung vào 3–5 món Signature của {query}.',
                        f'Thử nghiệm gói Combo theo khung giờ (Bữa sáng/Trà chiều văn phòng hoặc Đặt lịch định kỳ theo tuần) để đẩy giá trị đơn hàng trung bình (AOV).',
                        f'Theo dõi sát thời gian ra món, chất lượng sản phẩm khi giao đến tay khách, tỷ lệ hao hụt nguyên liệu cuối ngày và điểm đánh giá (Rating) tuần.',
                    ],
                    'owner': 'Quản lý Vận hành Điểm bán & Đội ngũ Marketing Điểm bán (Local Store Marketing)',
                    'deliverable': 'Báo cáo doanh thu theo khung giờ, biên lợi nhuận thực tế theo kênh và tỷ lệ khách hàng quay lại lần 2',
                    'gate': 'Đạt điểm đánh giá khách hàng ≥ 4.6/5.0 và biên đóng góp ròng dương trên mọi kênh bán.',
                },
                {
                    'period': 'Ngày 61–90',
                    'goal': f'Tối ưu tỷ lệ giữ chân khách hàng (Retention) & quyết định quy mô điểm bán {query}',
                    'actions': [
                        f'Đánh giá hiệu quả tài chính của {query} qua ít nhất 2 kỳ tháng liên tiếp: doanh thu/ngày, tỷ lệ khách cũ quay lại (Repeat Rate) và chênh lệch hao hụt kho.',
                        f'Loại bỏ các món bán chậm gây tồn nguyên liệu; tập trung truyền thông và tối ưu chuỗi cung ứng cho nhóm món mang lại 80% lợi nhuận.',
                        f'Chỉ quyết định nhân rộng điểm bán hoặc tăng công suất sản xuất cho {query} khi mô hình đơn vị (Unit Economics) đã chứng minh có lãi bền vững.',
                    ],
                    'owner': 'Chủ đầu tư / Ban Giám đốc Vận hành & Bộ phận Kế toán Quản trị',
                    'deliverable': f'Báo cáo kiểm toán Unit Economics 90 ngày, danh mục thực đơn tối ưu và kế hoạch mở rộng của {query}',
                    'gate': 'Đạt sản lượng hòa vốn ổn định và tỷ lệ khách quay lại sau 30 ngày đạt ngưỡng mục tiêu.',
                },
            ],
            'kpis': [
                {'name': 'Tỷ lệ giá vốn thực phẩm & bao bì (COGS / Food Cost %)', 'formula': '(Giá trị nguyên liệu + bao bì xuất dùng thực tế) / Doanh thu thuần', 'target': 'Kiểm soát trong ngưỡng 28%–35%, chênh lệch định mức < 1.5%', 'frequency': 'Hàng tuần'},
                {'name': 'Giá trị đơn hàng trung bình (AOV) & Biên đóng góp/đơn', 'formula': 'Doanh thu thuần / Tổng số hóa đơn; trừ chi phí biến đổi và chiết khấu sàn', 'target': 'Tăng AOV qua Combo/Upsell, đảm bảo biên đóng góp ròng ≥ 45%', 'frequency': 'Hàng tuần'},
                {'name': 'Tỷ lệ khách hàng mua lặp lại sau 30 ngày (30-Day Retention)', 'formula': 'Số khách hàng đặt mua từ lần thứ 2 trở lên trong tháng / Tổng khách hàng mới', 'target': 'Đạt ≥ 30%–35% đối với nhóm đồ uống và suất ăn định kỳ', 'frequency': 'Hàng tháng'},
                {'name': 'Tỷ lệ hao hụt & hủy nguyên liệu tươi (Wastage Rate)', 'formula': 'Giá trị nguyên liệu/thành phẩm hủy cuối ca / Tổng giá trị nguyên liệu nhập', 'target': '< 2.5% nhờ dự báo chuẩn lượng bán theo ca', 'frequency': 'Hàng ngày / Hàng tuần'},
            ],
        }

    # Specialized profiles for all other commercial categories
    category_profiles = {
        'Electric Vehicles': {
            'peers': 'VinFast VF 3 / VF 5 / VF 6 / VF 7, BYD Atto 3 / Dolphin, Wuling Mini EV, Hyundai Ioniq 5',
            'audience': f'Khách hàng cá nhân và gia đình đô thị mua xe lần đầu hoặc xe thứ hai, tài xế dịch vụ vận tải xanh và doanh nghiệp chuyển đổi đội xe sang {query}',
            'offer': f'tổng chi phí sở hữu (TCO: giá xe kèm pin/thuê pin, chi phí sạc điện cần đối chiếu với chi phí nhiên liệu cùng điều kiện), phạm vi di chuyển mỗi lần sạc (km/lần sạc), mạng lưới trạm sạc nhanh DC và chính sách bảo hành pin đã công bố của {query}',
            'focus': f'tối ưu bài toán tổng chi phí sở hữu (TCO), mở rộng trải nghiệm lái thử thực tế (Test Drive) và giải tỏa lo ngại về hạ tầng trạm sạc cho {query}',
            'channels': f'Hệ thống Showroom 3S / Đại lý ủy quyền, sự kiện Lái thử cuối tuần (Roadshow & Test Drive), kênh tư vấn tài chính trả góp ngân hàng và cộng đồng người dùng xe điện đối với {query}',
        },
        'Technology & Gaming': {
            'peers': 'ASUS ROG / TUF Gaming, Lenovo Legion / LOQ, Acer Predator / Nitro, MSI Gaming, Dell Alienware / Inspiron, Apple MacBook',
            'audience': f'Game thủ, kỹ sư lập trình - AI, nhà sáng tạo nội dung đồ họa, sinh viên khối ngành kỹ thuật - kinh tế và doanh nghiệp trang bị phần cứng {query}',
            'offer': f'hiệu năng xử lý CPU/GPU (TGP, khả năng tản nhiệt thực tế, màn hình chuẩn màu sRGB/OLED tần số quét cao), khả năng nâng cấp RAM/SSD và dịch vụ bảo hành chính hãng theo điều kiện đã công bố của {query}',
            'focus': f'định vị hiệu năng thực tế theo nhu cầu chuyên biệt (Gaming / Đồ họa / AI / Văn phòng) và tối ưu gói bán kèm phụ kiện - bảo hành cho {query}',
            'channels': f'Chuỗi bán lẻ CNTT chuyên biệt (GearVN, Phong Vũ, CellphoneS,HACOM, FPT Shop), sàn TMĐT chính hãng và cộng đồng công nghệ/Esports cho {query}',
        },
        'Beauty & Skincare': {
            'peers': 'Cocoon Vietnam, La Roche-Posay, CeraVe, Skin1004, The Ordinary, Paula’s Choice, Anessa, L’Oréal Paris',
            'audience': f'Người tiêu dùng nữ và nam (18–40 tuổi) quan tâm chăm sóc da khoa học theo tình trạng da (da dầu mụn, nhạy cảm, lão hóa) và ưu tiên bảng thành phần minh bạch của {query}',
            'offer': f'nồng độ hoạt chất chuẩn khoa học (Niacinamide, BHA, Retinol, Centella, chiết xuất thuần chay), hồ sơ công bố mỹ phẩm hợp pháp của Bộ Y tế, kiểm nghiệm da liễu không kích ứng và dung tích dùng thử/full-size của {query}',
            'focus': f'xây dựng niềm tin bằng bằng chứng lâm sàng - thành phần minh bạch, tối ưu chuyển đổi qua Social Commerce (TikTok Shop/Shopee Mall) và tăng tỷ lệ mua lặp lại khi hết chu kỳ dùng 45–60 ngày cho {query}',
            'channels': f'Gian hàng chính hãng Shopee Mall / TikTok Shop / Lazada Mall, chuỗi bán lẻ mỹ phẩm (Hasaki, Guardian, Watsons, Sociolla), phòng khám da liễu và mạng lưới KOC/Beauty Blogger review {query}',
        },
        'Real Estate & Housing': {
            'peers': 'Vinhomes, Masterise Homes, Nam Long (Akari/Mizuki/Waterpoint), Khang Điền, Ecopark, Becamex Tokyu, Phú Mỹ Hưng',
            'audience': f'Người mua ở thực (gia đình trẻ, chuyên gia làm việc tại đô thị/KCN), nhà đầu tư khai thác dòng tiền cho thuê dài hạn và khách hàng tích sản đối với {query}',
            'offer': f'tính minh bạch pháp lý (quy hoạch 1/500, giấy phép xây dựng, sổ hồng), vị trí kết nối hạ tầng giao thông (Vành đai, Metro, Cao tốc), tiến độ bàn giao thực tế và gói hỗ trợ lãi suất/giãn tiến độ thanh toán của {query}',
            'focus': f'minh bạch hóa hồ sơ pháp lý - tiến độ xây dựng, thiết kế phương án dòng tiền thanh toán vừa sức mua ở thực và khai thác tỷ suất cho thuê thực tế cho {query}',
            'channels': f'Sàn giao dịch bất động sản F1, sự kiện tham quan nhà mẫu & thực địa dự án (Site Tour), kênh tư vấn tài chính ngân hàng liên kết bảo lãnh và cổng thông tin quy hoạch cho {query}',
        },
        'FinTech & Digital Finance': {
            'peers': 'Vietcombank Digibank, Techcombank Mobile, MB Bank, MoMo, VNPay, ZaloPay, Cake by VPBank, TCBS',
            'audience': f'Người dùng cá nhân giao dịch ngân hàng số/thanh toán không tiền mặt hàng ngày, hộ kinh doanh SME chấp nhận thanh toán QR và nhà đầu tư cá nhân sử dụng {query}',
            'offer': f'tốc độ giao dịch liền mạch 24/7, chuẩn bảo mật xác thực sinh trắc học theo quy định Ngân hàng Nhà nước (Quyết định 2345), biểu phí minh bạch và hệ sinh thái tiện ích thanh toán - tiết kiệm - tín dụng của {query}',
            'focus': f'tối ưu tỷ lệ định danh eKYC thành công, gia tăng tần suất giao dịch hoạt động hàng tháng (MAU) và kiểm soát chặt rủi ro gian lận/nợ xấu cho {query}',
            'channels': f'Ứng dụng di động (App Store / Google Play), mạng lưới điểm chấp nhận thanh toán QR (Merchant O2O), tích hợp API/Mini App trên siêu ứng dụng và kênh đối tác tài chính của {query}',
        },
        'Digital Services & SaaS': {
            'peers': 'FPT Software, Viettel Solutions, MISA AMIS, Base.vn, KiotViet, Haravan, VNG Cloud, Zoho/Salesforce',
            'audience': f'Doanh nghiệp SME, hộ kinh doanh chuyển đổi số và các tập đoàn lớn cần tối ưu quy trình quản trị, kế toán, bán hàng đa kênh hoặc hạ tầng đám mây qua {query}',
            'offer': f'khả năng tự động hóa quy trình nghiệp vụ, giao diện dễ triển khai cho nhân sự không chuyên IT, khả năng kết nối API (hóa đơn điện tử, thuế, ngân hàng, sàn TMĐT) và cam kết SLA bảo mật dữ liệu của {query}',
            'focus': f'rút ngắn thời gian triển khai dùng thử có giá trị (Time-to-Value trong 7–14 ngày), tăng tỷ lệ chuyển đổi từ gói Trial sang thuê bao năm (ARR) và giảm tỷ lệ rời bỏ (Churn Rate) cho {query}',
            'channels': f'Đội ngũ tư vấn giải pháp B2B trực tiếp (Inside/Field Sales), chương trình đăng ký dùng thử (Free Trial / PoC), hội thảo chuyển đổi số ngành và mạng lưới đối tác triển khai cho {query}',
        },
        'Healthcare & Fitness': {
            'peers': 'Hệ thống Y tế Vinmec, Bệnh viện Đa khoa Tâm Anh, Nhà thuốc FPT Long Châu, Pharmacity, Hệ thống Tiêm chủng VNVC, Medlatec',
            'audience': f'Bệnh nhân và gia đình có nhu cầu khám chữa bệnh chuyên khoa/tầm soát định kỳ, người tiêu dùng mua dược phẩm chính hãng và người luyện tập chăm sóc sức khỏe chủ động với {query}',
            'offer': f'trình độ chuyên môn của đội ngũ y bác sĩ/dược sĩ, phác đồ chuẩn Bộ Y tế, trang thiết bị chẩn đoán hiện đại, nguồn gốc thuốc đạt chuẩn GPP và quy trình đặt lịch giảm thời gian chờ đợi của {query}',
            'focus': f'nâng cao chất lượng chuyên môn lâm sàng, công khai minh bạch bảng giá dịch vụ y tế/thuốc và số hóa hồ sơ sức khỏe theo dõi định kỳ cho {query}',
            'channels': f'Cơ sở khám chữa bệnh / nhà thuốc vật lý, tổng đài và ứng dụng đặt lịch khám trực tuyến, liên kết Bảo hiểm Y tế / Bảo hiểm sức khỏe thương mại và truyền thông giáo dục y khoa chính thống cho {query}',
        },
        'Logistics & Supply Chain': {
            'peers': 'Viettel Post, Giao Hàng Tiết Kiệm (GHTK), Giao Hàng Nhanh (GHN), J&T Express, SPX Express, Gemadept, Tân Cảng Sài Gòn',
            'audience': f'Nhà bán hàng thương mại điện tử (Shopee, TikTok Shop), doanh nghiệp sản xuất xuất nhập khẩu và chuỗi bán lẻ cần dịch vụ vận chuyển - kho vận {query}',
            'offer': f'tốc độ giao nhận toàn trình (SLA đúng hẹn), tỷ lệ giao hàng thành công lần đầu, năng lực đối soát tiền thu hộ (COD) nhanh chóng và chi phí vận chuyển/lưu kho tối ưu theo trọng lượng/tuyến đường của {query}',
            'focus': f'tối ưu mật độ tuyến giao nhận để giảm chi phí/đơn, kéo giảm tỷ lệ hoàn hàng (RTS) và tự động hóa kho bãi (Fulfillment/WMS) cho {query}',
            'channels': f'Tích hợp trực tiếp API trên các sàn TMĐT/phần mềm quản lý bán hàng, đội ngũ kinh doanh B2B ký hợp đồng sản lượng tháng và mạng lưới bưu cục thu gom toàn quốc của {query}',
        },
        'Tourism & Hospitality': {
            'peers': 'Vinpearl Resort, Sun World, Vietnam Airlines, Vietjet Air, Traveloka, Booking.com, Agoda, Saigontourist',
            'audience': f'Khách du lịch nội địa (gia đình, nhóm bạn tự túc), khách quốc tế (Inbound) và khối doanh nghiệp tổ chức hội nghị nghỉ dưỡng (MICE) lựa chọn {query}',
            'offer': f'trải nghiệm lưu trú - nghỉ dưỡng - khám phá bản địa đặc sắc, gói Combo linh hoạt (vé máy bay + phòng + vui chơi), chính sách hoàn hủy rõ ràng và chất lượng dịch vụ chuẩn sao của {query}',
            'focus': f'tối ưu công suất lấp đầy phòng/chuyến (Occupancy Rate) giữa mùa cao điểm và thấp điểm, đẩy mạnh đặt dịch vụ trực tiếp (Direct Booking) và nâng điểm đánh giá khách hàng cho {query}',
            'channels': f'Kênh đặt phòng trực tiếp (Website/Fanpage chính thức), các nền tảng OTA (Booking.com, Agoda, Traveloka, Klook), đại lý lữ hành B2B/MICE và nội dung review du lịch trải nghiệm thực tế về {query}',
        },
        'Fashion & E-Commerce': {
            'peers': 'Coolmate, Uniqlo Vietnam, Zara, Routine, IVY moda, Biti’s Hunter, Shopee Mall / TikTok Shop Local Brands',
            'audience': f'Người tiêu dùng thời trang yêu thích phong cách hiện đại, chất liệu thoáng mát bền màu phù hợp khí hậu Việt Nam và trải nghiệm mua sắm trực tuyến đổi trả dễ dàng với {query}',
            'offer': f'chất liệu vải và phom dáng chuẩn người Việt, bảng size chính xác, mức giá hợp lý theo bộ sưu tập mùa và chính sách đổi trả linh hoạt 30–60 ngày của {query}',
            'focus': f'tối ưu vòng quay bộ sưu tập (giảm tồn kho lệch size/màu), nâng cao tỷ lệ chuyển đổi qua Livestream/Video ngắn và kiểm soát tỷ lệ hoàn hàng cho {query}',
            'channels': f'Gian hàng TikTok Shop, Shopee Mall, Lazada Mall, Website D2C riêng, hệ thống cửa hàng trải nghiệm (Flagship Store) và mạng lưới KOC phối đồ (Lookbook/OOTD) cho {query}',
        },
        'FMCG & Consumer Goods': {
            'peers': 'Masan Consumer, Acecook Việt Nam, Vinamilk, TH true MILK, Unilever, Suntory PepsiCo, Bách Hóa Xanh',
            'audience': f'Hộ gia đình Việt Nam ở cả đô thị và nông thôn, người nội trợ mua sắm tiêu dùng thiết yếu hàng tuần và mạng lưới tạp hóa (GT) / siêu thị (MT) phân phối {query}',
            'offer': f'chất lượng sản phẩm đồng nhất, hương vị hợp khẩu vị đại chúng, quy cách đóng gói tiện lợi (gói lẻ, lốc, thùng gia đình) với mức giá dễ tiếp cận hàng ngày của {query}',
            'focus': f'mở rộng độ phủ điểm bán (Numeric & Weighted Distribution) trên cả kênh truyền thống (GT) lẫn hiện đại (MT/E-commerce) và duy trì vòng quay tiêu thụ nhanh tại quầy kệ cho {query}',
            'channels': f'Hệ thống siêu thị & chuỗi bách hóa (Bách Hóa Xanh, WinMart, Co.opmart), mạng lưới nhà phân phối - đại lý tạp hóa truyền thống (GT) và gian hàng FMCG trực tuyến cho {query}',
        },
        'Smartphones & Mobile': {
            'peers': 'iPhone 16 Pro Max / 15 Series, Samsung Galaxy S24 Ultra / Z Fold6, Xiaomi 14 Series, OPPO Find / Reno Series, Vivo X Series',
            'audience': f'Người tiêu dùng nâng cấp điện thoại thông minh, giới trẻ sáng tạo nội dung, nhân sự văn phòng và khách hàng mua trả góp qua hệ thống bán lẻ chính hãng đối với {query}',
            'offer': f'hiệu năng vi xử lý, hệ thống camera nhiếp ảnh điện toán, thời lượng pin - sạc nhanh, cam kết cập nhật phần mềm dài hạn và chính sách thu cũ đổi mới (Trade-in) chính hãng của {query}',
            'focus': f'tối ưu gói tài chính Thu cũ đổi mới - Trả góp 0%, đẩy mạnh bán kèm hệ sinh thái phụ kiện/bảo hành mở rộng và kiểm soát vòng quay tồn kho theo chu kỳ ra mắt của {query}',
            'channels': f'Hệ thống bán lẻ ủy quyền (Thế Giới Di Động, FPT Shop, CellphoneS, Viettel Store, Hoàng Hà Mobile), gian hàng chính hãng Shopee Mall / TikTok Shop và kênh review công nghệ cho {query}',
        },
        'Audio & Consumer Electronics': {
            'peers': 'Sony WH-1000XM5 / WF-1000XM5, Apple AirPods Pro 2, Bose QuietComfort Ultra, Marshall Stanmore III, JBL Charge 5, Sennheiser Momentum 4',
            'audience': f'Người yêu âm nhạc, nhân viên văn phòng cần chống ồn chủ động (ANC), người tập thể thao và khách hàng trang bị âm thanh giải trí gia đình/di động với {query}',
            'offer': f'chất lượng âm thanh đặc trưng (Codec Hi-Res/LDAC/Spatial Audio), hiệu quả chống ồn chủ động (ANC), thời lượng pin thực tế, độ bền kháng nước và chế độ bảo hành chính hãng 12 tháng của {query}',
            'focus': f'tạo điểm chạm nghe thử thực tế tại điểm bán, truyền thông trải nghiệm âm thanh/chống ồn qua video ngắn và tối ưu combo bán kèm thiết bị di động cho {query}',
            'channels': f'Chuỗi bán lẻ công nghệ & âm thanh chuyên sâu (CellphoneS, Mai Nguyên, Xuân Vũ Audio, FPT Shop), Shopee Mall / Lazada Mall / TikTok Shop và cộng đồng Audiophile cho {query}',
        },
        'Smart Home & IoT': {
            'peers': 'Roborock S8 Pro Ultra, Ecovacs Deebot X2 Omni, Dreame L20 Ultra, Xiaomi Smart Home, Ezviz Camera, Máy lọc nước/không khí Karofi & Philips',
            'audience': f'Gia đình trẻ tại các căn hộ chung cư, nhà phố hiện đại ưu tiên tự động hóa việc nhà, giám sát an ninh từ xa và nâng cao chất lượng không khí - nguồn nước với {query}',
            'offer': f'khả năng vận hành tự động thông minh (điều hướng LiDAR/AI, tự giặt sấy giẻ, cảnh báo an ninh thời gian thực qua App tiếng Việt), độ bền linh kiện và dịch vụ lắp đặt - bảo trì tận nhà của {query}',
            'focus': f'chứng minh hiệu quả tiết kiệm thời gian qua video thử nghiệm thực tế, chuẩn hóa dịch vụ lắp đặt - thay thế phụ kiện định kỳ (lõi lọc, chổi, túi rác) và hậu mãi tận nơi cho {query}',
            'channels': f'Hệ thống siêu thị điện máy (Điện Máy Xanh, Nguyễn Kim, MediaMart), đại lý Smart Home ủy quyền, gian hàng Shopee Mall / TikTok Shop và hội nhóm cư dân chung cư cho {query}',
        },
        'Education & EdTech': {
            'peers': 'Coursera, Udemy, ELSA Speak, Prep.vn, Kyna English, MindX Technology School, VUS / ILA / British Council',
            'audience': f'Học sinh - sinh viên, người đi làm cần nâng cao kỹ năng chuyên môn (AI, Lập trình, Ngoại ngữ IELTS/TOEIC, Quản trị) và doanh nghiệp đào tạo nội bộ qua {query}',
            'offer': f'lộ trình học tập cá nhân hóa có chấm chữa/tương tác, hệ thống bài tập thực hành dự án thực tế, cam kết chuẩn đầu ra minh bạch và chứng chỉ hoàn thành khóa học của {query}',
            'focus': f'nâng cao tỷ lệ học viên hoàn thành khóa học (Completion Rate), tối ưu phễu học thử miễn phí (Free Trial / Placement Test) sang đăng ký trả phí và gia tăng giới thiệu học viên mới cho {query}',
            'channels': f'Nền tảng học trực tuyến (Web/App), hội thảo chuyên đề (Webinar) & bài kiểm tra năng lực đầu vào miễn phí, cộng đồng học tập Facebook/TikTok/YouTube và kênh B2B doanh nghiệp của {query}',
        },
    }

    if cat in category_profiles:
        prof = category_profiles[cat]
        return {
            'sub_type': key(cat).replace(' ', '_'),
            'peers': prof['peers'],
            'audience': prof['audience'],
            'offer': prof['offer'],
            'focus': prof['focus'],
            'channels': prof['channels'],
            'demand_analysis': (
                f"Phân tích động lực nhu cầu thực tế đối với “{query}” trong lĩnh vực {context['label'].lower()}: "
                f"tần suất sử dụng, yếu tố quyết định xuống tiền, khả năng chi trả theo phân khúc và mức độ chuyển đổi từ tìm kiếm thông tin sang giao dịch thực.{fig_note}"
            ),
            'competition_analysis': (
                f"Đối chiếu trực tiếp “{query}” với các đối thủ và lựa chọn thay thế cùng phân khúc tại Việt Nam ({prof['peers']}) "
                f"theo tiêu chí: {', '.join(context['criteria'][:4]).lower()}."
            ),
            'market_gap': (
                f"Khoảng trống chiến lược cần kiểm nghiệm cho “{query}”: tối ưu hóa {prof['offer']} ở phân khúc khách hàng mục tiêu "
                f"nơi các đối thủ hiện hữu chưa đáp ứng trọn vẹn về tốc độ phục vụ, minh bạch chi phí hoặc hậu mãi."
            ),
            'pricing_reason': (
                f"Chiến lược giá cho “{query}” phải dựa trên cấu trúc chi phí đơn vị (Unit Cost), mức giá thực bán của nhóm đối sánh ({prof['peers']}) "
                f"và giá trị tăng thêm mà khách hàng nhận được."
            ),
            'pricing_methods': [
                {'name': 'Định giá theo cấu trúc chi phí & biên mục tiêu', 'action': f'Tính đủ giá vốn, chi phí vận hành, hoa hồng kênh phân phối và hậu mãi trên mỗi đơn vị {query} trước khi niêm yết giá.'},
                {'name': 'Đối chiếu giá trị tương quan với đối thủ cùng phân khúc', 'action': f'So sánh trực tiếp mức giá và quyền lợi đi kèm của {query} với các lựa chọn thay thế ({prof["peers"]}) cùng thời điểm.'},
                {'name': 'Thiết kế gói sản phẩm (Bundling / Tiered Pricing)', 'action': f'Xây dựng 2–3 mức gói tiêu chuẩn và nâng cao cho {query} để mở rộng tệp khách hàng mà không cần giảm giá đại trà.'},
            ],
            'required_inputs': [
                f'Đơn vị tính, cấu hình gói sản phẩm/dịch vụ và giá vốn chi tiết của {query}',
                'Chi phí cố định, chi phí tiếp thị thu hút khách hàng (CAC) và chiết khấu kênh phân phối',
                f'Bảng giá thực tế của nhóm đối thủ trực tiếp ({prof["peers"]}) cùng địa bàn và thời kỳ',
                'Dữ liệu tỷ lệ chuyển đổi mua hàng, tỷ lệ giữ chân khách hàng và biên lợi nhuận mục tiêu',
            ],
            'risks_tuples': [
                ('Áp lực cạnh tranh & chi phí chuyển đổi khách hàng', f'Khách hàng của {query} có nhiều lựa chọn thay thế trực tiếp từ {prof["peers"]}, dễ dẫn đến cạnh tranh giá nếu thiếu khác biệt cốt lõi.', 'Theo dõi tỷ lệ chuyển đổi báo giá/giỏ hàng, lý do từ chối mua và biến động giá đối thủ.', f'Tập trung củng cố lợi thế khác biệt về {prof["offer"]} thay vì cuốn vào cuộc chiến giảm giá.'),
                ('Chi phí thu hút khách hàng (CAC) & dòng tiền vận hành', f'Chi phí quảng cáo đa kênh hoặc chiết khấu đại lý cho {query} có thể vượt biên đóng góp nếu tỷ lệ mua lặp lại thấp.', 'Theo dõi tỷ số LTV/CAC, biên đóng góp ròng trên mỗi đơn vị và vòng quay dòng tiền theo tuần.', 'Đặt trần ngân sách thử nghiệm cho từng kênh, cắt giảm ngay kênh có CAC vượt ngưỡng cho phép.'),
                ('Chất lượng vận hành, hậu mãi & tuân thủ quy định', f'Sự cố về chất lượng sản phẩm/dịch vụ, tiến độ cung ứng hoặc yêu cầu pháp lý chuyên ngành có thể ảnh hưởng trực tiếp đến uy tín của {query}.', 'Theo dõi tỷ lệ lỗi/khiếu nại, thời gian xử lý bảo hành/hỗ trợ (SLA) và hồ sơ pháp lý.', f'Chuẩn hóa quy trình kiểm soát chất lượng đầu ra và cam kết hậu mãi minh bạch cho {query}.'),
            ],
            'action_plan': [
                {
                    'period': 'Ngày 1–30',
                    'goal': f'Xác lập đường cơ sở dữ liệu, đối sánh cạnh tranh & Unit Economics cho {query}',
                    'actions': [
                        f'Thu thập và chuẩn hóa bộ dữ liệu thực tế của {query} theo các tiêu chí trọng tâm: {", ".join(context["criteria"][:4])}.',
                        f'Lập bảng đối sánh trực tiếp {query} với nhóm cùng phân khúc ({prof["peers"]}) về mức giá, tính năng/dịch vụ và kênh phân phối.',
                        f'Khảo sát nhóm {prof["audience"]} để xác nhận 3 lý do chọn mua hàng đầu và tính toán điểm hòa vốn đơn vị.',
                    ],
                    'owner': 'Nhóm Nghiên cứu Thị trường, Sản phẩm & Tài chính Quản trị',
                    'deliverable': f'Báo cáo đối sánh cạnh tranh, bảng tính Unit Economics và bộ KPI đường cơ sở của {query}',
                    'gate': 'Đầy đủ số liệu giá vốn, giá đối thủ có nguồn kiểm chứng và định nghĩa KPI thống nhất.',
                },
                {
                    'period': 'Ngày 31–60',
                    'goal': f'Thử nghiệm {prof["focus"]}',
                    'actions': [
                        f'Chuẩn hóa gói giải pháp và thông điệp cốt lõi làm nổi bật {prof["offer"]}.',
                        f'Triển khai chiến dịch thử nghiệm có kiểm soát trên các kênh trọng điểm ({prof["channels"]}); gắn mã đo lường chuyển đổi và CAC theo từng tuần.',
                        f'Thu thập phản hồi thực tế của khách hàng sau trải nghiệm để xử lý ngay các điểm nghẽn trong phễu chuyển đổi và dịch vụ hậu mãi.',
                    ],
                    'owner': 'Bộ phận Kinh doanh, Marketing Tăng trưởng & Vận hành',
                    'deliverable': f'Báo cáo kết quả thử nghiệm kênh, chi phí mỗi chuyển đổi (CPA/CAC) và biên đóng góp thực tế của {query}',
                    'gate': 'Tỷ lệ chuyển đổi và chi phí thu hút khách hàng nằm trong ngưỡng an toàn của mô hình tài chính.',
                },
                {
                    'period': 'Ngày 61–90',
                    'goal': f'Tối ưu hóa hiệu suất kênh & quyết định mở rộng quy mô cho {query}',
                    'actions': [
                        f'Đối chiếu dữ liệu hiệu quả kinh doanh của {query} qua ít nhất 2 chu kỳ đo lường liên tiếp so với đường cơ sở ban đầu.',
                        f'Dồn ngân sách và nguồn lực vào phân khúc khách hàng và kênh phân phối đạt ROI dương; dừng hoặc tái cấu trúc các hoạt động chưa đạt chuẩn.',
                        f'Cập nhật dữ liệu lịch sử mới vào hệ thống dự báo Học máy để hiệu chỉnh kế hoạch cung ứng và ngân sách quý tiếp theo.',
                    ],
                    'owner': 'Ban Giám đốc Điều hành & Bộ phận Kế hoạch Tài chính',
                    'deliverable': f'Kế hoạch mở rộng quý tiếp theo, phân bổ ngân sách theo ROI và lộ trình quản trị rủi ro cho {query}',
                    'gate': 'Chứng minh được biên đóng góp dương và khả năng vận hành ổn định trên dữ liệu thực tế.',
                },
            ],
            'kpis': [
                {'name': 'Tỷ lệ chuyển đổi theo phễu tiếp cận (Conversion Rate)', 'formula': 'Số giao dịch/hành động mục tiêu hoàn tất / tổng lượt khách hàng tiềm năng tiếp cận hợp lệ', 'target': 'Xác lập đường cơ sở trong 30 ngày đầu và cải thiện 15%–25% sau tối ưu phễu', 'frequency': 'Hàng tuần'},
                {'name': 'Chi phí thu hút khách hàng (CAC) so với Biên đóng góp', 'formula': 'Tổng chi phí Marketing & Bán hàng / số khách hàng mới phát sinh giao dịch', 'target': 'CAC < 30% giá trị vòng đời khách hàng (LTV) hoặc thu hồi vốn ngay trong đơn đầu/kỳ đầu', 'frequency': 'Hàng tuần'},
                {'name': 'Tỷ lệ giữ chân / mua lặp lại & Hài lòng khách hàng (CSAT)', 'formula': 'Số khách hàng tiếp tục sử dụng hoặc giới thiệu / tổng khách hàng hiện hữu', 'target': 'Điểm hài lòng ≥ 4.5/5.0 và tỷ lệ khiếu nại/hoàn trả dưới ngưỡng kiểm soát ngành', 'frequency': 'Hàng tháng'},
                {'name': 'Sai số dự báo định lượng (MAE / MAPE)', 'formula': 'Trung bình |Giá trị thực tế − Giá trị dự báo| trên kỳ kiểm định độc lập', 'target': 'Thấp hơn sai số của phương án cơ sở (giữ nguyên kỳ trước) trước khi dùng để mở rộng vốn', 'frequency': 'Mỗi kỳ cập nhật dữ liệu'},
            ],
        }

    # General Research / Public Topic / Unknown Entity
    return {
        'sub_type': 'general_research',
        'peers': 'Các đối tượng cùng danh mục hoặc cùng địa bàn nghiên cứu sau khi xác minh danh tính',
        'audience': f'Nhóm độc giả, nhà nghiên cứu hoặc bên liên quan trực tiếp đến chủ đề “{query}”; cần xác minh rõ tư cách pháp nhân/đối tượng trước khi phân khúc thương mại',
        'offer': f'thông tin định danh, phạm vi hoạt động, bối cảnh pháp lý - xã hội và các chỉ tiêu thống kê có nguồn xác thực về “{query}”',
        'focus': f'xác minh danh tính chính xác, chuẩn hóa phạmび nghiên cứu và thu thập chuỗi dữ liệu gốc có nguồn kiểm chứng cho “{query}”',
        'channels': 'Cổng thông tin cơ quan quản lý, niên giám thống kê, báo cáo công bố chính thức và cơ sở dữ liệu học thuật/bách khoa',
        'demand_analysis': f'Làm rõ đối tượng, địa bàn và câu hỏi nghiên cứu của “{query}” trước khi xác định đây là chủ đề thông tin công cộng hay một thị trường có giao dịch thương mại.{fig_note}',
        'competition_analysis': f'Chỉ đối chiếu “{query}” với các đối tượng cùng bản chất, cùng đơn vị đo và cùng thời kỳ nghiên cứu; chưa mặc định tồn tại đối thủ kinh doanh khi chưa xác nhận giao dịch.',
        'market_gap': f'Khoảng trống dữ liệu cần bổ sung: làm rõ định nghĩa chỉ tiêu, đơn vị tính và chuỗi quan sát theo thời gian của chính “{query}”.',
        'pricing_reason': 'Từ khóa đang là địa danh/chủ đề hoặc chưa xác định giao dịch. Không tự đề xuất giá; nếu nghiên cứu dịch vụ liên quan, cần nêu rõ dịch vụ đó.',
        'pricing_methods': [],
        'required_inputs': [],
        'risks_tuples': [
            ('Sai danh tính hoặc phạm vi nghiên cứu', f'Tên gọi “{query}” có thể trùng lặp hoặc thiếu giới hạn địa bàn/thời kỳ dẫn đến ghép nhầm số liệu của đối tượng khác.', 'Đối chiếu tên đầy đủ, mã định danh, địa điểm và đơn vị chủ quản trên nguồn chính thức.', 'Xác nhận rõ phạm vi đối tượng trước khi đưa vào mô hình định lượng hoặc so sánh.'),
            ('Thiếu chuỗi dữ liệu định lượng đồng nhất', f'Các nguồn tham khảo về “{query}” có thể khác biệt về đơn vị tính, phương pháp thống kê hoặc bị đứt quãng thời gian.', 'Kiểm tra định nghĩa chỉ tiêu, kỳ đo (năm/quý/tháng) và đường dẫn nguồn của từng con số.', 'Nêu rõ giới hạn dữ liệu và chỉ huấn luyện dự báo khi có chuỗi quan sát liên tiếp cùng đơn vị.'),
        ],
        'action_plan': [
            {
                'period': 'Ngày 1–30',
                'goal': f'Xác minh danh tính, phạm vi hoạt động & nguồn dữ liệu gốc của “{query}”',
                'actions': [
                    f'Thu thập văn bản, báo cáo công bố chính thức hoặc hồ sơ định danh xác thực phạm vi của “{query}”.',
                    f'Phân tách rõ các dữ kiện đã có nguồn trực tiếp về “{query}” với số liệu bối cảnh vĩ mô cấp ngành/quốc gia.',
                    'Chuẩn hóa bảng cấu trúc dữ liệu: biến mục tiêu, đơn vị đo, tần suất thời gian và nguồn trích dẫn.',
                ],
                'owner': 'Nhóm Nghiên cứu & Quản trị Dữ liệu',
                'deliverable': f'Hồ sơ định danh đối tượng và bộ dữ liệu cơ sở đã làm sạch của “{query}”',
                'gate': 'Chỉ giữ lại các quan sát đúng đối tượng, có cùng định nghĩa và kỳ đo.',
            },
            {
                'period': 'Ngày 31–60',
                'goal': f'Kiểm chứng giả thuyết chuyên môn & bổ sung quan sát thực địa cho “{query}”',
                'actions': [
                    f'Đối chiếu các nhận định thu thập từ báo chí/web về “{query}” với số liệu thống kê chính thức hoặc khảo sát trực tiếp.',
                    'Thực hiện đánh giá chéo giữa các nguồn độc lập để loại bỏ thông tin nhiễu hoặc thiếu ngữ cảnh thời gian.',
                    'Chạy kiểm định mô hình định lượng trên tập dữ liệu đã làm sạch và đối chiếu sai số với phương án cơ sở.',
                ],
                'owner': 'Bộ phận Phân tích Định lượng & Chuyên môn',
                'deliverable': f'Báo cáo kiểm chứng dữ liệu và kết quả đánh giá sai số mô hình cho “{query}”',
                'gate': 'Sai số kiểm định minh bạch; không suy diễn vượt quá phạm vi dữ liệu đầu vào.',
            },
            {
                'period': 'Ngày 61–90',
                'goal': f'Tổng hợp báo cáo hoàn chỉnh & thiết lập cơ chế cập nhật định kỳ cho “{query}”',
                'actions': [
                    f'Đánh giá biến động của “{query}” qua tối thiểu hai kỳ dữ liệu liên tiếp đã được xác thực.',
                    'Đưa ra khuyến nghị hành động cụ thể tương ứng với từng kịch bản dữ liệu (Thận trọng / Thử nghiệm / Mở rộng).',
                    'Thiết lập lịch cập nhật dữ liệu mới và tái kiểm định mô hình khi có công bố thống kê kỳ tiếp theo.',
                ],
                'owner': 'Người ra quyết định & Nhóm Phân tích',
                'deliverable': f'Báo cáo chiến lược hoàn chỉnh và lịch trình theo dõi chỉ số định kỳ cho “{query}”',
                'gate': 'Mọi kết luận trọng yếu đều có đường dẫn nguồn hoặc bảng số liệu đối chiếu đi kèm.',
            },
        ],
        'kpis': [
            {'name': 'Độ đầy đủ dữ liệu có nguồn xác thực', 'formula': 'Số quan sát có đầy đủ nguồn, đơn vị tính và kỳ thời gian / tổng số quan sát thu thập', 'target': 'Đạt 100% trước khi đưa vào huấn luyện dự báo định lượng', 'frequency': 'Mỗi lần cập nhật dữ liệu'},
            {'name': 'Tỷ lệ tài liệu khớp đúng đối tượng (Exact Identity Match)', 'formula': 'Số nguồn tài liệu nhắc đúng thực thể nghiên cứu / tổng số nguồn tìm kiếm', 'target': 'Loại bỏ hoàn toàn các nguồn chỉ nhắc biến thể hoặc đối tượng trùng tên một phần', 'frequency': 'Mỗi phiên tra cứu'},
            {'name': 'Tỷ lệ tiêu chí nghiên cứu có bằng chứng đối chiếu', 'formula': 'Số tiêu chí trọng tâm có ít nhất 1 nguồn chính thống xác nhận / tổng số tiêu chí', 'target': 'Hoàn thiện độ phủ dữ liệu cho toàn bộ các tiêu chí cốt lõi', 'frequency': 'Hàng tháng'},
            {'name': 'Sai số dự báo trên tập kiểm định (MAE)', 'formula': 'Trung bình |Giá trị thực − Giá trị dự báo| trên các kỳ kiểm định độc lập', 'target': 'So sánh trực tiếp với phương án cơ sở; không ấn định độ chính xác giả định', 'frequency': 'Mỗi kỳ có dữ liệu mới'},
        ],
    }


def build_sections(query, context, sources, provenance, quantitative):
    category = context['category']
    education = category == 'Education & EdTech'
    commercial = category != 'General Research'
    corpus = key(query + ' ' + ' '.join(s.get('excerpt', '') for s in sources[:3]))
    public_topic = category == 'General Research' and any(word in corpus for word in (
        'thanh pho', 'dia danh', 'di tich', 'bien doi khi hau', 'lich su', 'hien tuong', 'khai niem', 'tinh thuoc'))

    intel = get_keyword_intelligence(query, context, sources)
    findings = [{'title': s['title'], 'excerpt': s.get('excerpt', ''), 'url': s['url'], 'verified': False}
                for s in sources if s.get('excerpt')][:4]
    change = (quantitative or {}).get('recent_change_pct')
    market = {
        'title': 'Phân tích thị trường & phân khúc',
        'scope': context['label'],
        'status': 'Có tài liệu để đối chiếu' if sources else 'Chưa tìm thấy tài liệu xác nhận riêng cho từ khóa',
        'target_segments': intel['audience'],
        'demand_analysis': intel['demand_analysis'],
        'competition_analysis': intel['competition_analysis'],
        'market_gap': intel['market_gap'],
        'trend_reading': (f"Chỉ tiêu “{provenance.get('scope_label')}” thay đổi {change:+.2f}% giữa hai kỳ gần nhất có dữ liệu; không suy ra mức tăng của riêng {query}." if change is not None else
                          'Chưa có chuỗi định lượng đủ điều kiện để xác nhận xu hướng; giữ nguyên trạng thái thiếu dữ liệu.'),
        'size_estimate': None,
        'size_note': 'Chưa tính quy mô thị trường, thị phần hoặc tổng doanh thu khi chưa có số lượng khách hàng và mức chi tiêu phù hợp cùng kỳ.',
        'source_findings': findings,
    }
    price_terms = ('hoc phi', 'hoc bong', 'gia ban', 'bang gia', 'chi phi', 'price', 'pricing', 'subscription', 'phi dich vu')
    price_sources = [{'title': s['title'], 'url': s['url'], 'excerpt': s.get('excerpt', ''), 'verified': False}
                     for s in sources if any(term in key(s['title']+' '+s.get('excerpt','')) for term in price_terms)][:5]
    pricing = {
        'applicable': commercial,
        'title': 'Chính sách học phí & học bổng' if education else 'Chiến lược định giá',
        'status': 'Có thể xây dựng phương án; chưa đủ dữ liệu chốt mức giá' if commercial else 'Không áp dụng định giá ở phạm vi hiện tại' if public_topic else 'Chưa xác định sản phẩm hoặc dịch vụ cần định giá',
        'reason': intel['pricing_reason'],
        'recommended_price': None,
        'price_sources': price_sources,
        'methods': intel['pricing_methods'] if commercial else [],
        'formulas': ([
            'Biên đóng góp/đơn vị = giá thực thu − chi phí biến đổi/đơn vị.',
            'Số lượng hòa vốn = chi phí cố định / biên đóng góp mỗi đơn vị, chỉ khi biên đóng góp > 0.',
            'Giá theo biên lợi nhuận mục tiêu = tổng chi phí/đơn vị / (1 − biên mục tiêu), với 0 ≤ biên mục tiêu < 1.',
        ] if commercial and not education else []),
        'required_inputs': intel['required_inputs'] if commercial else [],
    }
    # Risk signals are matching excerpts, not claims that an incident occurred.
    risks = intel['risks_tuples']
    risk_section = {
        'title': 'Rủi ro & thách thức',
        'status': 'Các tình huống cần kiểm soát; chưa khẳng định đã xảy ra',
        'items': [{'name': name, 'scenario': scenario, 'warning_sign': warning, 'mitigation': mitigation,
                   'probability': None, 'impact': None} for name, scenario, warning, mitigation in risks],
        'note': 'Không gán xác suất hay mức thiệt hại khi thiếu bằng chứng. Các nhận định về sự cố cụ thể phải có nguồn xác nhận.',
    }
    return {'market_analysis': market, 'pricing_strategy': pricing, 'risk_assessment': risk_section}
