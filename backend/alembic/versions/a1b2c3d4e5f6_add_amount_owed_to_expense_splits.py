from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "c3a1b9f2d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    cols = [c['name'] for c in inspector.get_columns('expense_splits')]
    if 'amount_owed' not in cols:
        op.add_column(
            'expense_splits',
            sa.Column('amount_owed', sa.Float(), nullable=False, server_default='0')
        )


def downgrade() -> None:
    op.drop_column('expense_splits', 'amount_owed')
