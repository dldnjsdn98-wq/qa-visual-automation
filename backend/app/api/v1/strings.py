from backend.app.models import StringEntry
from backend.app.schemas import strings as schema
from .catalog_routes import scoped_router, StringFilter
router = scoped_router("strings", "entry_id", StringEntry, schema.StringEntryCreate, schema.StringEntryPatch, schema.StringEntry, StringFilter)
