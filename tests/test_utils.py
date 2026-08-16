import re

from app.utils import check_crisis, generate_session_code, allowed_file


def test_check_crisis_detects_keyword():
    assert check_crisis("aku pengen mati aja rasanya") is True


def test_check_crisis_ignores_normal_text():
    assert check_crisis("hari ini aku ngerasa cukup baik") is False


def test_check_crisis_case_insensitive():
    assert check_crisis("MENDING GW MATI") is True


def test_generate_session_code_format():
    code = generate_session_code()
    assert re.match(r"^CK-\d{4}$", code)


def test_allowed_file_accepts_images():
    assert allowed_file("foto.jpg") is True
    assert allowed_file("foto.PNG") is True


def test_allowed_file_rejects_others():
    assert allowed_file("script.exe") is False
    assert allowed_file("noext") is False
