"""Add last message field

Revision ID: 63349a01d030
Revises: ea948c067e85
Create Date: 2019-01-29 21:50:50.643835

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63349a01d030'
down_revision = 'ea948c067e85'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('games', sa.Column('last_message_json', sa.Text(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('games', 'last_message_json')
    # ### end Alembic commands ###
