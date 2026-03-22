"""PIIMasker — masks Korean PII before sending text to cloud LLM APIs."""

import re


class PIIMasker:
    """Masks Korean personally identifiable information (PII) using regex patterns.

    Apply this before sending any text to external cloud LLM services to prevent
    sensitive personal data from leaving the organization.
    """

    def __init__(self) -> None:
        # Patterns are ordered: more specific / higher-risk first.
        # Each entry is (compiled_pattern, replacement_string).
        self._patterns: list[tuple[re.Pattern, str]] = [
            # 1. Resident Registration Number (주민등록번호): YYMMDD-[1-4]NNNNNN
            (re.compile(r"\d{6}-[1-4]\d{6}"), "[주민번호]"),

            # 2. Mobile phone (010/011/016/017/018/019)
            (re.compile(r"\b01[016789]-\d{3,4}-\d{4}\b"), "[전화번호]"),

            # 3. Seoul landline (02)
            (re.compile(r"\b02-\d{3,4}-\d{4}\b"), "[전화번호]"),

            # 4. Other area codes (031, 032, … 099)
            (re.compile(r"\b0[3-9]\d-\d{3,4}-\d{4}\b"), "[전화번호]"),

            # 5. Mobile phone without hyphens
            (re.compile(r"(?<!\d)01[016789]\d{7,8}(?!\d)"), "[전화번호]"),

            # 6. Email address
            (re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"), "[이메일]"),

            # 7. Bank account number (3–6 digits) - (2–6 digits) - (4–8 digits)
            #    Applied after phone patterns so already-replaced tokens won't re-match.
            (re.compile(r"(?<!\d)\d{3,6}-\d{2,6}-\d{4,8}(?!\d)"), "[계좌번호]"),

            # 8. Passport number: one uppercase letter followed by 8 digits
            (re.compile(r"(?<![A-Z])[A-Z][0-9]{8}(?!\d)"), "[여권번호]"),

            # 9. Korean address: 시/도 + (시/구/군) + 로/길 + number
            #    Covers "서울특별시 강남구 테헤란로 123", "경기도 성남시 분당구 판교로 456", etc.
            (
                re.compile(
                    r"[가-힣]+(특별시|광역시|특별자치시|특별자치도|시|도)\s*"
                    r"(?:[가-힣]+(시|구|군)\s*)?"
                    r"(?:[가-힣]+(구|군)\s*)?"
                    r"[가-힣]+(로|길)\s*\d+"
                ),
                "[주소]",
            ),
        ]

    def mask(self, text: str) -> str:
        """Return *text* with all recognised PII replaced by placeholder tokens."""
        for pattern, replacement in self._patterns:
            text = pattern.sub(replacement, text)
        return text
