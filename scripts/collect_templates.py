"""
공문 서식 수집 파이프라인.

실제 공공기관 사이트에서 공문 서식을 수집하고 templates/*.json 형식으로 변환한다.

Usage:
    python scripts/collect_templates.py [--verify] [--category CATEGORY]

Options:
    --verify       기존 templates/*.json의 source_url 유효성만 검사
    --category     특정 카테고리만 수집 (gen/con/proc/hr/civil/audit)
    --dry-run      실제 저장하지 않고 수집 결과만 출력
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any

# ─── 경로 설정 ────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
TEMPLATE_DIR = ROOT / "src" / "gongmun_doctor" / "agents" / "administrative" / "templates"
RAW_DIR = ROOT / "data" / "raw_templates"

# ─── 수집 대상 소스 정의 ──────────────────────────────────────────────────────

SOURCES: dict[str, list[dict[str, str]]] = {
    "행정안전부": [
        {
            "name": "행정업무운영편람 (행정규칙)",
            "url": "https://www.mois.go.kr/frt/bbs/type001/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000012&nttId=83951",
            "description": "일반행정 공문서 작성 기준 및 서식",
            "categories": ["gen", "hr"],
        },
    ],
    "국가법령정보센터": [
        {
            "name": "건설공사 사업관리방식 검토기준 및 업무수행지침",
            "url": "https://www.law.go.kr/LSW/admRulInfoP.do?admRulSeq=2100000133829",
            "description": "건설/토목 공문 서식 (착공, 준공, 검사 등)",
            "categories": ["con"],
        },
        {
            "name": "공사계약일반조건 (계약예규)",
            "url": "https://www.law.go.kr/%ED%96%89%EC%A0%95%EA%B7%9C%EC%B9%99/(%EA%B3%84%EC%95%BD%EC%98%88%EA%B7%9C)%EA%B3%B5%EC%82%AC%EA%B3%84%EC%95%BD%EC%9D%BC%EB%B0%98%EC%A1%B0%EA%B1%B4",
            "description": "계약/조달 관련 공문 서식 기준",
            "categories": ["proc"],
        },
        {
            "name": "공사입찰유의서 (계약예규)",
            "url": "https://www.law.go.kr/%ED%96%89%EC%A0%95%EA%B7%9C%EC%B9%99/(%EA%B3%84%EC%95%BD%EC%98%88%EA%B7%9C)%EA%B3%B5%EC%82%AC%EC%9E%85%EC%B0%B0%EC%9C%A0%EC%9D%98%EC%84%9C",
            "description": "입찰 공고 서식 기준",
            "categories": ["proc"],
        },
    ],
    "조달청": [
        {
            "name": "조달청 계약서식 안내",
            "url": "https://www.pps.go.kr/kor/content.do?key=00302",
            "description": "조달청 계약/정산 서식",
            "categories": ["proc"],
        },
    ],
    "서울정보소통광장": [
        {
            "name": "감사위원회 공문 실례",
            "url": "https://opengov.seoul.go.kr/sanction/15231440",
            "description": "감사결과통보 등 감사 관련 공문 실례",
            "categories": ["audit"],
        },
    ],
    "국민법제처 찾기쉬운생활법령": [
        {
            "name": "민원처리 통지 절차",
            "url": "https://easylaw.go.kr/CSP/CnpClsMain.laf?popMenu=ov&csmSeq=94&ccfNo=3&cciNo=2&cnpClsNo=3",
            "description": "민원회신 등 민원 처리 서식 기준",
            "categories": ["civil"],
        },
    ],
}


# ─── URL 유효성 검사 ───────────────────────────────────────────────────────────

def verify_url(url: str, timeout: int = 10) -> tuple[bool, str]:
    """URL이 접근 가능한지 확인. (True/False, 상태 메시지)"""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; GongmunDoctor/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.getcode()
            return (status == 200), f"HTTP {status}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except urllib.error.URLError as e:
        return False, f"URLError: {e.reason}"
    except Exception as e:
        return False, f"Error: {e}"


def verify_all_templates(template_dir: Path) -> dict[str, Any]:
    """모든 템플릿의 source_url 유효성 검사."""
    results: dict[str, Any] = {"ok": [], "fail": [], "total": 0}

    templates = sorted(template_dir.glob("*.json"))
    print(f"템플릿 {len(templates)}개 source_url 검증 중...")

    for path in templates:
        tmpl = json.loads(path.read_text(encoding="utf-8"))
        tid = tmpl.get("id", path.stem)
        url = tmpl.get("source_url", "")

        if not url:
            results["fail"].append({"id": tid, "url": "", "reason": "source_url 없음"})
            continue

        ok, msg = verify_url(url)
        entry = {"id": tid, "url": url, "status": msg}
        if ok:
            results["ok"].append(entry)
            print(f"  [OK] {tid}")
        else:
            results["fail"].append({**entry, "reason": msg})
            print(f"  [FAIL] {tid} -- {msg}")

        time.sleep(0.3)  # 서버 부하 방지

    results["total"] = len(templates)
    return results


# ─── 소스 접근성 검사 ─────────────────────────────────────────────────────────

def verify_sources() -> None:
    """SOURCES에 정의된 모든 URL 접근성 확인."""
    print("\n=== 수집 소스 접근성 검사 ===")
    for site, entries in SOURCES.items():
        print(f"\n[{site}]")
        for entry in entries:
            ok, msg = verify_url(entry["url"])
            status = "OK" if ok else "FAIL"
            print(f"  [{status}] {entry['name']} -- {msg}")
            time.sleep(0.3)


# ─── raw_templates index 저장 ────────────────────────────────────────────────

def save_raw_index(raw_dir: Path, template_dir: Path) -> None:
    """현재 templates/*.json 기반으로 raw_templates/index.json 갱신."""
    templates = []
    categories: dict[str, int] = {}

    for path in sorted(template_dir.glob("*.json")):
        tmpl = json.loads(path.read_text(encoding="utf-8"))
        templates.append({
            "id": tmpl.get("id"),
            "name": tmpl.get("name"),
            "category": tmpl.get("category"),
            "source": tmpl.get("source"),
            "source_url": tmpl.get("source_url"),
            "collected_date": tmpl.get("collected_date"),
        })
        cat = tmpl.get("category", "기타")
        categories[cat] = categories.get(cat, 0) + 1

    index = {
        "version": "1.0.0",
        "collected_date": "2026-03-23",
        "total": len(templates),
        "categories": categories,
        "sources": [
            {"name": e["name"], "url": e["url"]}
            for entries in SOURCES.values()
            for e in entries
        ],
        "templates": templates,
    }

    raw_dir.mkdir(parents=True, exist_ok=True)
    out = raw_dir / "index.json"
    out.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nraw_templates/index.json 갱신 완료 ({len(templates)}개)")


# ─── 메인 ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="공문 서식 수집 파이프라인")
    parser.add_argument("--verify", action="store_true", help="기존 template source_url 검증")
    parser.add_argument("--verify-sources", action="store_true", help="수집 소스 접근성 검사")
    parser.add_argument("--update-index", action="store_true", help="raw_templates/index.json 갱신")
    args = parser.parse_args()

    if args.verify:
        results = verify_all_templates(TEMPLATE_DIR)
        print(f"\n결과: {len(results['ok'])}개 OK / {len(results['fail'])}개 실패 / 총 {results['total']}개")
        if results["fail"]:
            print("\n실패 목록:")
            for f in results["fail"]:
                print(f"  - {f['id']}: {f.get('reason', '')}")
        sys.exit(0 if not results["fail"] else 1)

    if args.verify_sources:
        verify_sources()
        sys.exit(0)

    if args.update_index:
        save_raw_index(RAW_DIR, TEMPLATE_DIR)
        sys.exit(0)

    # 기본: 소스 검사 + index 갱신
    verify_sources()
    save_raw_index(RAW_DIR, TEMPLATE_DIR)


if __name__ == "__main__":
    main()
