# GongMun Doctor MCP

**AI가 공문서를 로컬에서 안전하게 교정합니다**
**AI-powered Korean official document proofreading -- 100% local, no cloud required**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green.svg)](https://python.org)
[![MCP](https://img.shields.io/badge/MCP-1.0-orange.svg)](https://modelcontextprotocol.io)

---

## 소개 | Introduction

GongMun Doctor MCP는 한국 공문서(.hwpx/.hwp)를 **로컬 PC에서** 자동 교정하는 MCP 서버입니다. Claude, Codex 등 AI 에이전트에게 "이 문서 교정해줘"라고 말하면, 파일이 외부로 나가지 않고 내 PC 안에서 교정이 완료됩니다.

GongMun Doctor MCP is a local MCP server that proofreads Korean official documents (.hwpx/.hwp) entirely on your PC. When you ask an AI agent like Claude or Codex to "proofread this document," the file never leaves your machine.

> **보안 원칙 | Security First**: 문서는 밖으로 나가지 않습니다. 네트워크 호출 없음. 클라우드 API 키 불필요.
> Documents stay local. No network calls. No cloud API keys needed.

---

## 이런 분들에게 유용합니다 | Who Is This For?

| 대상 | 활용 예시 |
|------|----------|
| **공무원** | 기안 작성 후 맞춤법/공문서체 자동 교정, 보고 전 최종 검수 |
| **공공기관 직원** | 업무협조 요청, 민원회신 등 공문 템플릿 자동 생성 |
| **행정사/법무사** | 대량 문서 일괄 교정, 교정 보고서 자동 생성 |
| **공문 작성이 처음인 분** | 50종 행정문서 템플릿으로 올바른 양식 학습 |

| Who | Use Case |
|-----|----------|
| **Government officials** | Auto-proofread drafts before submission |
| **Public institution staff** | Generate official document templates (cooperation requests, civil responses, etc.) |
| **Administrative professionals** | Batch-correct large volumes of documents with reports |
| **Beginners** | Learn proper official document formatting with 50 built-in templates |

---

## 주요 기능 | Key Features

### 3단계 교정 규칙 | 3-Layer Correction Rules

| 레이어 Layer | 내용 Description | 예시 Example |
|-------------|-----------------|-------------|
| **L1 맞춤법** | 띄어쓰기, 맞춤법 교정 | "시행알림" -> "시행 알림" |
| **L2 문법** | 조사 오류, 병기 제거 | "을/를" -> "을" (공문서는 조사 병기 금지) |
| **L3 공문서체** | 행정업무운영편람 기준 서식 교정 | "관련하여," -> "관련하여" (접속표현 뒤 쉼표 생략) |

### 10개 MCP 도구 | 10 MCP Tools

| # | 도구 Tool | 설명 Description |
|---|-----------|-----------------|
| 1 | `correct_document` | 단일 문서 교정 / Correct one document |
| 2 | `correct_documents_in_folder` | 폴더 내 문서 일괄 교정 / Batch correct all documents in a folder |
| 3 | `list_rules` | 교정 규칙 목록 조회 / List correction rules |
| 4 | `get_correction_report` | 교정 보고서 조회 / Read correction report |
| 5 | `preview_text_corrections` | 텍스트 교정 미리보기 / Preview corrections without touching files |
| 6 | `list_document_templates` | 행정문서 템플릿 목록 / List document templates |
| 7 | `match_document_templates` | 키워드로 템플릿 검색 / Search templates by keyword |
| 8 | `get_template_variables` | 템플릿 입력 변수 조회 / Show required template variables |
| 9 | `render_document_template` | 템플릿 렌더링 (문서 생성) / Render template with values |
| 10 | `get_server_info` | 서버 정보 조회 / Server info |

### 50종 행정문서 템플릿 | 50 Administrative Templates

6개 분야에 걸쳐 실무에서 바로 쓸 수 있는 템플릿을 제공합니다:

| 분야 Category | 템플릿 수 | 예시 Examples |
|--------------|---------|-------------|
| **일반행정** (gen) | 15종 | 업무협조요청, 알림통보, 회신, 업무보고, 자료요청, 회의개최알림 등 |
| **감사** (audit) | 5종 | 감사결과통보, 시정조치요구, 지도점검알림 등 |
| **민원** (civil) | 5종 | 민원회신, 처리기간연장통보, 이첩통보, 질의회신 등 |
| **건설공사** (con) | 10종 | 착공알림, 준공알림, 설계변경요청, 하자보수통보 등 |
| **인사** (hr) | 5종 | 출장결과보고, 휴가사용보고, 겸직허가신청, 직위해제통보 등 |
| **계약조달** (proc) | 10종 | 입찰공고, 낙찰자결정통보, 계약체결요청, 보조금교부신청 등 |

---

## 빠른 시작 가이드 | Quick Start Guide

### 1단계: 설치 | Step 1: Install

> Python **3.12 또는 3.13**을 권장합니다. 3.14에서는 `lxml` 빌드 문제가 발생할 수 있습니다.
> Python **3.12 or 3.13** recommended. 3.14 may have `lxml` build issues.

```bash
# 저장소 클론 | Clone the repository
git clone https://github.com/sinmb79/GongMun-Doctor-MCP.git
cd GongMun-Doctor-MCP

# MCP 라이브러리 설치 | Install MCP library
python -m pip install "mcp[cli]>=1.0,<2"

# GongMun Doctor 설치 (개발 모드) | Install in dev mode
python -m pip install -e . --no-deps
```

### 2단계: 서버 실행 확인 | Step 2: Verify Server

```bash
# 서버 직접 실행 | Run server directly
python -m gongmun_doctor.mcp.server

# MCP Inspector로 도구 목록 확인 (선택) | Inspect tools visually (optional)
npx -y @modelcontextprotocol/inspector python -m gongmun_doctor.mcp.server
```

### 3단계: AI 클라이언트 연결 | Step 3: Connect Your AI Client

#### Codex (가장 간단 | Simplest)

```bash
codex mcp add gongmun-doctor -- python -m gongmun_doctor.mcp.server
```

확인:
```bash
codex mcp list
```

#### Claude Code

```bash
claude mcp add --transport stdio gongmun-doctor -- python -m gongmun_doctor.mcp.server
```

프로젝트 단위로 설정하려면 `.mcp.json`을 사용하세요. 자세한 내용은 [docs/client-setup-ko.md](docs/client-setup-ko.md)를 참고하세요.

#### Claude Desktop

수동 stdio 연결 예시는 [examples/claude_desktop_config.json](examples/claude_desktop_config.json)을 참고하세요.

---

## 실전 사용 예시 | Real-World Usage Examples

AI 에이전트에 연결한 후, 자연어로 요청하면 됩니다. 도구 이름을 외울 필요가 없습니다.

After connecting to your AI agent, just ask in natural language. No need to memorize tool names.

### 예시 1: 단일 문서 교정 | Example 1: Correct One Document

**이렇게 말하세요 | Say this:**
```
D:\문서\공문.hwpx를 dry_run으로 먼저 검사해줘
```

**AI가 수행하는 작업 | What happens:**

`correct_document(file_path="D:\\문서\\공문.hwpx", dry_run=True)` 호출

```json
{
  "status": "dry_run_complete",
  "file_path": "D:\\문서\\공문.hwpx",
  "corrections": [
    {"rule": "SP-001", "layer": "L1_spelling", "before": "시행알림", "after": "시행 알림"},
    {"rule": "GR-001", "layer": "L2_grammar", "before": "을/를", "after": "을"},
    {"rule": "OS-002", "layer": "L3_official_style", "before": "관련 :", "after": "관련:"}
  ],
  "total_corrections": 3
}
```

교정 내용을 확인한 뒤 실제 적용:
```
확인했어. 실제로 교정해줘.
```

### 예시 2: 폴더 일괄 교정 | Example 2: Batch Correct a Folder

```
D:\문서\주간보고 폴더 안의 .hwpx를 전부 교정하고 보고서도 만들어줘
```

`correct_documents_in_folder(folder_path="D:\\문서\\주간보고", report=True)` 호출 -- 폴더 내 모든 .hwpx 파일을 교정하고 각각의 교정 보고서(Markdown)를 생성합니다.

### 예시 3: 교정 규칙 확인 | Example 3: Check Rules

```
맞춤법 레이어 규칙만 보여줘
```

`list_rules(layer="L1_spelling")` 호출:

```json
[
  {"id": "SP-001", "search": "시행알림", "replace": "시행 알림", "desc": "합성어가 아닌 경우 띄어쓰기"},
  {"id": "SP-002", "search": "참고 하시기", "replace": "참고하시기", "desc": "'참고하다'는 한 단어이므로 붙여 씀"},
  {"id": "SP-003", "search": "보수 공사", "replace": "보수공사", "desc": "'보수공사'는 한 단어이므로 붙여 씀"}
]
```

### 예시 4: 공문 템플릿으로 문서 작성 | Example 4: Generate Document from Template

```
업무 협조 요청 공문을 만들어줘
```

AI가 자동으로 적절한 템플릿을 찾고, 필요한 정보를 물어본 뒤 문서를 생성합니다:

```
수신기관: ○○시 도시건설국장
제목: 도시계획 변경 관련 업무 협조 요청
관련문서: 도시계획과-1234(2026.03.10.)
협조사항: 도시계획 변경안 검토
기한: 2026. 4. 10.
```

**생성 결과 | Output:**

```
수신 ○○시 도시건설국장
(경유)
제목 도시계획 변경 관련 업무 협조 요청

1. 관련: 도시계획과-1234(2026.03.10.)

2. 위 호와 관련하여 도시계획 변경안 검토에 대한 귀 기관의
   적극적인 협조를 요청합니다.

3. 협조 요청 사항은 다음과 같습니다.
   가. 협조 내용: 도시계획 변경안 검토
   나. 회신 기한: 2026. 4. 10.까지
   다. 담당자: 도시계획과 담당자 홍길동

붙임 협조 요청 자료 1부.  끝.
```

### 예시 5: 텍스트 미리보기 | Example 5: Preview Text Corrections

```
"관련하여, 을/를 첨부 합니다" 이 문장 교정해줘
```

`preview_text_corrections(text="관련하여, 을/를 첨부 합니다")` 호출 -- 파일 없이 텍스트만으로 교정 결과를 미리 확인할 수 있습니다.

---

## 프로젝트 구조 | Project Structure

```
GongMun-Doctor-MCP/
|-- src/gongmun_doctor/
|   |-- mcp/                   # MCP 서버 | MCP server
|   |   |-- server.py           #   서버 정의 (10개 도구)
|   |   |-- services.py         #   비즈니스 로직
|   |   +-- models.py           #   데이터 모델
|   |-- rules/                  # 교정 규칙 | Correction rules
|   |   |-- L1_spelling.json    #   맞춤법/띄어쓰기
|   |   |-- L2_grammar.json     #   문법 (조사 오류 등)
|   |   +-- L3_official_style.json  #   공문서체
|   |-- agents/administrative/  # 행정문서 템플릿 | Templates
|   |   +-- templates/          #   50종 JSON 템플릿
|   |-- parser/                 # HWPX/HWP 파서 | Document parser
|   |-- engine.py               # 교정 엔진 | Correction engine
|   +-- report/                 # 보고서 생성 | Report generator
|-- docs/                       # 설정 가이드 | Setup guides
|-- examples/                   # 클라이언트 설정 예시 | Client config examples
+-- tests/                      # 테스트 | Tests
```

---

## 자주 묻는 질문 | FAQ

### 서버는 뜨는데 문서 교정이 안 돼요

MCP 서버 실행과 문서 교정은 별개입니다. 실제 `.hwpx` 문서 교정에는 `python-hwpx` 런타임이 필요합니다:

```bash
python -m pip install "python-hwpx>=2.8.0"
```

### Windows에서 명령어를 못 찾아요

`python`, `codex`, `claude` 명령이 PATH에 없는 경우입니다. 전체 경로를 사용하세요:

```bash
# 예시: Python 전체 경로
C:\Users\사용자\AppData\Local\Programs\Python\Python312\python.exe -m gongmun_doctor.mcp.server
```

### Claude Code에서 승인 팝업이 떠요

정상 동작입니다. `.mcp.json` 기반 프로젝트 서버는 처음 사용 시 승인 과정을 거칩니다.

### Claude Desktop에서 연결이 안 돼요

현재 주력 지원 대상은 Codex와 Claude Code입니다. Claude Desktop은 수동 stdio 연결로 가능하지만 환경에 따라 차이가 있을 수 있습니다.

---

## 테스트 실행 | Running Tests

```bash
pytest tests -q
```

실제 HWPX 파일이 필요한 통합 테스트는 별도 마커로 관리합니다:

```bash
# 통합 테스트 제외 | Skip integration tests
pytest tests -q -m "not integration"
```

---

## 보안 설계 원칙 | Security Design Principles

| 원칙 Principle | 설명 Description |
|---------------|-----------------|
| **로컬 우선** | 모든 파일 처리는 사용자 PC 내에서 완료 |
| **네트워크 없음** | 기본 동작에 네트워크 호출 없음 |
| **API 키 불필요** | 클라우드 API 키 없이 시작 가능 |
| **경계 명확** | 로컬 처리와 외부 통신의 경계를 명확히 구분 |

> 클라우드 LLM 분석, 한글 COM 자동조작 등 확장 기능은 선택적(opt-in)이며 기본 범위에 포함되지 않습니다.
> Cloud LLM analysis and HWP COM automation are opt-in extensions, not included in the default scope.

---

## 참고 문서 | References

- [클라이언트 연결 가이드 (한글)](docs/client-setup-ko.md)
- [MCP 준비 메모](docs/mcp-preparation.md)
- [Claude Desktop 설정 예시](examples/claude_desktop_config.json)
- [Claude Code .mcp.json 예시](examples/claude_code.mcp.json)
- [Codex 설정 예시](examples/codex-config.toml)

---

## 라이선스 | License

MIT License -- 자유롭게 사용, 수정, 배포할 수 있습니다.

MIT License -- Free to use, modify, and distribute.

---

## 만든 사람 | Author

**22B Labs** (sinmb79) -- The 4th Path

문의사항이나 기여는 [Issues](https://github.com/sinmb79/GongMun-Doctor-MCP/issues)를 이용해 주세요.

For questions or contributions, please use [Issues](https://github.com/sinmb79/GongMun-Doctor-MCP/issues).
