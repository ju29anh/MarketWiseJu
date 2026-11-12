# MarketWise

Website nghiên cứu thị trường, so sánh đối tượng, phân tích dữ liệu và lập kế hoạch với **MarketWiseJu**.

## Chạy local

Yêu cầu Python 3.11–3.13 và Node.js 22.12 trở lên.

```powershell
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt
backend/.venv/Scripts/python.exe scripts/setup_env.py
cd frontend
npm ci
cd ..
.\start.bat
```

Giữ nguyên các tệp `.env` đã có khi cập nhật. Mở http://localhost:5173. Không cần bật Apache. Launcher ghi vị trí log và PID để kiểm tra/dừng tiến trình.

## Cấu hình và triển khai

- Cấu hình riêng và khóa nhà cung cấp nằm ở `backend/.env`; tên biến cần giữ đúng theo `.env.example`. Không đặt khóa trong `VITE_*` hoặc đưa `.env` lên Git.
- Giao diện và bản xuất hiển thị MarketWiseJu. Tên model và chi tiết nhà cung cấp thuộc phần xử lý nội bộ; dữ liệu, nguồn và giới hạn phân tích vẫn được công bố.
- Có thể build và chạy một dịch vụ Docker phục vụ cả giao diện lẫn backend. Xem [triển khai](docs/DEPLOYMENT.md). Không phục vụ trực tiếp toàn bộ checkout qua Apache.
- Xem [kết quả kiểm tra bảo mật và mức sẵn sàng triển khai](docs/SECURITY_REVIEW.md), bao gồm các giới hạn về dữ liệu dùng chung và bước xác minh trên host.
- Chạy một tiến trình backend. Lịch sử trò chuyện và trạng thái tác vụ nằm trong bộ nhớ tiến trình; restart sẽ xóa các phiên này. Báo cáo đã lưu vẫn nằm trong SQLite.

## Cấu trúc

```text
backend/       Dịch vụ xử lý, cấu hình riêng, thuật toán, dữ liệu và kiểm thử
frontend/      Giao diện React / TypeScript
scripts/       Khởi động, cấu hình và kiểm tra triển khai
```

Giữ `backend/marketwise.db`, `backend/datasets/uploads/` và `backend/research_runs/` khi muốn bảo toàn dữ liệu đã tạo. Không đưa các mục này vào gói mã nguồn công khai. `node_modules`, `.venv`, `dist`, log và cache được sinh trong quá trình chạy/build.

## Kiểm tra

```powershell
cd backend
.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider
cd ../frontend
npm test
npm run build
npm run lint
```

Báo cáo phân biệt tài liệu nguồn, giả định và đề xuất. Trích dẫn khớp văn bản không chứng minh nguồn đúng hoặc kế hoạch chắc chắn thành công. Dữ liệu quốc gia giữ nguyên phạm vi quốc gia, không được coi là doanh số riêng của sản phẩm.

## Bản quyền

Tác giả: Nguyễn Hoàng Anh (Ju). Biểu tượng sử dụng Lucide, giấy phép ISC; xem [giấy phép Lucide](https://lucide.dev/license). Tham khảo phong cách Flaticon Web Icons, không dùng tài sản Flaticon tải về.
