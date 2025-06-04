from .News import NewsSourcer
from lib.agent_manager import get_agent_manager
from .ManufacturingMetrices import ManufacturingMetrices
from .ManufacturingBusinessModels import ManufacturingBusinessModels


am = get_agent_manager()

news_sourcer = NewsSourcer(am)
manufacturing_metrices = ManufacturingMetrices(am)
manufacturing_business_models = ManufacturingBusinessModels(am)
