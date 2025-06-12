#!/usr/bin/env python3
"""
Example client for NewStore to Hail integration API.

This script demonstrates how to interact with the API programmatically.
"""
import asyncio
import json
import sys
from pathlib import Path

import httpx


async def send_webhook_event(event_file: str = "../newstore_sample_payload.json", url: str = "http://localhost:8000/webhooks/newstore/simulate"):
    """Send a webhook event to the API."""
    # Load the event from file
    try:
        event_path = Path(event_file)
        if not event_path.exists():
            # Try a relative path
            event_path = Path(__file__).parent / event_file

        if not event_path.exists():
            print(f"Error: Event file not found: {event_file}")
            return False

        with open(event_path, "r") as f:
            event_data = json.load(f)

        # Send the event to the API
        print(f"Sending event to {url}")
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=event_data)

        if response.status_code == 202:
            print("Event accepted for processing")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"Error: {e!s}")
        return False


async def check_api_status(url: str = "http://localhost:8000"):
    """Check if the API is running."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url)

        if response.status_code == 200:
            print("API is running")
            print(json.dumps(response.json(), indent=2))
            return True
        else:
            print(f"API returned status code: {response.status_code}")
            return False

    except Exception as e:
        print(f"API is not running: {e!s}")
        return False


async def main():
    """Main entry point."""
    # Check if the API is running
    api_running = await check_api_status()

    if not api_running:
        print("\nAPI is not running. Start it with:")
        print("  rye run dev")
        sys.exit(1)

    # Send a sample event
    print("\nSending a sample event...")
    event_file = "../newstore_sample_payload.json"
    if len(sys.argv) > 1:
        event_file = sys.argv[1]

    await send_webhook_event(event_file)


if __name__ == "__main__":
    asyncio.run(main())
