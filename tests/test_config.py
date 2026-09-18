from e_block_bot.config import Settings


def test_settings_validate_and_expose_timezone(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("E_BLOCK_TIMEZONE", "Asia/Singapore")

    settings = Settings()

    assert settings.telegram_bot_token.get_secret_value() == "test-token"
    assert settings.timezone.key == "Asia/Singapore"


def test_settings_reject_unknown_timezone(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("E_BLOCK_TIMEZONE", "Not/A_Timezone")

    try:
        Settings()
    except ValueError as error:
        assert "Unknown timezone" in str(error)
    else:
        raise AssertionError("Settings should reject an unknown timezone")


def test_settings_reject_invalid_daily_limit(monkeypatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("MAX_DAILY_BOOKING_MINUTES", "100")
    monkeypatch.setenv("SLOT_INCREMENT_MINUTES", "30")

    try:
        Settings()
    except ValueError as error:
        assert "configured time increment" in str(error)
    else:
        raise AssertionError("Settings should reject an invalid daily limit")
