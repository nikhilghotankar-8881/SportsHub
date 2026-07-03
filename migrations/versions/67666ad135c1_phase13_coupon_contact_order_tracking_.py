"""phase13_coupon_contact_order_tracking_inventory

Revision ID: 67666ad135c1
Revises: 41dbc85d4b97
Create Date: 2026-07-02 22:14:49.588351

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67666ad135c1'
down_revision = '41dbc85d4b97'
branch_labels = None
depends_on = None


def upgrade():
    # contacts table
    op.create_table('contacts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=120), nullable=False),
    sa.Column('subject', sa.String(length=200), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.PrimaryKeyConstraint('id')
    )

    # coupons table
    op.create_table('coupons',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(length=50), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=True),
    sa.Column('coupon_type', sa.String(length=20), nullable=False, server_default='percentage'),
    sa.Column('discount_value', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
    sa.Column('minimum_purchase', sa.Numeric(precision=10, scale=2), nullable=False, server_default='0'),
    sa.Column('max_discount', sa.Numeric(precision=10, scale=2), nullable=True),
    sa.Column('usage_limit', sa.Integer(), nullable=True),
    sa.Column('used_count', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
    sa.Column('expires_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )

    # order_status_history table
    op.create_table('order_status_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=30), nullable=False),
    sa.Column('note', sa.String(length=300), nullable=True),
    sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    # orders table – new columns with server_default for NOT NULL fields
    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discount_amount', sa.Numeric(precision=12, scale=2),
                                       nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('coupon_code', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('gst_amount', sa.Numeric(precision=12, scale=2),
                                       nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=False,
                                       server_default=sa.func.now()))
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(length=20),
               type_=sa.String(length=30),
               existing_nullable=False)

    # products table – low_stock_threshold with default 5
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.add_column(sa.Column('low_stock_threshold', sa.Integer(),
                                       nullable=False, server_default='5'))


def downgrade():
    with op.batch_alter_table('products', schema=None) as batch_op:
        batch_op.drop_column('low_stock_threshold')

    with op.batch_alter_table('orders', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.String(length=30),
               type_=sa.VARCHAR(length=20),
               existing_nullable=False)
        batch_op.drop_column('updated_at')
        batch_op.drop_column('gst_amount')
        batch_op.drop_column('coupon_code')
        batch_op.drop_column('discount_amount')

    op.drop_table('order_status_history')
    op.drop_table('coupons')
    op.drop_table('contacts')
