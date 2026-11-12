"""Bounded file parsing shared by validation, upload and the ML pipeline."""
from pathlib import Path
from zipfile import ZipFile, BadZipFile
import pandas as pd
import numpy as np
from openpyxl.utils.exceptions import InvalidFileException
from defusedxml.common import DefusedXmlException
from xml.etree.ElementTree import ParseError
from fastapi import HTTPException
from core.config import settings, DATASETS_DIR, UPLOADS_DIR
from core.serialization import np_clean


def resolve_dataset(filename: str) -> Path:
    if not filename or any(c in filename for c in ('/', '\\', ':', '\x00')) or Path(filename).suffix.lower() != '.csv':
        raise HTTPException(400, 'Tên dataset không hợp lệ. Vui lòng chọn lại dữ liệu.')
    for root in (DATASETS_DIR, UPLOADS_DIR, DATASETS_DIR / 'uploads'):
        path = (root / filename).resolve()
        if path.parent == root.resolve() and path.is_file():
            return path
    raise HTTPException(404, 'Không tìm thấy dataset. Vui lòng tải lại hoặc chọn file mẫu.')


def read_dataset(path: Path, *, excel=False) -> pd.DataFrame:
    if path.stat().st_size > settings.max_upload_mb * 1024**2:
        raise HTTPException(413, 'File quá lớn. Hãy chia nhỏ dữ liệu trước khi tải lên.')
    try:
        if excel:
            # XLSX is a ZIP container: cap expanded bytes before the XML parser runs.
            with ZipFile(path) as archive:
                if sum(entry.file_size for entry in archive.infolist()) > settings.max_dataset_memory_mb * 1024**2:
                    raise HTTPException(413, 'File Excel giải nén quá lớn. Hãy chia nhỏ dữ liệu.')
            frame = pd.read_excel(path, engine='openpyxl', nrows=settings.max_dataset_rows + 1)
        else:
            with pd.read_csv(path, chunksize=min(10000, settings.max_dataset_rows + 1)) as reader:
                chunks, rows, memory = [], 0, 0
                for chunk in reader:
                    rows += len(chunk)
                    memory += int(chunk.memory_usage(deep=True).sum())
                    if rows > settings.max_dataset_rows or len(chunk.columns) > settings.max_dataset_columns or memory > settings.max_dataset_memory_mb * 1024**2:
                        raise HTTPException(413, 'Dataset vượt giới hạn dòng, cột hoặc bộ nhớ. Hãy chia nhỏ dữ liệu.')
                    chunks.append(chunk)
                frame = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
        if len(frame) > settings.max_dataset_rows or len(frame.columns) > settings.max_dataset_columns or frame.memory_usage(deep=True).sum() > settings.max_dataset_memory_mb * 1024**2:
            raise HTTPException(413, 'Dataset quá lớn. Hãy chia nhỏ dữ liệu.')
        frame.columns = frame.columns.map(str)
        if np.isinf(frame.select_dtypes(include=[np.number]).to_numpy(dtype=float)).any():
            raise HTTPException(400, 'Dataset có giá trị số vô hạn. Hãy sửa các ô inf/Infinity rồi tải lại.')
        return frame
    except HTTPException:
        raise
    except (ValueError, OSError, UnicodeError, BadZipFile, pd.errors.ParserError,
            KeyError, EOFError, InvalidFileException, DefusedXmlException, ParseError) as exc:
        raise HTTPException(400, 'Không đọc được file. Hãy dùng CSV UTF-8 hoặc XLSX có hàng tiêu đề.') from exc


def preview(frame):
    return {'columns': frame.columns.tolist(), 'rows': np_clean(frame.head(5).to_dict(orient='records')), 'total_rows': len(frame)}
