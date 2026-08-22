"""Import every SQLAlchemy model so Alembic sees complete metadata."""

from backend.app.identity.models import *  # noqa: F401,F403
from backend.app.athletes.models import *  # noqa: F401,F403
from backend.app.knowledge.models import *  # noqa: F401,F403
from backend.app.training.models import *  # noqa: F401,F403
from backend.app.activities.models import *  # noqa: F401,F403
from backend.app.maps.models import *  # noqa: F401,F403
from backend.app.competition.models import *  # noqa: F401,F403
from backend.app.nutrition.models import *  # noqa: F401,F403
from backend.app.health.models import *  # noqa: F401,F403
from backend.app.notifications.models import *  # noqa: F401,F403
from backend.app.moderation.models import *  # noqa: F401,F403
from backend.app.operations.models import *  # noqa: F401,F403

