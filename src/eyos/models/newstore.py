from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class Address(BaseModel):
    first_name: str
    last_name: str
    address_line_1: str
    address_line_2: Optional[str] = ""
    zip_code: str
    city: str
    state: Optional[str] = ""
    country: str
    phone: Optional[str] = ""


class TaxProviderDetail(BaseModel):
    name: str
    amount: float
    rate: float


class OrderItem(BaseModel):
    id: str
    item_type: str
    product_id: str
    pricebook_id: str
    pricebook_price: float
    list_price: float
    item_discounts: float
    order_discounts: float
    tax: float
    tax_provider_details: List[TaxProviderDetail]
    tax_class: str
    quantity: int
    status: str
    shipping_service_level: str
    is_preorder: bool
    future_fulfillment_location_id: str
    shipping_method: str
    extended_attributes: List[Dict[str, Any]] = []
    discounts: List[Dict[str, Any]] = []


class Payment(BaseModel):
    payment_method: str
    card_brand: Optional[str] = None
    card_last4: Optional[str] = None
    amount: float
    currency: str
    status: str


class OrderPayload(BaseModel):
    id: str
    external_id: str
    created_at: datetime
    placed_at: datetime
    completed_at: datetime
    associate_id: str
    associate_email: str
    channel_type: str
    channel: str
    is_exchange: bool
    customer_email: str
    customer_id: str
    external_customer_id: str
    is_historical: bool
    discounts: List[Dict[str, Any]] = []
    billing_address: Address
    shipping_address: Address
    price_method: str
    subtotal: float
    discount_total: float
    shipping_total: float
    shipping_tax: float
    tax_total: float
    grand_total: float
    currency: str
    tax_strategy: str
    tax_exempt: bool
    extended_attributes: List[Dict[str, Any]] = []
    items: List[OrderItem]
    payments: List[Payment]


class NewStoreEvent(BaseModel):
    tenant: str
    name: str
    published_at: datetime
    payload: OrderPayload
