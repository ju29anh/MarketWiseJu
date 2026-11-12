from fastapi import APIRouter, File, Form, UploadFile
from fastapi.responses import Response
from schemas.analysis import DatasetRequest, PreviewResponse, UploadResponse
from services.datasets import read_dataset, resolve_dataset
from services.upload import process_upload
from ml_engine.validator import DataValidator

router = APIRouter(prefix='/api', tags=['Datasets'])


@router.post('/datasets/upload', response_model=UploadResponse)
def upload_dataset(file: UploadFile = File(...), category: str = Form('Custom Upload', max_length=120)):
    return process_upload(file, category)


@router.post('/datasets/preview', response_model=PreviewResponse)
def preview_dataset(file: UploadFile = File(...)):
    return process_upload(file, '', preview_only=True)


@router.get('/datasets/template')
def download_template():
    csv = 'product_name,price,sales,search_volume,growth_rate,rating\n' + '\n'.join(
        f'Sample product,{10+i},{100+i*10},{200+i*20},{2+i/10},4.5' for i in range(24))
    return Response(csv, media_type='text/csv', headers={'Content-Disposition': 'attachment; filename="marketwise_sample.csv"'})


@router.post('/validate')
def validate_dataset_endpoint(payload: DatasetRequest):
    return DataValidator.validate_dataset(read_dataset(resolve_dataset(payload.dataset_name)))
