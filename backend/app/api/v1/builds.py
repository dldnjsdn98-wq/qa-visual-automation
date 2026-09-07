from backend.app.models import Build
from backend.app.schemas import catalog as schema
from .catalog_routes import scoped_router
router = scoped_router("builds", "build_id", Build, schema.BuildCreate, schema.BuildPatch, schema.Build)
