"""purchase table

Revision ID: d5fb26062a01
Revises: 115858d5323c
Create Date: 2020-01-20 20:10:21.788464

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd5fb26062a01'
down_revision = '115858d5323c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('consumption_item',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=30), nullable=True),
    sa.Column('state', sa.String(length=10), nullable=False),
    sa.Column('unit', sa.String(length=5), nullable=False),
    sa.Column('amount', sa.Integer(), nullable=False),
    sa.Column('requestor_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['requestor_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consumption_item_name'), 'consumption_item', ['name'], unique=False)
    op.create_index(op.f('ix_consumption_item_state'), 'consumption_item', ['state'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_consumption_item_state'), table_name='consumption_item')
    op.drop_index(op.f('ix_consumption_item_name'), table_name='consumption_item')
    op.drop_table('consumption_item')
    # ### end Alembic commands ###
