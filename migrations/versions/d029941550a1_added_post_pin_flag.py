"""added post pin flag

Revision ID: d029941550a1
Revises: 12eb4af68db6
Create Date: 2020-03-03 20:04:41.926633

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd029941550a1'
down_revision = '12eb4af68db6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('post', sa.Column('is_pinned', sa.Boolean(), nullable=True))
    op.alter_column('post', 'body',
                    existing_type=sa.VARCHAR(length=140),
                    type_=sa.String(length=666),
                    existing_nullable=False)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('post', 'is_pinned')
    op.alter_column('post', 'body',
                    existing_type=sa.VARCHAR(length=666),
                    type_=sa.String(length=140),
                    existing_nullable=False)
