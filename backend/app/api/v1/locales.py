from backend.app.models import Locale
from backend.app.schemas import catalog as schema
from .catalog_routes import scoped_router
router = scoped_router("locales", "locale_id", Locale, schema.LocaleCreate, schema.LocalePatch, schema.Locale)
