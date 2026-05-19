import pytest
from app.pipeline.preprocessing import preprocess_text


def test_lowercase():
    assert preprocess_text("СРОЧНО КРЕДИТ") == "срочно кредит"


def test_masks_http_url():
    result = preprocess_text("Перейди на https://evil-bank.com/steal")
    assert "<URL>" in result
    assert "https://evil-bank.com" not in result


def test_masks_www_url():
    result = preprocess_text("зайди на www.phishing.ru прямо сейчас")
    assert "<URL>" in result
    assert "www.phishing.ru" not in result


def test_masks_russian_phone():
    result = preprocess_text("позвони +7 (999) 123-45-67 срочно")
    assert "<PHONE>" in result
    assert "999" not in result


def test_masks_short_russian_phone():
    result = preprocess_text("звони 8-800-555-35-35 бесплатно")
    assert "<PHONE>" in result


def test_masks_compact_phone():
    result = preprocess_text("номер 89161234567 для связи")
    assert "<PHONE>" in result


def test_masks_email():
    result = preprocess_text("пиши на support@evil-bank.ru немедленно")
    assert "<EMAIL>" in result
    assert "support@evil-bank.ru" not in result


def test_normalizes_whitespace():
    assert preprocess_text("hello   world\t\nfoo") == "hello world foo"


def test_empty_string():
    assert preprocess_text("") == ""


def test_url_masked_before_lowercase():
    result = preprocess_text("VISIT HTTPS://SCAM.COM NOW")
    assert "<url>" in result or "<URL>" in result
    assert "HTTPS://SCAM.COM" not in result


def test_multiple_pii_in_one_text():
    text = "позвони +7(999)1234567 или напиши user@bank.ru или зайди на https://scam.ru"
    result = preprocess_text(text)
    assert "<PHONE>" in result
    assert "<EMAIL>" in result
    assert "<URL>" in result


def test_plain_text_unchanged_structure():
    result = preprocess_text("простой текст без пии")
    assert result == "простой текст без пии"
    assert "<PHONE>" not in result
    assert "<EMAIL>" not in result
    assert "<URL>" not in result
