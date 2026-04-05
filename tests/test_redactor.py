from privacyguard.engine.redactor import Redactor


def test_redacts_multiple_categories() -> None:
    engine = Redactor()
    text = (
        "Alice Johnson can be reached at alice@example.com or +1 (202) 555-0137. "
        "Her card is 4242 4242 4242 4242 and server IP is 192.168.1.10. "
        "Use key sk-abcdefghijklmnopqrstuvwxyz12345 for the API."
    )

    result = engine.redact(text)

    assert "[EMAIL_" in result.redacted_text
    assert "[PHONE_" in result.redacted_text
    assert "[PERSON_" in result.redacted_text
    assert "[CREDIT_CARD_" in result.redacted_text
    assert "[IPV4_" in result.redacted_text
    assert "[OPENAI_KEY_" in result.redacted_text or "[GENERIC_SECRET_" in result.redacted_text


def test_restore_text_roundtrip() -> None:
    engine = Redactor()
    text = "Contact Bob Stone at bob@example.com"

    result = engine.redact(text)
    restored = result.restore_text()

    assert restored == text


def test_disable_email_detection() -> None:
    engine = Redactor()
    text = "Email jane@example.com and call 202-555-0111"

    result = engine.redact(text, enabled_categories={"emails": False, "phones": True})

    assert "jane@example.com" in result.redacted_text
    assert "[PHONE_" in result.redacted_text


def test_overlap_prefers_pii_over_custom_on_equal_span() -> None:
    engine = Redactor()
    text = "Primary email: test.user@example.com"

    result = engine.redact(text, custom_regex=[r"test\.user@example\.com"])

    assert "[EMAIL_1]" in result.redacted_text
    assert "CUSTOM" not in result.redacted_text
