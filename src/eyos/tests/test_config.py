import os

from eyos.config import get_settings


def test_default_settings():
    """Test that default settings are loaded correctly."""
    settings = get_settings()

    assert settings.api_title == "NewStore to Hail Integration"
    assert settings.api_version == "0.1.0"
    assert settings.hail_api_max_retries == 3
    assert settings.newstore_webhook_secret == "mock_webhook_secret"


def test_env_override():
    """Test that environment variables override default settings."""
    # Set environment variables
    os.environ["EYOS_API_TITLE"] = "Custom API Title"
    os.environ["EYOS_HAIL_API_MAX_RETRIES"] = "5"

    # Get settings
    settings = get_settings()

    # Check that environment variables were used
    assert settings.api_title == "Custom API Title"
    assert settings.hail_api_max_retries == 5

    # Clean up
    del os.environ["EYOS_API_TITLE"]
    del os.environ["EYOS_HAIL_API_MAX_RETRIES"]


def test_supported_events():
    """Test that supported events are loaded correctly."""
    settings = get_settings()

    assert "order.completed" in settings.newstore_supported_events
