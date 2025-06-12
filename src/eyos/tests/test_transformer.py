import json
from pathlib import Path

import pytest

from eyos.models.hail import HailTransaction
from eyos.models.newstore import NewStoreEvent
from eyos.services.transformer import transform_newstore_to_hail


@pytest.fixture
def sample_newstore_event() -> NewStoreEvent:
    """Load sample NewStore event data."""
    sample_file = Path(__file__).parent.parent.parent.parent / "newstore_sample_payload.json"
    with open(sample_file, "r") as f:
        data = json.load(f)
    return NewStoreEvent(**data)


@pytest.mark.asyncio
async def test_transform_newstore_to_hail(sample_newstore_event: NewStoreEvent) -> None:
    """Test the transformation from NewStore to Hail format."""
    # Transform the event
    hail_transaction = await transform_newstore_to_hail(sample_newstore_event)

    # Validate the result is a HailTransaction
    assert isinstance(hail_transaction, HailTransaction)

    # Validate the basic structure
    assert hail_transaction.type == "transaction"
    assert hail_transaction.device_ref.startswith("NEWLOOK-DEVICE")

    # Validate receipt
    assert hail_transaction.receipt.total.amount.value == 150.0
    assert hail_transaction.receipt.total.amount.unit == "GBP"

    # Validate items
    assert len(hail_transaction.receipt.sale_items) == 2

    # Validate delivery channels
    assert len(hail_transaction.delivery_channels) == 1
    assert hail_transaction.delivery_channels[0].channel == "email"
    assert hail_transaction.delivery_channels[0].recipient.value == "alice.smith@example.com"


@pytest.mark.asyncio
async def test_transform_sale_items(sample_newstore_event: NewStoreEvent) -> None:
    """Test the transformation of sale items."""
    # Transform the event
    hail_transaction = await transform_newstore_to_hail(sample_newstore_event)

    # Validate the first sale item
    item = hail_transaction.receipt.sale_items[0]
    assert item.sku == "SKU-1001"
    assert item.quantity["value"] == 1
    assert item.total["value"] == 50.0

    # Validate the tax calculation
    assert item.tax.amount.value == 10.0
    assert item.tax.rate == 20.0
    assert item.tax.exempt is False


@pytest.mark.asyncio
async def test_transform_tenders(sample_newstore_event: NewStoreEvent) -> None:
    """Test the transformation of payment tenders."""
    # Transform the event
    hail_transaction = await transform_newstore_to_hail(sample_newstore_event)

    # Validate the tender
    assert len(hail_transaction.receipt.tenders) == 1
    tender = hail_transaction.receipt.tenders[0]
    assert tender.amount.value == 150.0
    assert tender.amount.unit == "GBP"
    assert tender.type == "card"
    assert tender.payment_card is not None
    assert tender.payment_card.type == "VISA"
