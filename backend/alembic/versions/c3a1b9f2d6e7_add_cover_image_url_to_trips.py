from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3a1b9f2d6e7"
down_revision: Union[str, None] = "047b0cd807a5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("cover_image_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("trips", "cover_image_url")
