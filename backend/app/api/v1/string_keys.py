from backend.app.models import StringKey
from backend.app.schemas import strings as schema
from .catalog_routes import scoped_router, StringKeyFilter
router = scoped_router("string-keys", "string_key_id", StringKey, schema.StringKeyCreate, schema.StringKeyPatch, schema.StringKey, StringKeyFilter)
