"""Initial migration

Revision ID: 8e6c6132252a
Revises: 
Create Date: 2025-04-04 05:08:28.149988

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8e6c6132252a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('email', sa.String(length=100), nullable=False),
    sa.Column('password', sa.String(length=100), nullable=False),
    sa.Column('is_owner', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email')
    )
    op.create_table('turf',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('location', sa.String(length=100), nullable=False),
    sa.Column('price_per_hour', sa.Float(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('community',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team_name', sa.String(length=100), nullable=True),
    sa.Column('sport', sa.String(length=50), nullable=False),
    sa.Column('max_players', sa.Integer(), nullable=False),
    sa.Column('turf_id', sa.Integer(), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['turf_id'], ['turf.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('team_name', 'status', name='unique_active_team_name')
    )
    op.create_table('slot',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('turf_id', sa.Integer(), nullable=False),
    sa.Column('start_time', sa.String(length=20), nullable=False),
    sa.Column('is_blocked', sa.Boolean(), nullable=True),
    sa.Column('is_booked', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['turf_id'], ['turf.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('booking',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('owner_id', sa.Integer(), nullable=False),
    sa.Column('community_id', sa.Integer(), nullable=False),
    sa.Column('turf_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('slot_time', sa.String(length=20), nullable=False),
    sa.Column('total_cost', sa.Float(), nullable=False),
    sa.Column('per_player_cost', sa.Float(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.ForeignKeyConstraint(['community_id'], ['community.id'], ),
    sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['turf_id'], ['turf.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('community_players',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('community_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.Column('paid', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['community_id'], ['community.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'community_id', name='unique_user_community')
    )
    op.create_table('booking_slots',
    sa.Column('booking_id', sa.Integer(), nullable=True),
    sa.Column('slot_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['booking_id'], ['booking.id'], ),
    sa.ForeignKeyConstraint(['slot_id'], ['slot.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('booking_slots')
    op.drop_table('community_players')
    op.drop_table('booking')
    op.drop_table('slot')
    op.drop_table('community')
    op.drop_table('turf')
    op.drop_table('user')
    # ### end Alembic commands ###
