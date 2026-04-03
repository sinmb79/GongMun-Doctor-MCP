# 왜 이 저장소가 필요한가

Meta description: 민감한 공문을 외부 업로드 없이 로컬에서 교정하도록 돕는 GongMun Doctor MCP 서버.

Labels: mcp, gongmun-doctor, hwpx, 보안, 로컬우선, codex, claude-code

22B Labs · The 4th Path · GitHub: sinmb79

대부분의 문서 자동화 도구는 편리하지만, 보안이 엄격한 환경에서는 그 편리함이 곧 위험이 됩니다. 파일을 외부로 보내야 하거나, API 키를 별도로 다뤄야 하거나, 사용자가 직접 스크립트를 짜야 한다면 실제 현장에서는 오래 못 갑니다. 이 저장소는 그 불편한 현실에서 출발합니다.

`GongMun Doctor MCP`는 기존 GongMun Doctor의 규칙 기반 공문 교정 엔진을 **로컬 MCP 서버**로 감싼 프로젝트입니다. 그래서 Codex, Claude Code 같은 에이전트형 도구가 “이 문서 교정해줘”라고 자연어로 요청받아도, 실제 교정은 사용자의 PC 안에서 처리할 수 있습니다.

핵심은 화려함이 아니라 경계입니다. 문서는 밖으로 나가지 않고, 기본 도구는 네트워크를 호출하지 않으며, 클라우드 API 키 없이도 시작할 수 있습니다.

## ⚡ 30초 요약

- 이 저장소는 공문 교정 엔진을 MCP 도구로 바꿉니다.
- 기본 동작은 `로컬 파일 경로만`, `네트워크 호출 없음`, `API 키 불필요`입니다.
- Codex, Claude Code, Claude Desktop에서 붙여 쓸 수 있도록 준비했습니다.
- 한 파일 교정, 폴더 일괄 교정, 규칙 조회, 보고서 읽기까지 바로 가능합니다.
- 클라우드 LLM 분석이나 한글 COM 자동조작은 일부러 기본 범위에서 뺐습니다.

개발자가 아니어도 이해해야 하는 요점은 하나입니다. 이 프로젝트는 “AI가 공문을 대신 읽어주는 것”보다 “민감한 문서를 안전하게 다루는 것”을 먼저 설계했습니다.

## 🔒 왜 로컬 MCP가 중요한가

보안이 엄격한 조직에서 문제는 기술이 부족해서가 아니라, 기술이 조직의 제약을 무시해서 생깁니다.

- CLI만 있으면 사용자는 명령어를 직접 기억해야 합니다.
- GUI만 있으면 다른 에이전트와 연결이 약합니다.
- 클라우드 API에 기대면 승인, 키 관리, 반출 우려가 늘어납니다.

로컬 MCP는 이 셋 사이의 절충점입니다.

- 사용자는 자연어로 요청합니다.
- 에이전트는 도구를 구조적으로 호출합니다.
- 실제 파일 처리는 로컬에서 끝납니다.

즉, 편의성은 올리되 반출 경로는 늘리지 않는 방향입니다.

## 🧰 지금 바로 되는 것

현재 제공하는 MCP 도구는 아래와 같습니다.

- `correct_document(file_path, dry_run=False, report=False)`
- `correct_documents_in_folder(folder_path, dry_run=False, report=False, recursive=False)`
- `list_rules(layer=None)`
- `get_correction_report(file_path)`
- `preview_text_corrections(text, layers=None)`
- `list_document_templates(category=None)`
- `match_document_templates(query)`
- `get_template_variables(template_id)`
- `render_document_template(template_id, values)`

실무적으로 보면 중요한 도구는 앞의 네 개입니다. 나머지는 템플릿 자동화와 설명 보강용입니다.

## 🚀 처음 시작하는 사람을 위한 가장 쉬운 순서

먼저 Python 3.12 또는 3.13 환경을 권장합니다. Python 3.14에서는 `python-hwpx` 계열 설치가 `lxml` 빌드 문제로 막힐 수 있습니다.

그 다음 PowerShell에서 이 저장소 루트로 이동한 뒤:

```bash
python -m pip install "mcp[cli]>=1.0,<2"
python -m pip install -e . --no-deps
```

여기까지 되면 MCP 서버 자체는 뜰 수 있습니다.

서버를 직접 확인하려면:

```bash
python -m gongmun_doctor.mcp.server
```

도구 목록을 눈으로 보고 싶다면:

```bash
npx -y @modelcontextprotocol/inspector python -m gongmun_doctor.mcp.server
```

이 단계가 중요한 이유는 “설치가 되었는가”와 “클라이언트가 붙을 준비가 되었는가”가 다르기 때문입니다. MCP는 실행보다 연결에서 더 자주 막힙니다.

## 🖥️ 어떤 클라이언트에서 쓸 수 있나

### Codex

가장 단순합니다. 로컬에서 확인한 CLI 문법 기준으로 아래 명령으로 등록하면 됩니다.

```bash
codex mcp add gongmun-doctor -- python -m gongmun_doctor.mcp.server
```

등록 확인:

```bash
codex mcp get gongmun-doctor
codex mcp list
```

### Claude Code

개인용으로 붙일 때는:

```bash
claude mcp add --transport stdio gongmun-doctor -- python -m gongmun_doctor.mcp.server
```

프로젝트 전체가 함께 쓰게 하려면 `.mcp.json` 기반 프로젝트 스코프를 쓰는 편이 좋습니다. 자세한 단계는 [docs/client-setup-ko.md](docs/client-setup-ko.md)에 정리해 두었습니다.

### Claude Desktop

현재 Anthropic은 로컬 MCP를 **데스크톱 확장(.mcpb)** 흐름으로 더 강하게 밀고 있습니다. 이 저장소는 아직 `.mcpb` 패키지까지 만들지는 않았고, 대신 수동 stdio 연결 예시를 제공합니다.

즉, 지금은 “개발자용 수동 연결” 단계이고, 나중에 필요하면 “한 번 클릭 설치용 데스크톱 확장” 단계로 가면 됩니다.

## ✅ 실제로 이렇게 쓰면 된다

한 파일만 먼저 안전하게 보고 싶을 때:

- “`D:\문서\공문.hwpx`를 `dry_run`으로 먼저 검사해줘.”

한 폴더를 한 번에 돌리고 싶을 때:

- “`D:\문서\주간보고` 폴더 안의 `.hwpx`를 전부 교정해줘.”

규칙부터 확인하고 싶을 때:

- “현재 맞춤법 레이어 규칙만 보여줘.”

보고서를 다시 읽고 싶을 때:

- “방금 생성한 교정 보고서를 다시 열어 보여줘.”

좋은 MCP는 사용자가 도구 이름을 외우게 하지 않습니다. 사용자는 의도를 말하고, 에이전트가 적절한 도구를 고르는 쪽이 맞습니다.

## 🛠️ 자주 막히는 지점

### 1. Python은 있는데 문서 교정이 안 될 때

MCP 서버는 떠도, 실제 `.hwpx` 문서 교정에는 `python-hwpx` 런타임이 필요합니다. 그래서 “서버 실행 성공”과 “문서 교정 성공”은 별개입니다.

### 2. Windows에서 실행 파일을 못 찾을 때

`python`, `codex`, `claude` 명령이 PATH에 없으면 전체가 멈춥니다. 이런 경우에는 실행 파일의 전체 경로를 써야 합니다.

### 3. Claude Code에서 프로젝트 서버 승인이 뜰 때

이건 오류가 아니라 정상 동작입니다. 프로젝트의 `.mcp.json` 서버는 처음 사용할 때 승인 과정을 거치는 것이 맞습니다.

### 4. Claude Desktop에서 바로 안 붙을 때

현재 공식 방향은 데스크톱 확장 쪽이므로, 수동 설정 방식은 환경마다 차이가 있을 수 있습니다. 그래서 이 저장소에서는 Claude Desktop을 “가능한 대상”으로 두되, 주력 연결 대상은 Codex와 Claude Code로 잡고 있습니다.

## 📚 처음 사용자용 상세 안내

처음부터 끝까지 따라가는 자세한 설명은 아래 문서에 정리했습니다.

- [클라이언트 연결 가이드 (한글)](docs/client-setup-ko.md)
- [MCP 준비 메모](docs/mcp-preparation.md)
- [Claude Desktop 예시 설정](examples/claude_desktop_config.json)
- [Claude Code 예시 `.mcp.json`](examples/claude_code.mcp.json)
- [Codex 예시 TOML 조각](examples/codex-config.toml)

## 🔎 참고 문서

이 저장소의 연결 설명은 아래 자료를 바탕으로 정리했습니다.

- Claude Code MCP 문서
- Claude Code 설정 문서
- Claude Desktop 로컬 MCP 시작 문서
- OpenAI Codex 관련 공식 자료와 로컬 `codex mcp --help` 확인 결과

최신 링크는 아래 상세 가이드 문서에 함께 적어 두었습니다.

## 🌱 만드는 철학

좋은 자동화는 사람을 압도하지 않습니다. 처음 쓰는 사람도 이해할 수 있어야 하고, 보안팀이 봐도 설명 가능해야 하며, 문제가 생겼을 때 어디까지가 로컬이고 어디서부터가 외부인지 바로 말할 수 있어야 합니다.

도구가 똑똑한 것보다, 경계가 정직한 것이 더 오래 갑니다.
