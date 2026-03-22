"""Unit tests for PIIMasker."""

import pytest
from gongmun_doctor.llm.pii_masker import PIIMasker


@pytest.fixture
def masker():
    return PIIMasker()


class TestRRN:
    def test_masks_rrn(self, masker):
        text = "주민등록번호는 901231-1234567입니다."
        assert "[주민번호]" in masker.mask(text)
        assert "901231-1234567" not in masker.mask(text)

    def test_masks_rrn_with_spaces(self, masker):
        text = "주민번호: 850101-2345678 확인"
        assert "[주민번호]" in masker.mask(text)


class TestPhone:
    def test_masks_mobile(self, masker):
        text = "연락처: 010-1234-5678"
        assert "[전화번호]" in masker.mask(text)
        assert "010-1234-5678" not in masker.mask(text)

    def test_masks_landline_seoul(self, masker):
        text = "전화: 02-1234-5678"
        assert "[전화번호]" in masker.mask(text)

    def test_masks_landline_other(self, masker):
        text = "담당자 연락처: 031-123-4567"
        assert "[전화번호]" in masker.mask(text)

    def test_masks_phone_no_hyphen(self, masker):
        text = "전화번호 01012345678"
        assert "[전화번호]" in masker.mask(text)


class TestEmail:
    def test_masks_email(self, masker):
        text = "이메일: hong@example.com 로 연락하세요."
        assert "[이메일]" in masker.mask(text)
        assert "hong@example.com" not in masker.mask(text)

    def test_masks_gov_email(self, masker):
        text = "담당자: kim@seoul.go.kr"
        assert "[이메일]" in masker.mask(text)


class TestBankAccount:
    def test_masks_bank_account(self, masker):
        text = "계좌번호: 123-456-789012"
        assert "[계좌번호]" in masker.mask(text)
        assert "123-456-789012" not in masker.mask(text)


class TestPassport:
    def test_masks_passport(self, masker):
        text = "여권번호 M12345678 확인"
        assert "[여권번호]" in masker.mask(text)
        assert "M12345678" not in masker.mask(text)


class TestAddress:
    def test_masks_si_gu_address(self, masker):
        text = "주소: 서울특별시 강남구 테헤란로 123"
        result = masker.mask(text)
        assert "[주소]" in result

    def test_masks_do_address(self, masker):
        text = "경기도 성남시 분당구 판교로 456"
        assert "[주소]" in masker.mask(text)


class TestClean:
    def test_clean_text_unchanged(self, masker):
        text = "본 공문은 2024년도 예산안에 관한 사항입니다."
        assert masker.mask(text) == text

    def test_multiple_pii_all_masked(self, masker):
        text = "홍길동(010-1234-5678, hong@gov.kr) 주민번호 901231-1234567"
        result = masker.mask(text)
        assert "010-1234-5678" not in result
        assert "hong@gov.kr" not in result
        assert "901231-1234567" not in result
