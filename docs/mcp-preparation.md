# Gongmun Doctor MCP 준비 메모

이 문서는 구현지시서가 들어오기 전, 현재 저장소를 MCP로 옮기기 위한 기준선을 정리한 문서다.

## 왜 지금 MCP인가

현재 프로젝트는 이미 핵심 도메인이 분리돼 있다.

- 규칙 기반 교정 코어: `engine.py`
- 규칙 카탈로그: `rules/`
- 템플릿 매칭/렌더링: `agents/administrative/template_engine.py`
- 파일/앱 연동: CLI, GUI, HWP COM, clipboard

즉, 문제는 기능이 없는 게 아니라 기능 표면이 CLI와 Windows 연동에 묶여 있다는 점이다. MCP 전환의 핵심은 새 기능을 만드는 것이 아니라, 기존 기능을 LLM이 호출 가능한 도구 표면으로 재배치하는 것이다.

## 1차 범위

구현지시서가 오기 전까지는 다음만 MCP로 여는 것이 안전하다.

- 로컬 문서 교정
- 규칙 목록 조회
- 교정 보고서 조회
- 일반 텍스트 교정 미리보기
- 행정 템플릿 목록 조회
- 템플릿 매칭
- 템플릿 변수 조회
- 템플릿 렌더링

파일 교정까지 1차에 포함하되, 범위는 `로컬 파일 경로 기반 교정`까지만 연다. Windows COM, clipboard, cloud API는 계속 분리한다.

## 1차에서 의도적으로 미루는 것

- 한글 COM 자동 조작
- 트레이 앱 / 전역 단축키 / 클립보드 감시
- 클라우드 LLM 기반 문장 조화 분석

이 부분들은 도구 설계보다 권한, 로컬 환경, 실패 복구, 사용자 확인 흐름이 더 중요하다. 구현지시서 없이 먼저 만들면 API보다 사고가 먼저 난다.

## 권장 배포 경로

현재 프로젝트 성격상 1차는 로컬 `stdio` 서버가 가장 자연스럽다.

- 이유 1: HWP/HWPX와 Windows 앱 연동은 사용자 PC 맥락을 강하게 탄다.
- 이유 2: 원격 HTTP 서버로 가면 로컬 파일 접근과 COM 제어를 다시 우회 설계해야 한다.
- 이유 3: 보안이 엄격한 환경일수록 API 키, 외부 업로드, 원격 실행보다 로컬 stdio가 감사와 통제가 쉽다.

원격 배포는 2차 이후에 다시 판단한다. 그 시점에는 텍스트/템플릿 계층만 별도 서버로 분리하고, 로컬 전용 기능은 별도 MCP 또는 MCPB 번들로 나누는 편이 더 깔끔하다.

## 이번 준비 작업에 포함된 것

- `.[mcp]` optional dependency 추가
- `gongmun-doctor-mcp` 엔트리포인트 추가
- `src/gongmun_doctor/mcp/` 패키지 생성
- 기존 코어를 MCP 친화적 구조화 출력으로 감싼 서비스 레이어 추가
- 로컬 파일 교정 tool 추가
- sidecar Markdown 보고서 조회 tool 추가
- 로컬 `stdio` MCP 서버 스캐폴드 추가
- 최소 스모크 테스트 추가

## 현재 노출된 MCP 도구

- `get_server_info`
- `correct_document`
- `correct_documents_in_folder`
- `list_rules`
- `get_correction_report`
- `preview_text_corrections`
- `list_document_templates`
- `match_document_templates`
- `get_template_variables`
- `render_document_template`

## 구현지시서가 오면 바로 결정해야 할 것

- 최종 사용 클라이언트: Claude Desktop, Claude Code, ChatGPT, Codex, 자체 앱 중 무엇인지
- 파일 기반 교정을 1차에 넣을지, 텍스트 교정만 먼저 갈지
- 출력 형식: 단순 텍스트, 구조화 JSON, Markdown 보고서 중 우선순위
- 쓰기 동작 전 사용자 확인이 필요한지
- 로컬 전용 MCP 하나로 갈지, 로컬/원격 서버를 분리할지
- 클라우드 LLM 사용 시 마스킹 범위를 그대로 유지할지 확장할지

## 로컬 실행 메모

현재 확인된 환경 이슈:

- Python 3.14 환경에서는 `python-hwpx -> lxml` 빌드가 실패할 수 있다.
- 따라서 HWPX 포함 전체 설치 검증은 당분간 Python 3.12 또는 3.13 기준으로 보는 편이 안전하다.
- 이번 MCP 준비 작업은 텍스트/템플릿 계층을 먼저 분리해, HWPX 런타임이 없어도 기본 MCP 표면을 개발할 수 있게 했다.

보안 디폴트:

- MCP 서버는 로컬 파일 경로만 받는다.
- 기본 tool은 네트워크 호출을 하지 않는다.
- 클라우드 LLM / 외부 API 키는 요구하지 않는다.
- 보고서 파일은 요청 시에만 `.md` sidecar로 저장한다.

설치:

```bash
pip install -e ".[mcp]"
```

서버 실행:

```bash
gongmun-doctor-mcp
```

또는:

```bash
python -m gongmun_doctor.mcp.server
```

MCP Inspector로 점검:

```bash
npx -y @modelcontextprotocol/inspector gongmun-doctor-mcp
```

스크립트 경로가 잡히지 않으면:

```bash
npx -y @modelcontextprotocol/inspector python -m gongmun_doctor.mcp.server
```

## 다음 구현 순서 제안

1. `correct_document`의 반환 형식을 기준으로 대화형 UX를 고정한다.
2. 그 다음 폴더 단위 배치 교정 tool 여부를 결정한다.
3. 그 다음 한글 COM / clipboard처럼 부작용이 큰 도구를 별도 권한 레이어로 분리한다.
4. 마지막에 원격 배포 여부를 판단한다.

MCP 전환의 진짜 일은 서버를 띄우는 게 아니라, 무엇을 아직 도구로 만들지 말아야 하는지 구분하는 일이다.
