export function friendlyStatus(status: number): string {
  if (status === 413) return 'File quá lớn. Hãy chia nhỏ dữ liệu rồi tải lại.';
  if (status === 429) return 'Hệ thống đang bận. Vui lòng thử lại sau ít phút.';
  if (status === 404) return 'Dữ liệu hoặc phiên xử lý không còn tồn tại. Hãy chọn lại dataset.';
  if (status === 400 || status === 422) return 'Dữ liệu chưa hợp lệ. Kiểm tra định dạng, hàng tiêu đề và các cột số hoặc tải file mẫu.';
  return 'Máy chủ chưa thể xử lý yêu cầu. Vui lòng thử lại sau.';
}

export function errorMessage(error: unknown): string {
  if (error instanceof Error && error.name === 'AbortError') return 'Đã dừng chờ kết quả.';
  return error instanceof Error ? error.message : 'Có lỗi xảy ra. Vui lòng thử lại.';
}
