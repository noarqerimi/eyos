import logging
from typing import Any, Dict

from fastapi import APIRouter, Body, status

from eyos.models import HailTransaction

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/mock/hail",
    tags=["mock"],
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"},
    }
)


@router.post(
    "/events/v2/transaction/",
    status_code=status.HTTP_200_OK,
    summary="Mock Hail API transaction endpoint",
)
async def mock_hail_transaction(
    transaction: HailTransaction = Body(...)
) -> Dict[str, Any]:
    """
    Mock endpoint for the Hail API transaction endpoint.

    This endpoint simulates the behavior of the Hail API for testing purposes.

    Args:
        transaction: The transaction to process

    Returns:
        A mock response from the Hail API
    """
    # Log the receipt for debugging
    logger.info(f"Received transaction: {transaction.receipt.transaction_information.id}")

    # Log some details for debugging
    logger.debug(
        f"Transaction details:\n"
        f"- Device: {transaction.device_ref}\n"
        f"- Total: {transaction.receipt.total.amount.value} {transaction.receipt.total.amount.unit}\n"
        f"- Items: {len(transaction.receipt.sale_items)}\n"
        f"- Delivery: {[ch.channel for ch in transaction.delivery_channels]}"
    )

    # Simulate processing the transaction
    return {
        "status": "success",
        "transaction_id": transaction.receipt.transaction_information.id,
        "message": "Transaction processed successfully"
    }
