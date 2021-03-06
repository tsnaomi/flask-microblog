"""empty message

Revision ID: 463f2100619c
Revises: 14f5ee244408
Create Date: 2014-03-13 16:37:37.133244

"""

# revision identifiers, used by Alembic.
revision = '463f2100619c'
down_revision = '14f5ee244408'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('registration',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.Integer(), nullable=True),
    sa.Column('email', sa.String(length=40), nullable=True),
    sa.Column('username', sa.String(length=20), nullable=True),
    sa.Column('password', sa.String(length=20), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('key'),
    sa.UniqueConstraint('username')
    )
    op.add_column(u'author', sa.Column('email', sa.String(length=40), nullable=True))
    op.create_unique_constraint(None, 'author', ['email'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'author')
    op.drop_column(u'author', 'email')
    op.drop_table('registration')
    ### end Alembic commands ###
