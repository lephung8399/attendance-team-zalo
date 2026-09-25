"""Import every module's models so `Base.metadata` is fully populated before
`create_all()` (dev/tests) or Alembic autogenerate runs."""

from app.modules.attendance import models as attendance_models  # noqa: F401
from app.modules.audit import models as audit_models  # noqa: F401
from app.modules.matches import models as matches_models  # noqa: F401
from app.modules.members import models as members_models  # noqa: F401
from app.modules.publishing import models as publishing_models  # noqa: F401
from app.modules.teams import models as teams_models  # noqa: F401
