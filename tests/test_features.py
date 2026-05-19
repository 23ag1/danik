import pytest
from app.pipeline.features import extract_features


def test_text_len():
    assert extract_features("hello")["text_len"] == 5


def test_word_count():
    assert extract_features("hello world foo")["word_count"] == 3


def test_uppercase_ratio_all_upper():
    features = extract_features("HELLO")
    assert features["uppercase_ratio"] == pytest.approx(1.0)


def test_uppercase_ratio_mixed():
    features = extract_features("Hello World")
    # H, W = 2 uppercase out of 11 chars
    assert features["uppercase_ratio"] == pytest.approx(2 / 11)


def test_uppercase_ratio_no_upper():
    assert extract_features("hello world")["uppercase_ratio"] == pytest.approx(0.0)


def test_exclamation_count():
    assert extract_features("Win now!!! Hurry!")["exclamation_count"] == 4


def test_exclamation_count_zero():
    assert extract_features("calm text here")["exclamation_count"] == 0


def test_question_count():
    assert extract_features("who? what? why?")["question_count"] == 3


def test_has_url_true():
    assert extract_features("visit https://scam.com now")["has_url"] is True


def test_has_url_www():
    assert extract_features("go to www.evil.ru")["has_url"] is True


def test_has_url_false():
    assert extract_features("no link here at all")["has_url"] is False


def test_has_phone_true():
    assert extract_features("call +7 (999) 123-45-67 now")["has_phone"] is True


def test_has_phone_false():
    assert extract_features("no phone in this text")["has_phone"] is False


def test_has_email_true():
    assert extract_features("write to user@bank.ru now")["has_email"] is True


def test_has_email_false():
    assert extract_features("no email in this text")["has_email"] is False


def test_empty_text_no_zero_division():
    features = extract_features("")
    assert features["text_len"] == 0
    assert features["word_count"] == 0
    assert features["uppercase_ratio"] == pytest.approx(0.0)
    assert features["has_url"] is False
    assert features["has_phone"] is False
    assert features["has_email"] is False


def test_uppercase_ratio_uses_raw_text():
    # uppercase_ratio must reflect the original case, not post-lowercase
    features = extract_features("СРОЧНО кредит")
    assert features["uppercase_ratio"] > 0.0


def test_returns_correct_keys():
    keys = extract_features("test text").keys()
    expected = {"text_len", "word_count", "exclamation_count", "question_count",
                "uppercase_ratio", "has_url", "has_phone", "has_email"}
    assert expected.issubset(keys)
