"""make products thumbnail nullable

Revision ID: 7e23f8bf45bf
Revises: d60799c9dd7f
Create Date: 2026-01-12 01:21:34.708983

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e23f8bf45bf'
down_revision: Union[str, Sequence[str], None] = 'd60799c9dd7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
