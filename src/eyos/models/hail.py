from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class Amount(BaseModel):
    value: float
    unit: Optional[str] = None


class Currency(BaseModel):
    code: str
    language_code: Optional[str] = None
    country_code: Optional[str] = None


class Associate(BaseModel):
    name: str
    id: str


class TaxAuthority(BaseModel):
    identifier: str
    name: str


class Tax(BaseModel):
    header: str
    footer: Optional[str] = ""
    amount: Amount
    exempt: bool
    net_taxed_amount: Optional[Amount] = None
    rate: float
    gross_taxed_amount: Optional[Amount] = None
    code: str
    reason: str
    authority: Optional[TaxAuthority] = None
    text: str


class SaleItem(BaseModel):
    header: str
    footer: Optional[str] = ""
    quantity: Dict[str, Any]
    total: Dict[str, float]
    sku: str
    currency: Currency
    salesperson: Optional[Associate] = None
    color: Optional[str] = None
    size: Optional[str] = None
    alternate_sku: Optional[str] = ""
    gtin: Optional[str] = ""
    serial_number: Optional[str] = ""
    unit_price: Amount
    original_price: Amount
    text: str
    notes: Optional[str] = ""
    full_text: Optional[str] = ""
    tax: Tax
    discounts: List[Dict[str, Any]] = []
    additional_attributes: Optional[Dict[str, Any]] = None
    gift_numbers: List[str] = []


class Total(BaseModel):
    header: str
    footer: Optional[str] = ""
    amount: Amount
    text: str
    type: str


class Subtotal(BaseModel):
    header: str
    footer: Optional[str] = ""
    amount: Amount
    text: str
    type: str


class Shipping(BaseModel):
    header: str
    footer: Optional[str] = ""
    amount: Amount


class PaymentCard(BaseModel):
    type: str
    start_date: Optional[str] = None
    expiry_date: Optional[str] = None
    name_on_card: Optional[str] = "Customer"
    slip: Optional[str] = ""
    token: Optional[str] = None


class PaymentProvider(BaseModel):
    id: str


class PaymentAuthorization(BaseModel):
    provider: PaymentProvider
    reference_id: str
    approval_code: str
    reference_text: Optional[str] = None
    token: Optional[str] = None


class Tender(BaseModel):
    header: str
    footer: Optional[str] = ""
    type: str
    amount: Amount
    text: str
    payment_card: Optional[PaymentCard] = None
    payment_authorization: Optional[PaymentAuthorization] = None


class TransactionInfo(BaseModel):
    date_time: str
    id: str
    number: str


class FiscalInfo(BaseModel):
    transaction_id: str
    transaction_number: str
    signature: Optional[str] = None
    printer_id: Optional[str] = None


class Discount(BaseModel):
    header: str
    footer: Optional[str] = ""
    text: str
    amount: Amount
    reduction_percent: Optional[float] = None


class Receipt(BaseModel):
    paper_printed: bool = False
    header: str
    footer: str
    total: Total
    sale_items: List[SaleItem]
    currency: Currency
    additional_attributes: Optional[Dict[str, Any]] = None
    associate: Optional[Associate] = None
    barcode: Optional[str] = None
    discounts: List[Discount] = []
    fees: List[Dict[str, Any]] = []
    fiscal_information: Optional[FiscalInfo] = None
    other_totals: List[Dict[str, Any]] = []
    reason: str
    salesperson: Optional[Associate] = None
    other_text: Optional[str] = None
    shipping: Optional[Shipping] = None
    subtotal: Subtotal
    taxes: List[Tax]
    tenders: List[Tender]
    transaction_information: TransactionInfo
    vat_refund_receipt_requested: bool = False


class DeliveryRecipient(BaseModel):
    value: str


class DeliveryChannel(BaseModel):
    channel: str
    recipient: DeliveryRecipient


class ConsentAction(BaseModel):
    identifier: str
    value: Literal["grant_consent", "revoke_consent"]


class Customer(BaseModel):
    consent_actions: List[ConsentAction] = []


class HailTransaction(BaseModel):
    type: str = "transaction"
    device_ref: str
    receipt: Receipt
    flags: List[str] = []
    delivery_channels: List[DeliveryChannel]
    customer: Optional[Customer] = None
