# 클라이언트 연결 가이드

이 문서는 처음 사용하는 사람을 기준으로 씁니다. 목표는 간단합니다. 이 저장소를 설치하고, Codex 또는 Claude Code에서 실제 MCP 도구로 호출할 수 있게 만드는 것입니다.

## 1. 먼저 이해해야 할 것

이 저장소는 웹 서비스가 아닙니다. 브라우저에 URL을 넣는 방식이 아니라, **내 컴퓨터에서 실행되는 로컬 MCP 서버**입니다.

그래서 연결 흐름은 늘 같습니다.

1. 내 PC에 Python 환경을 준비한다.
2. 이 저장소를 설치한다.
3. MCP 클라이언트가 `python -m gongmun_doctor.mcp.server` 를 실행하도록 등록한다.
4. 클라이언트 안에서 자연어로 문서 교정을 요청한다.

이 구조를 이해하면, Codex든 Claude Code든 사실상 같은 문제를 다른 껍데기로 푸는 것뿐입니다.

## 2. 공통 준비

### 권장 Python 버전

- 권장: Python 3.12 또는 3.13
- 주의: Python 3.14는 `python-hwpx` 의존성 설치가 실패할 수 있음

### 설치 순서

저장소 루트에서 아래 순서로 진행하세요.

```bash
python -m pip install "mcp[cli]>=1.0,<2"
python -m pip install -e . --no-deps
```

설명:

- 첫 줄은 MCP 클라이언트 연동용 Python 패키지를 설치합니다.
- 두 번째 줄은 현재 저장소를 editable 모드로 등록합니다.
- `--no-deps` 를 쓴 이유는 문서 처리용 무거운 의존성이 별도 이슈를 일으킬 수 있기 때문입니다.

### 서버가 뜨는지 먼저 확인

```bash
python -m gongmun_doctor.mcp.server
```

아무 말 없이 대기 상태가 되면 정상입니다. 이 서버는 stdio 기반이라, 웹 서버처럼 포트를 띄우고 안내 문구를 크게 보여주지 않을 수 있습니다.

중단은 `Ctrl + C` 로 하면 됩니다.

## 3. Codex에서 연결하기

### 가장 쉬운 방법

로컬에서 실제로 확인한 Codex CLI 문법 기준으로는 아래 명령이 가장 간단합니다.

```bash
codex mcp add gongmun-doctor -- python -m gongmun_doctor.mcp.server
```

등록 확인:

```bash
codex mcp get gongmun-doctor
codex mcp list
```

### 잘 안 될 때

#### `python` 명령을 못 찾는 경우

실행 파일 전체 경로를 사용하세요.

```bash
codex mcp add gongmun-doctor -- C:\Path\To\python.exe -m gongmun_doctor.mcp.server
```

#### 설정 파일로 직접 넣고 싶은 경우

예시 조각은 [examples/codex-config.toml](../examples/codex-config.toml)에 넣어 두었습니다.

일반적으로는 `~/.codex/config.toml` 안의 `mcp_servers` 구역에 아래처럼 추가합니다.

```toml
[mcp_servers.gongmun-doctor]
command = "python"
args = ["-m", "gongmun_doctor.mcp.server"]
startup_timeout_sec = 20
```

이 방식은 여러 프로젝트에서 공용으로 쓰고 싶을 때 좋습니다. 반대로 “이 프로젝트에서만 쓸 것”이라면 `codex mcp add` 명령으로 등록하는 쪽이 더 부담이 적습니다.

### 연결 후 이렇게 말해보세요

- `D:\문서\착공보고.hwpx`를 먼저 dry run으로 검사해줘.
- `D:\문서\주간보고` 폴더 안 문서를 전부 교정해줘.
- 현재 교정 규칙 목록을 보여줘.

## 4. Claude Code에서 연결하기

Anthropic 공식 문서 기준으로 Claude Code는 로컬 stdio MCP 서버를 직접 등록할 수 있습니다.

### 방법 A: 개인용으로 빠르게 등록

```bash
claude mcp add --transport stdio gongmun-doctor -- python -m gongmun_doctor.mcp.server
```

확인:

```bash
claude mcp get gongmun-doctor
claude mcp list
```

Claude Code 세션 안에서는 `/mcp` 명령으로 연결 상태를 다시 볼 수 있습니다.

### 방법 B: 프로젝트 전체가 공유하도록 등록

팀이 같은 프로젝트에서 함께 쓸 것이라면 `.mcp.json` 을 프로젝트 루트에 두는 방식이 더 좋습니다.

예시 파일은 [examples/claude_code.mcp.json](../examples/claude_code.mcp.json)에 넣어 두었습니다.

내용은 아래와 같습니다.

```json
{
  "mcpServers": {
    "gongmun-doctor": {
      "command": "python",
      "args": ["-m", "gongmun_doctor.mcp.server"],
      "env": {}
    }
  }
}
```

이 파일을 프로젝트 루트에 `.mcp.json` 이름으로 두면 됩니다.

### 중요한 보안 포인트

Anthropic 공식 문서에 따르면 프로젝트 스코프의 `.mcp.json` 서버는 **처음 사용할 때 승인 절차**가 뜹니다. 이건 오류가 아니라 보안 설계입니다.

즉, “왜 한 번 더 물어보지?”가 아니라 “그래서 안심할 수 있구나”에 가깝습니다.

### Windows 사용자 팁

Anthropic 문서에는 Windows에서 `npx` 계열은 `cmd /c` 래퍼가 필요하다고 나옵니다. 하지만 이 저장소는 `python` 실행이라 보통 그 문제를 직접 맞지 않습니다. 그래도 `python` 이 PATH에 없으면 전체 경로를 적는 쪽이 더 안전합니다.

## 5. Claude Desktop에서 연결하기

여기는 조금 더 솔직하게 설명해야 합니다.

### 지금 Anthropic이 권장하는 방향

최근 Claude Desktop 공식 문서는 로컬 MCP를 **데스크톱 확장(.mcpb)** 형태로 다루는 쪽을 강하게 권장합니다. 즉, 장기적으로는 “설정 파일 수동 편집”보다 “확장 설치”가 표준이 될 가능성이 큽니다.

### 이 저장소의 현재 상태

이 저장소는 아직 `.mcpb` 패키지를 제공하지 않습니다. 대신 **개발자용 수동 stdio 연결 예시**를 제공합니다.

예시 파일:

- [examples/claude_desktop_config.json](../examples/claude_desktop_config.json)

예시 내용:

```json
{
  "mcpServers": {
    "gongmun-doctor": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "gongmun_doctor.mcp.server"],
      "env": {}
    }
  }
}
```

### 실무적으로 어떻게 이해하면 되나

- 지금 당장 안정적으로 쓰려면 Codex 또는 Claude Code가 1순위입니다.
- Claude Desktop은 “가능하지만 아직 패키징을 더 다듬으면 좋아질 대상”입니다.
- 나중에 배포성을 높이려면 `.mcpb` 확장으로 감싸는 2차 작업을 하면 됩니다.

### 상태 확인

Anthropic 지원 문서 기준으로 Claude Desktop에서는 채팅창 아래 `+` 버튼의 `Connectors` 화면이나 Developer settings에서 연결 상태와 로그를 확인할 수 있습니다.

## 6. 보안이 엄격한 환경에서의 추천 운영 방식

이 부분이 사실 가장 중요합니다.

### 추천 방식

- 로컬 stdio 서버만 사용
- 원격 MCP 서버는 나중에 검토
- `dry_run=True` 로 먼저 검사
- 보고서 파일은 꼭 필요할 때만 생성
- 전용 가상환경 또는 전용 Python 설치 사용

### 권장하지 않는 방식

- 클라우드 API 키를 섞어 시작하기
- 곧바로 폴더 전체에 쓰기 작업 걸기
- 공용 PC에서 사용자 범위 설정과 프로젝트 범위 설정을 뒤섞기

처음에는 기능을 넓히는 것보다, 실패했을 때 어디서 멈췄는지 바로 알 수 있는 구조가 더 중요합니다.

## 7. 초보자가 가장 먼저 해볼 시나리오

가장 안전한 첫 검증은 아래 순서입니다.

1. MCP 서버를 등록한다.
2. `dry_run` 으로 `.hwpx` 한 파일만 검사한다.
3. 결과를 대화에서 확인한다.
4. 괜찮으면 `report=True` 로 보고서까지 생성한다.
5. 마지막에만 실제 쓰기 교정을 진행한다.

이 순서를 따르면 “연결 문제”, “권한 문제”, “문서 처리 문제”를 한꺼번에 섞지 않고 분리해서 볼 수 있습니다.

## 8. 참고 자료

이 문서는 아래 자료를 바탕으로 작성했습니다.

- OpenAI Codex 관련 공식 자료: [OpenAI Developers](https://developers.openai.com/), [Unlocking the Codex harness](https://openai.com/index/unlocking-the-codex-harness/)
- Codex CLI 문법: 2026-04-03 기준 로컬에서 `codex mcp --help`, `codex mcp add --help` 로 직접 확인
- Claude Code MCP 공식 문서: [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp)
- Claude Code 설정 문서: [Claude Code settings](https://code.claude.com/docs/en/settings)
- Claude Desktop 로컬 MCP 문서: [Getting Started with Local MCP Servers on Claude Desktop](https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop)

## 9. 마지막 조언

처음 연결하는 사람은 자꾸 “무슨 기능이 더 있나?”를 묻게 됩니다. 하지만 실제로 중요한 질문은 그것이 아닙니다.

**이 도구가 내 환경의 제약을 존중하는가, 그 질문이 먼저입니다.**
