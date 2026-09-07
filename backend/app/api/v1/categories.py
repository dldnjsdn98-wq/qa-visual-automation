from backend.app.models import Category
from backend.app.schemas import catalog as schema
from .catalog_routes import scoped_router
router = scoped_router("categories", "category_id", Category, schema.CategoryCreate, schema.CategoryPatch, schema.Category)
