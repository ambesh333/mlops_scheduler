"""adding org in cluster

Revision ID: fdb1a612bb28
Revises: e5f135d4355d
Create Date: 2025-05-18 15:39:15.492231

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fdb1a612bb28'
down_revision: Union[str, None] = 'e5f135d4355d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('clusters', sa.Column('organization_id', sa.Integer(), nullable=False))
    op.create_foreign_key(None, 'clusters', 'organizations', ['organization_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'clusters', type_='foreignkey')
    op.drop_column('clusters', 'organization_id')
    # ### end Alembic commands ###
