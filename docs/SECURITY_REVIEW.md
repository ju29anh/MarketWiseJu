# Kiểm tra trước triển khai — 12/11/2026

**Kết luận: mã nguồn đã qua các kiểm tra bên dưới và phù hợp để triển khai bản demo công khai theo Docker/Render hiện có. Chưa phù hợp để lưu dữ liệu riêng tư hoặc triển khai dịch vụ nhiều người dùng có phân quyền. Chưa triển khai hay kiểm tra URL host thực tế trong đợt này.**

## Kết quả xác minh

| Hạng mục | Kết quả |
| --- | --- |
| Backend | 177 test đạt, gồm API, bảo mật, hồi quy ML, nghiên cứu và cấu hình triển khai |
| Frontend | 24 test đạt; lint, TypeScript và build production đạt |
| Thư viện frontend | `npm audit`: 0 lỗ hổng đã biết được báo cáo, gồm cả dev dependency |
| Thư viện backend | `pip_audit` trên toàn bộ `requirements-lock.txt`: không báo lỗ hổng đã biết; `pip check` đạt |
| Phiên bản backend | Các dependency runtime đang dùng khớp lock file |
| `.env` local | Cả hai file tồn tại, không thiếu biến trong template; SECRET_KEY đủ độ dài và không phải placeholder |
| Khóa trong frontend | Không tìm thấy giá trị khóa backend hiện có trong bản build frontend |
| Khóa viết cứng | Không phát hiện mẫu Google/API token/private key trong các file mã nguồn được quét; đây là quét theo mẫu, không phải kiểm chứng lịch sử Git |
| Chạy production thật tại máy | 8 nhóm kiểm tra triển khai đạt với Uvicorn, frontend đã build và SQLite tạm |

Luồng production đã chạy: tải file CSV mẫu, tạo tác vụ ML, chờ hoàn tất, đọc lại báo cáo đã lưu và kết quả đánh giá mô hình. Kiểm tra thêm 16 bộ dữ liệu mẫu, tài nguyên JS/CSS/theme, input sai trả 422 và yêu cầu quá dung lượng trả 413. Server tạm đã dừng, dữ liệu tạm đã dọn; kiểm thử không dùng cơ sở dữ liệu hoặc khóa API thật của người dùng.

Các URL `.env`, `.env.example`, `backend/.env`, `frontend/.env`, `.git/config`, `main.py`, `marketwise.db`, tài nguyên không tồn tại và tài liệu API production trả 404. Phản hồi 400/413/422/429/500 có header bảo mật và mã yêu cầu; lỗi nội bộ không trả thông tin ngoại lệ riêng tư.

## Các điểm đã sửa

- Chuẩn hóa và giới hạn `ENVIRONMENT`, tránh cấu hình sai chính tả/vết hoa làm bỏ qua bảo vệ production. Kiểm tra SECRET_KEY, DB và thư mục frontend trước khi chạy.
- Chặn production bind ra ngoài khi chưa xác nhận `PUBLIC_DEMO=true`. Cờ này xác nhận chế độ dữ liệu dùng chung, không bật đăng nhập.
- Chặn `STATIC_DIR` trỏ vào backend, thư mục chứa backend hoặc bản public có `.env`, metadata Git, khóa, DB, log và mã Python.
- Thêm CSP, chống nhúng iframe, Permissions-Policy và HSTS khi ASGI nhận đúng HTTPS; giữ các header trên cả phản hồi lỗi sớm, CORS và lỗi nội bộ. Tắt tài liệu API và header phiên bản server ở production.
- Chuyển script khởi tạo theme ra file riêng để tương thích CSP không cho chạy JavaScript inline.
- Chuyển khóa Gemini từ URL sang header, không tự theo redirect trong các lệnh sinh nội dung/giọng nói. Sửa trường `role` bị gõ sai trong payload TTS.
- Bổ sung GEMINI_API_KEY và RESEARCH_FETCH_PAGES trong template. Đồng bộ các biến còn thiếu vào `.env` local, giữ nguyên giá trị hiện có; chạy lại script đồng bộ không thay đổi file.
- Chặn reload trong launcher production và đặt mặc định giới hạn luồng tính toán như container. Bổ sung kiểm thử hồi quy và mở rộng script kiểm tra triển khai.

## Các việc còn phụ thuộc host

1. Tạo biến môi trường trong dashboard host theo [DEPLOYMENT.md](DEPLOYMENT.md). `.env` local không được đóng gói vào Docker. Không đưa `.env`, DB, upload, log, venv hoặc node_modules lên web root/Git công khai.
2. Build image Docker/Linux trên host. Máy hiện có Docker CLI nhưng Docker Engine chưa chạy, nên đợt kiểm tra này chưa xác minh được image Docker thực tế.
3. Sau deploy, chạy `backend/.venv/Scripts/python.exe scripts/check_deployment.py https://TEN-DICH-VU.onrender.com`. Kiểm tra HTTPS/HSTS, IP proxy tin cậy, frontend và nguồn web từ chính IP host. Thêm `--exercise` để tạo một bộ dữ liệu mẫu và một báo cáo trên host.
4. Khóa Gemini đang được cấu hình ở backend; chưa gọi dịch vụ bằng khóa thật để xác minh hiệu lực, quyền, model hoặc quota. Đặt hạn mức chi phí ở nhà cung cấp trước khi bật công khai. Brave/Tavily là nguồn bổ sung tùy chọn.
5. Ứng dụng chưa có đăng nhập, phân quyền sở hữu dataset/báo cáo hoặc quota dung lượng theo người dùng. Có giới hạn file, dòng/cột/bộ nhớ, tốc độ POST và hàng đợi, nhưng cần hạn mức ổ đĩa và kiểm soát lưu lượng ở host. Chỉ dùng dữ liệu mẫu/công khai trong bản demo.
6. SQLite, uploads và research_runs cần bộ nhớ bền vững/backup nếu muốn giữ dữ liệu. Render Free mất file khi restart/redeploy/ngủ; không dùng làm nơi lưu dữ liệu dài hạn. [Tài liệu Render Free](https://render.com/docs/free).

Thư mục hiện không phải Git repository nên chưa thể kiểm tra file đã stage hay lịch sử commit. Chạy `scripts/check_git_hygiene.py` trong repository trước khi commit. Nếu khóa từng bị đưa lên nơi công khai, cần đổi khóa tại nhà cung cấp.

Hai cảnh báo kiểm thử hiện tại là deprecation của tích hợp pytest/AnyIO và Starlette TestClient/httpx; không có test thất bại. Kết quả audit thư viện phản ánh dữ liệu advisory tại thời điểm chạy, không chứng minh ứng dụng hết mọi lỗi.

Tham khảo thiết kế header: [OWASP Secure Headers Project](https://owasp.org/projects/secure-headers-project).
