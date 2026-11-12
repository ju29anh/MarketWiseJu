# Demo miễn phí trên Render

Khuyến nghị cho dự án này: một **Render Free Web Service, Docker**, phục vụ cả giao diện đã build và API Python. Một tên miền cùng origin, không cần cấu hình Vercel riêng hay đưa API key vào frontend.

## Giới hạn cần biết

Theo [tài liệu Render Free](https://render.com/docs/free), dịch vụ ngủ sau 15 phút không có truy cập, mất khoảng một phút để thức lại, file cục bộ không được giữ khi restart/redeploy/ngủ. Vì vậy đây là phương án demo, không phải lưu trữ dài hạn. Gói miễn phí có hạn mức giờ, lưu lượng và build; xem dashboard của tài khoản trước khi tạo dịch vụ. Không tự chọn gói trả phí.

GitHub dùng để lưu mã nguồn. GitHub Pages chỉ phục vụ nội dung tĩnh, không chạy API Python của dự án. Vercel có thể phục vụ giao diện, nhưng tách API thành dịch vụ riêng sẽ thêm cấu hình cho bản demo. Chọn một dịch vụ Docker để giữ nguyên kiến trúc một tiến trình.

## Đưa mã nguồn lên GitHub

1. Tạo repository, ưu tiên private nếu tài khoản Render của bạn kết nối được repository đó.
2. Đưa mã nguồn dự án, `Dockerfile`, `.dockerignore`, `render.yaml`, `frontend/package-lock.json`, `backend/requirements-lock.txt` vào repo.
3. Không đưa `.env`, khóa truy cập, DB, file tải lên, `research_runs`, log, venv, node_modules hoặc dist lên GitHub. `.gitignore` và `.dockerignore` đã loại các mục này. Nếu khóa từng được commit, phải đổi khóa; bỏ file khỏi commit mới không xóa khóa trong lịch sử.

## Tạo dịch vụ

1. Đăng nhập [Render Dashboard](https://dashboard.render.com/), kết nối GitHub.
2. Chọn **New → Blueprint**, chọn repository có `render.yaml` ở thư mục gốc.
3. Kiểm tra dịch vụ `marketwise-demo`, runtime Docker, instance **Free**. `SECRET_KEY` được sinh tự động trong Render.
4. Triển khai và chờ log báo API đã khởi động. Mở URL `https://...onrender.com` Render cấp.

Nếu tạo thủ công bằng **New → Web Service**: chọn Docker, `Dockerfile` ở root, gói Free, health check `/api/health`. Tạo `SECRET_KEY` ngẫu nhiên ít nhất 32 ký tự; thêm các biến môi trường tương ứng trong `render.yaml`. Không dùng placeholder trong `.env.example`.

Các nguồn không cần khóa chạy được ngay; nguồn bổ sung có thể cần khóa/hạn mức. Chỉ thêm khóa ở phần Environment của Render, không commit hoặc dùng `VITE_*` cho chúng.

### Biến môi trường khi lên host

`backend/.env` và `frontend/.env` hiện có phục vụ local. Docker không sao chép các file này vào image. Tạo các biến trong Environment của host; không tải nguyên thư mục dự án lên một web root Apache/PHP.

| Biến | Docker / Render |
| --- | --- |
| `ENVIRONMENT` | `production` (Docker đã đặt) |
| `HOST` / `PORT` | `0.0.0.0` / cổng host cấp; mặc định Docker là `10000` |
| `PUBLIC_DEMO` | `true`, vì ứng dụng hiện dùng chung dữ liệu và chưa có đăng nhập |
| `SECRET_KEY` | Sinh ngẫu nhiên ít nhất 32 ký tự; Blueprint tự sinh |
| `STATIC_DIR` | `/app/frontend_dist` (Docker đã đặt) |
| `STORAGE_DIR` | `/app/data` (Docker đã đặt); cần persistent disk khi muốn giữ dữ liệu |
| `ALLOWED_ORIGINS` | Để trống khi giao diện và API cùng tên miền |
| `GEMINI_API_KEY` | Tùy chọn, cần cho tính năng AI/giọng nói qua nhà cung cấp; thiếu khóa sẽ dùng phương án dự phòng |
| `BRAVE_SEARCH_API_KEY` / `TAVILY_API_KEY` | Tùy chọn cho nguồn tìm kiếm bổ sung |

`SECRET_KEY` không tạo tài khoản hay bảo vệ dữ liệu theo người dùng. `PUBLIC_DEMO=false` cũng không bật xác thực. Launcher chặn production bind ra ngoài khi chưa xác nhận chế độ demo. Nếu cần dữ liệu riêng tư, phải bổ sung xác thực và phân quyền trước khi mở truy cập công khai.

Giữ `UVICORN_RELOAD` tắt, chỉ chạy một worker. Uvicorn mặc định chỉ tin proxy trên loopback; nếu host dùng reverse proxy khác, đặt `FORWARDED_ALLOW_IPS` đúng IP/CIDR của proxy theo hạ tầng host để nhận đúng HTTPS và IP cho giới hạn tần suất. Không tin mọi IP nếu cổng backend còn truy cập trực tiếp từ Internet. Kiểm tra HSTS trên URL HTTPS thực tế bằng lệnh kiểm tra bên dưới.

Khi cập nhật local, chạy `backend/.venv/Scripts/python.exe scripts/setup_env.py` để bổ sung biến thiếu từ template; script giữ nguyên giá trị và khóa hiện có.

## Tự kiểm tra sau khi build trên host

Từ máy local đã cài dependency kiểm thử, có thể chạy kiểm tra chỉ đọc đối với URL production:

```powershell
backend/.venv/Scripts/python.exe scripts/check_deployment.py https://TEN-DICH-VU.onrender.com
```

Thêm `--exercise` nếu muốn tạo **một bộ dữ liệu mẫu và một báo cáo ML** để kiểm tra cả luồng tải lên, xử lý và đọc lại. Lệnh không thay cho kiểm tra giao diện và các nguồn web thực tế trên host.

- `/api/health` trả `status: ok`.
- Trang chủ mở được; Network không có request đến `localhost:8000` hoặc `localhost:5173`.
- Thử một trường đại học, một sản phẩm/dịch vụ và một chủ đề không có giao dịch. Kiểm tra mục thị trường, học phí/giá, rủi ro phù hợp loại từ khóa.
- Thử so sánh hai tên, tải báo cáo và CSV. Số liệu quốc gia phải giữ nhãn quốc gia, không gán thành dữ liệu của doanh nghiệp/trường.
- Thử trên điện thoại. Bảng rộng chỉ cuộn trong khung.
- Dùng file mẫu, tối đa 5 MB, 5.000 dòng, 50 cột theo cấu hình demo. Không tải thông tin riêng tư: bản demo dùng chung dữ liệu và chưa có tài khoản/phân quyền từng người.

Mở web và chạy thử một lần trước buổi trình bày 5–10 phút. Lưu báo cáo quan trọng về máy. Không dùng công cụ giữ thức liên tục để né giới hạn của host. Nếu API nguồn ngoài hạn chế truy cập từ IP cloud, báo cáo sẽ nêu thiếu dữ liệu hoặc dùng nguồn tham khảo khác; không coi đó là lỗi kết nối của giao diện.

## Chạy container tại máy có Docker

```powershell
docker build -t marketwise-demo .
# SECRET_KEY được đặt sẵn trong môi trường terminal, không ghi vào Dockerfile.
docker run --rm -p 127.0.0.1:10000:10000 -e SECRET_KEY -e PUBLIC_DEMO=true marketwise-demo
```

Tạo bản cho VPS sau này: dùng ổ dữ liệu gắn vào `/app/data`, reverse proxy HTTPS và xác thực/phân quyền trước khi dùng dữ liệu riêng. Không public Vite dev server. `render.yaml` không tạo database hay disk trả phí.

Giới hạn tần suất và hàng đợi chỉ áp dụng cho một tiến trình. Trên host công khai, cần đặt hạn mức chi phí API ở nhà cung cấp, giới hạn dung lượng ổ lưu trữ và theo dõi log/lưu lượng. Các lớp giới hạn trong ứng dụng không thay cho chống DDoS ở hạ tầng.
