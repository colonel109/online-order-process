from sqlalchemy import Integer, String, Column, ForeignKey, DateTime, Numeric
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Combo(Base):
    __tablename__ = 'combo'
    combo_key = Column(Integer, primary_key=True)
    combo_name = Column(String, unique=True)

    combo_variant_link = relationship('ComboVariant', back_populates='combo_link')


class Variant(Base):
    __tablename__ = 'variant'
    variant_key = Column(Integer, primary_key=True)
    variant_name = Column(String, unique=True)

    combo_variant_link = relationship('ComboVariant', back_populates='variant_link')


class ComboVariant(Base):
    __tablename__ = 'combo_variant'
    combo_variant_key = Column(Integer, primary_key=True)
    combo_key = Column(Integer, ForeignKey('combo.combo_key'))
    variant_key = Column(Integer, ForeignKey('variant.variant_key'))

    combo_link = relationship('Combo', back_populates='combo_variant_link')
    variant_link = relationship('Variant', back_populates='combo_variant_link')
    combo_detail_link = relationship('ComboDetail', back_populates='combo_variant_link')


class ProductType(Base):
    __tablename__ = 'product_type'
    product_type_key = Column(Integer, primary_key=True)
    product_type_name = Column(String, unique=True)

    product_link = relationship('Product', back_populates='product_type_link')


class Product(Base):
    __tablename__ = 'product'
    product_key = Column(Integer, primary_key=True)
    product_code = Column(String, unique=True)
    product_name = Column(String, unique=True)
    product_type_key = Column(Integer, ForeignKey('product_type.product_type_key'))

    product_type_link = relationship('ProductType', back_populates='product_link')
    combo_detail_link = relationship('ComboDetail', back_populates='product_link')


class ComboDetail(Base):
    __tablename__ = 'combo_detail'
    combo_detail_key = Column(Integer, primary_key=True)
    combo_variant_key = Column(Integer, ForeignKey('combo_variant.combo_variant_key'), nullable=False)
    combo_composition_key = Column(Integer, nullable=False)
    product_key = Column(Integer, ForeignKey('product.product_key'), nullable=False)
    product_price = Column(Numeric, nullable=False)
    product_quantity = Column(Numeric, nullable=False)
    created_date = Column(DateTime)
    updated_date = Column(DateTime)

    combo_variant_link = relationship('ComboVariant', back_populates='combo_detail_link')
    product_link = relationship('Product', back_populates='combo_detail_link')


class ShopeeOrder(Base):
    __tablename__ = 'shopee_orders'

    order_key = Column(Integer, primary_key=True)
    order_id = Column(String)
    package_id = Column(String)
    order_date = Column(DateTime)
    order_status = Column(String)
    ready_to_ship_combo = Column(String)
    top_selling_combo = Column(String)
    buyer_comment = Column(String)
    tracking_number = Column(String)
    shipping_carrier = Column(String)
    shipping_method = Column(String)
    order_type = Column(String)
    ship_out_date = Column(DateTime)
    estimated_delivery_date = Column(DateTime)
    local_delivery_date = Column(DateTime)
    delivery_time = Column(DateTime)
    order_completion_time = Column(DateTime)
    return_refund_status = Column(String)
    cancellation_date = Column(DateTime)
    fulfilled_by_shopee = Column(String)
    combo_sku = Column(String)
    combo_name = Column(String)
    combo_weight = Column(Numeric(15, 2))
    total_weight = Column(Numeric(15, 2))
    warehouse_name = Column(String)
    combo_variation_sku = Column(String)
    variant_name = Column(String)
    owned_by_shopee = Column(String)
    original_price = Column(Numeric(15, 2))
    seller_subsidy = Column(Numeric(15, 2))
    shopee_subsidy = Column(Numeric(15, 2))
    total_seller_subsidy_amount = Column(Numeric(15, 2))
    deal_price = Column(Numeric(15, 2))
    quantity = Column(Integer)
    returned_quantity = Column(Integer)
    total_buyer_payment_amount = Column(Numeric(15, 2))
    total_order_value_vnd = Column(Numeric(15, 2))
    shop_voucher = Column(Numeric(15, 2))
    coin_cashback = Column(Numeric(15, 2))
    shopee_voucher = Column(Numeric(15, 2))
    bundle_deal_indicator = Column(String)
    shopee_bundle_discount = Column(Numeric(15, 2))
    shop_bundle_discount = Column(Numeric(15, 2))
    shopee_coins_redeemed = Column(Numeric(15, 2))
    debit_card_discount = Column(Numeric(15, 2))
    trade_in_discount = Column(Numeric(15, 2))
    trade_in_bonus = Column(Numeric(15, 2))
    estimated_shipping_fee = Column(Numeric(15, 2))
    trade_in_bonus_by_seller = Column(Numeric(15, 2))
    shipping_fee_paid_by_buyer = Column(Numeric(15, 2))
    return_shipping_fee = Column(Numeric(15, 2))
    grand_total_buyer_payment = Column(Numeric(15, 2))
    payment_time = Column(DateTime)
    escrow_verification_date = Column(DateTime)
    payment_method = Column(String)
    fixed_fee = Column(Numeric(15, 2))
    service_fee = Column(Numeric(15, 2))
    transaction_fee = Column(Numeric(15, 2))
    escrow_amount = Column(Numeric(15, 2))
    buyer_username = Column(String)
    recipient_name = Column(String)
    phone_number = Column(String)
    province_city = Column(String)
    city_district = Column(String)
    district = Column(String)
    delivery_address = Column(String)
    country = Column(String)
    note = Column(String)
    source_file = Column(String)