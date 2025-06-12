import uuid
from typing import Any, Dict, List

from eyos.models.hail import (
    Amount,
    Associate,
    ConsentAction,
    Currency,
    Customer,
    DeliveryChannel,
    DeliveryRecipient,
    HailTransaction,
    PaymentAuthorization,
    PaymentCard,
    PaymentProvider,
    Receipt,
    SaleItem,
    Subtotal,
    Tax,
    TaxAuthority,
    Tender,
    Total,
    TransactionInfo,
)
from eyos.models.newstore import NewStoreEvent, OrderItem


async def transform_newstore_to_hail(event: NewStoreEvent) -> HailTransaction:
    """
    Transform a NewStore event to a Hail transaction format.

    Args:
        event: The NewStore event to transform

    Returns:
        The transformed Hail transaction
    """
    # Extract common data
    order = event.payload
    tenant = event.tenant

    # Transform currency
    currency = Currency(
        code=order.currency,
        language_code="en",  # Assumption: Default to English
        country_code=order.shipping_address.country
    )

    # Transform sale items
    sale_items = await _transform_sale_items(order.items, currency, order.associate_id)

    # Create transaction information
    transaction_info = TransactionInfo(
        date_time=order.completed_at.isoformat(),
        id=f"TRX-{tenant}-{order.id}",
        number=order.external_id
    )

    # Create fiscal information
    fiscal_info = {
        "transaction_id": order.id,
        "transaction_number": order.external_id,
        "signature": f"DigitalSignature-{order.id}",
        "printer_id": f"Printer-{order.channel}"
    }

    # Transform payments to tenders
    tenders = await _transform_payments_to_tenders(order.payments, order.currency)

    # Create associate
    associate = Associate(
        name=order.associate_email.split('@')[0].replace('.', ' ').title(),
        id=order.associate_id
    )

    # Create total
    total = Total(
        header="Total",
        footer="Includes all applicable taxes",
        amount=Amount(value=order.grand_total, unit=order.currency),
        text="Total Amount Due",
        type="Total"
    )

    # Create subtotal
    subtotal = Subtotal(
        header="Subtotal",
        footer="",
        amount=Amount(value=order.subtotal, unit=order.currency),
        text="Subtotal before taxes",
        type="Subtotal"
    )

    # Create taxes
    taxes = [
        Tax(
            header="VAT",
            footer="",
            amount=Amount(value=order.tax_total, unit=order.currency),
            exempt=order.tax_exempt,
            net_taxed_amount=Amount(value=order.subtotal, unit=order.currency),
            rate=20,  # Assumption based on the sample data
            gross_taxed_amount=Amount(value=order.grand_total, unit=order.currency),
            code="VAT20",
            reason="Standard rate",
            authority=TaxAuthority(
                identifier=f"{order.shipping_address.country}VAT",
                name="Tax Authority"
            ),
            text="Value Added Tax at 20%"
        )
    ]

    # Create receipt
    receipt = Receipt(
        paper_printed=False,
        header=f"{tenant.capitalize()} - Receipt",
        footer=f"Thank you for shopping with {tenant.capitalize()}!",
        total=total,
        sale_items=sale_items,
        currency=currency,
        additional_attributes={
            "product_category": "Fashion",
            "brand": tenant.capitalize(),
            "store_id": order.channel
        },
        associate=associate,
        barcode=f"{tenant.upper()}-{order.external_id}",
        discounts=[],
        fees=[],
        fiscal_information=fiscal_info,
        other_totals=[],
        reason="Purchase",
        salesperson=associate,
        other_text="Receipt",
        shipping=None,  # In-store purchase
        subtotal=subtotal,
        taxes=taxes,
        tenders=tenders,
        transaction_information=transaction_info,
        vat_refund_receipt_requested=False
    )

    # Create delivery channels
    delivery_channels = [
        DeliveryChannel(
            channel="email",
            recipient=DeliveryRecipient(value=order.customer_email)
        )
    ]

    # Create customer consent
    customer = Customer(
        consent_actions=[
            ConsentAction(identifier="general", value="grant_consent")
        ]
    )

    # Create the transaction
    transaction = HailTransaction(
        type="transaction",
        device_ref=f"{tenant.upper()}-DEVICE-{order.channel}",
        receipt=receipt,
        flags=[],
        delivery_channels=delivery_channels,
        customer=customer
    )

    return transaction


async def _transform_sale_items(
    items: List[OrderItem],
    currency: Currency,
    associate_id: str
) -> List[SaleItem]:
    """Transform order items to sale items."""
    sale_items = []

    for item in items:
        tax_detail = item.tax_provider_details[0] if item.tax_provider_details else None
        tax_rate = tax_detail.rate * 100 if tax_detail else 20  # Default to 20% if not provided

        # Create tax
        tax = Tax(
            header="VAT",
            footer="",
            amount=Amount(value=item.tax, unit=currency.code),
            exempt=False,
            net_taxed_amount=Amount(
                value=item.list_price - item.tax,
                unit=currency.code
            ),
            rate=tax_rate,
            gross_taxed_amount=Amount(value=item.list_price, unit=currency.code),
            code=f"VAT{int(tax_rate)}",
            reason="Standard rate",
            authority=TaxAuthority(
                identifier=f"{currency.country_code}VAT",
                name="Tax Authority"
            ),
            text=f"VAT at {int(tax_rate)}%"
        )

        # Create sale item
        sale_item = SaleItem(
            header=f"Product {item.product_id}",
            footer="",
            quantity={"value": item.quantity, "unit": "piece"},
            total={"value": item.list_price},
            sku=item.product_id,
            currency=currency,
            salesperson=Associate(
                name=f"Associate {associate_id[-6:]}",
                id=associate_id
            ),
            color=None,
            size=None,
            alternate_sku="",
            gtin="",
            serial_number="",
            unit_price=Amount(value=item.list_price / item.quantity, unit=currency.code),
            original_price=Amount(value=item.list_price / item.quantity, unit=currency.code),
            text=f"Product {item.product_id}",
            notes="",
            full_text=f"Product {item.product_id} x{item.quantity}",
            tax=tax,
            discounts=[],
            additional_attributes=None,
            gift_numbers=[]
        )

        sale_items.append(sale_item)

    return sale_items


async def _transform_payments_to_tenders(
    payments: List[Dict[str, Any]],
    currency_code: str
) -> List[Tender]:
    """Transform payments to tenders."""
    tenders = []

    for payment in payments:
        # Create payment card if applicable
        payment_card = None
        payment_auth = None

        # Check if this is a dict or a Pydantic model
        # Instead of checking model_fields, check if it's a dict directly
        if not isinstance(payment, dict):
            # This is a Pydantic model, access attributes directly
            card_brand = payment.card_brand if hasattr(payment, 'card_brand') else None
            payment_method = payment.payment_method
            amount = payment.amount
        else:
            # This is a dict, use get method
            card_brand = payment.get("card_brand")
            payment_method = payment.get("payment_method", "Payment")
            amount = payment.get("amount", 0)

        if card_brand:
            payment_card = PaymentCard(
                type=card_brand,
                expiry_date="01/30",  # Assumption
                name_on_card="Customer",
                token=f"CardToken{uuid.uuid4().hex[:10]}"
            )

            payment_auth = PaymentAuthorization(
                provider=PaymentProvider(id=f"{card_brand}Provider"),
                reference_id=f"AuthRef{uuid.uuid4().hex[:8]}",
                approval_code=f"Approval{uuid.uuid4().hex[:8]}",
                reference_text="Fashion payment",
                token=f"fashiontoken{uuid.uuid4().hex[:8]}"
            )

        # Create tender
        tender = Tender(
            header=payment_method,
            footer="",
            type="card" if card_brand else "cash",
            amount=Amount(value=amount, unit=currency_code),
            text=f"Total paid by {card_brand if card_brand else 'Cash'}",
            payment_card=payment_card,
            payment_authorization=payment_auth
        )

        tenders.append(tender)

    return tenders
