import uuid
from pathlib import Path
from contextlib import closing
from fastapi import HTTPException, UploadFile
from core.config import BACKEND_DIR, UPLOADS_DIR, settings
from database import get_db_connection
from ml_engine.validator import DataValidator
from services.datasets import read_dataset, preview


def process_upload(file: UploadFile, category: str, *, preview_only=False):
    """Stream to disk, validate, then atomically publish a normalized CSV."""
    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in ('.csv', '.xlsx'):
        raise HTTPException(400, 'Chỉ hỗ trợ file .csv hoặc .xlsx. Hãy tải file mẫu để xem cấu trúc.')
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    temporary = UPLOADS_DIR / f'{token}.tmp'
    final = UPLOADS_DIR / f'upload_{token}.csv'
    committed = False
    try:
        size = 0
        with temporary.open('xb') as output:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > settings.max_upload_mb * 1024**2:
                    raise HTTPException(413, f'File vượt quá {settings.max_upload_mb} MB. Hãy chia nhỏ dữ liệu.')
                output.write(chunk)
        frame = read_dataset(temporary, excel=suffix == '.xlsx')
        sample = preview(frame)
        if preview_only:
            return sample
        validation = DataValidator.validate_dataset(frame)
        if not validation['valid']:
            raise HTTPException(400, 'Dữ liệu chưa đủ để phân tích. Cần ít nhất 5 dòng và các cột số như giá, doanh số.')
        frame.to_csv(final, index=False)
        if final.stat().st_size > settings.max_upload_mb * 1024**2:
            raise HTTPException(413, 'Dữ liệu sau chuyển đổi quá lớn. Hãy chia nhỏ file.')
        with closing(get_db_connection()) as conn, conn:
            conn.execute('''INSERT INTO datasets (title, category, filename, filepath, source, total_rows, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (Path(file.filename.replace('\\', '/')).stem[:200], category, final.name,
                 str(final.relative_to(BACKEND_DIR)) if final.is_relative_to(BACKEND_DIR) else str(Path('uploads') / final.name), 'User Uploaded Dataset', len(frame), validation['quality_score']))
        committed = True
        return {'message': 'Tải lên và kiểm định dataset thành công.', 'filename': final.name,
                'validation': validation, 'preview': sample}
    finally:
        file.file.close()
        temporary.unlink(missing_ok=True)
        if not committed:
            final.unlink(missing_ok=True)
