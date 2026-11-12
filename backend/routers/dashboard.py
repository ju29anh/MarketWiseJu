from fastapi import APIRouter
from services import catalog

router = APIRouter(prefix='/api', tags=['Dashboard & catalog'])
router.add_api_route('/categories', catalog.get_categories, methods=['GET'])
router.add_api_route('/datasets', catalog.get_datasets, methods=['GET'])
router.add_api_route('/search', catalog.search_market_data, methods=['GET'])
router.add_api_route('/datasets/{filename}/products', catalog.get_dataset_products, methods=['GET'])
router.add_api_route('/market-overview', catalog.get_market_overview, methods=['GET'])
router.add_api_route('/dashboard/stats', catalog.get_dashboard, methods=['GET'])
