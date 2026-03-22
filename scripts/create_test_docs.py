"""
Generate test HWPX documents with deliberate errors for PoC testing.
"""
from hwpx.document import HwpxDocument
from pathlib import Path


def create_test_doc_01(output_path: str):
    """도로 보수공사 시행 알림 — contains 10+ deliberate errors."""
    doc = HwpxDocument.new()

    lines = [
        # Error: "시행알림" → "시행 알림" (spacing)
        "공문 제목: 도로 보수공사 시행알림",
        "",
        # Error: "관련:" → "관련 :" space before colon is wrong in 공문서
        # Error: "도시과 -" → "도시과-" (no space before hyphen)
        "1. 관련 : 도시과 -1234호 (2026.03.15.)",
        "",
        # Error: "시행하오니" → OK but "참고 하시기" → "참고하시기" (spacing)
        # Error: "바랍니다" is correct but "관련하여," → "관련하여" (no comma in 공문서)
        "2. 위 호와 관련하여, 아래와 같이 도로 보수공사를 시행하오니 업무에 참고 하시기 바랍니다.",
        "",
        # Error: "공사명:" → "공사명 :" (no, actually "공사명:" is wrong in 공문서, should have space)
        # Actually in 공문서 the colon style varies. Let's use a different error.
        # Error: "양주시" OK, "보수 공사" → "보수공사" (should not split)
        "  가. 공사명: 양주시 OO로 보수 공사",
        "",
        # Error: "2026.04.01~2026.06.30" → "2026. 4. 1. ~ 2026. 6. 30." (date format)
        "  나. 공사기간: 2026.04.01~2026.06.30",
        "",
        # Error: "오억원" → "금 500,000,000원" or "금 오억원" (금 prefix missing)
        # Error: "5억원" mixed style
        "  다. 공사금액: 5억원",
        "",
        "  라. 시공업체: OO건설(주)",
        "",
        # Error: "붙임 1." → "붙임  1." (double space after 붙임)
        "붙임 1. 설계도면 1부.",
        # Error: missing "끝." at the end
        "      2. 공사내역서 1부.",
        "",
        # Error: "시행하겠습니다" mixed with "바랍니다" (inconsistent ending style)
        "3. 아울러, 공사기간중 교통 통제가 예상되오니 관계 부서에서는 적극 협조하여 주시기를 부탁드립니다.",
        "",
        # Error: "되시기" → "되기" (honorific misuse)
        # Error: "문의사항이 있으시면" → "문의 사항이 있으면" (spacing + honorific)
        "4. 문의사항이 있으시면 토목과 도로팀(☎ 031-1234-5678)으로 연락 주시면 되시기 바랍니다.",
    ]

    for line in lines:
        doc.add_paragraph(line)

    doc.save_to_path(output_path)
    print(f"[OK] Test doc 01 created: {output_path}")


def create_test_doc_02(output_path: str):
    """준공검사 요청 — contains formatting and style errors."""
    doc = HwpxDocument.new()

    lines = [
        "공문 제목: OO사업 준공검사 요청",
        "",
        "1. 관련: 건설과-5678호(2026. 1. 15.)",
        "",
        # Error: "완료되었기에" → "완료되었으므로" (more formal)
        # Error: "하여주시기" → "하여 주시기" (spacing)
        "2. 위 호와 관련하여 OO사업이 완료되었기에 준공검사를 요청하오니 검토하여주시기 바랍니다.",
        "",
        "  가. 사업명: OO지구 하수관로 정비사업",
        # Error: "2025.03.01.~2026.02.28." spacing
        "  나. 사업기간: 2025.03.01.~2026.02.28.",
        "  다. 사업비: 금 1,200,000,000원",
        "  라. 시공업체: △△건설(주)",
        "",
        # Error: "붙임" format
        "붙임 1. 준공검사 요청서 1부.",
        "      2. 준공도서 1부.",
        "      3. 기성검사 조서 1부.  끝.",
    ]

    for line in lines:
        doc.add_paragraph(line)

    doc.save_to_path(output_path)
    print(f"[OK] Test doc 02 created: {output_path}")


def create_test_doc_03(output_path: str):
    """업무 협조 요청 — contains common phrasing errors."""
    doc = HwpxDocument.new()

    lines = [
        "공문 제목: 도로점용 허가 관련 업무협조 요청",
        "",
        # Error: "관련:" colon directly attached
        "1. 관련: 도로과-9012호(2026. 2. 20.)",
        "",
        # Error: "대해서" → "대하여" (formal), "할려고" → "하려고"
        "2. 위 호와 관련, OO 도로에 대해서 점용허가를 할려고 하오니 아래 사항에 대해 협조하여 주시기 바랍니다.",
        "",
        # Error: "점용위치" → "점용 위치" (spacing)
        "  가. 점용위치: 양주시 OO로 123번길 일원",
        # Error: "점용목적" → "점용 목적"
        "  나. 점용목적: 상수도관 매설",
        # Error: "점용기간" → "점용 기간"
        "  다. 점용기간: 2026. 4. 1. ~ 2026. 5. 31.",
        "",
        # Error: "검토해 주시기 바랍니다" → OK but "회신하여 주세요" inconsistent (주세요 vs 바랍니다)
        "3. 상기 사항을 검토하시어 2026. 3. 30.까지 회신하여 주세요.",
        "",
        "붙임 1. 도로점용 허가 신청서 1부.",
        "      2. 위치도 1부.  끝.",
    ]

    for line in lines:
        doc.add_paragraph(line)

    doc.save_to_path(output_path)
    print(f"[OK] Test doc 03 created: {output_path}")


if __name__ == "__main__":
    out = Path("test_docs")
    out.mkdir(exist_ok=True)
    create_test_doc_01(str(out / "test_01_road_repair.hwpx"))
    create_test_doc_02(str(out / "test_02_completion_inspect.hwpx"))
    create_test_doc_03(str(out / "test_03_cooperation_request.hwpx"))
    print("\n[DONE] All test documents created.")
