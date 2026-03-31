# 🏗️ 요양원 SEO 프로젝트: 멀티 에이전트 최적화 아키텍처 및 권한 명세

본 문서는 4대 하이브리드 AI 모델(Claude 4.6 Opus, Claude 4.6 Sonnet, Gemini 3.1 Pro, Haiku)이 충돌 없이 효율적으로 협업하기 위한 폴더 구조 및 접근 권한(Context/Write)을 정의합니다.

## 1. 최적화된 디렉토리 구조 (Directory Tree)

```text
nursing-home-seo/
├── CLAUDE.md                 # [NEW/핵심] 최상단 위치. Claude CLI가 자동 인식하는 전역 행동 지침 (dangerouslySetInnerHTML 금지 등)
├── .ai/                      # AI 작업 이력 및 컨텍스트 통제소
│   └── handoff/              # PM이 작성한 에이전트 간 작업 인수인계 기록 (예: m1_handoff.md)
│
├── docs/                     # 📚 기획 및 아키텍처 (Master Documents) -> 주 담당: [Claude 4.6 Opus]
│   ├── plan-v3.md            # 전체 마스터 기획서 (Reviewer의 기준점)
│   ├── api_spec.md           # 공공데이터포털 API 명세
│   └── schema_design.md      # DB 및 JSON 스키마 설계도
│
├── src/                      # 🛠️ 소스 코드 (Maker의 주 작업 공간)
│   ├── pipeline/             # Data Engineer 영역 (Python) -> 주 담당: [Claude 4.6 Sonnet]
│   │   ├── schemas/          # (중요) seo_content_schema.json ([Gemini 3.1 Pro]가 수시로 검증할 파일)
│   │   ├── step1_load_xlsx.py
│   │   └── ...
│   │
│   └── frontend/             # Frontend Dev 영역 (Next.js App Router) -> 주 담당: [Claude 4.6 Sonnet]
│       ├── app/
│       ├── components/       # SeoContent.tsx 등 (CLAUDE.md의 보안 규칙이 집중 적용되는 곳)
│       └── types/            # (중요) pipeline/schemas 와 동기화되어야 할 TS 타입들
│
├── supabase/migrations/      # 🗄️ 인프라 및 DB 보안 (SQL) -> 주 담당: [Haiku]
│
└── .github/workflows/        # ⚙️ CI/CD 파이프라인 -> 주 담당: [Haiku]


2. 에이전트별 접근 권한 및 컨텍스트 매트릭스 (Access & Context Rules)
우리의 방식은 인간 PM이 중간에서 통제하는 **'반자율주행(Human-in-the-loop)'**입니다. 각 에이전트에게 주입할 컨텍스트와 권한을 엄격히 통제하여 비용(토큰)을 아끼고 품질을 올립니다.

🧠 Agent A: Claude 4.6 Opus (Chief Architect / 문서 및 설계)
역할: 프로젝트의 뼈대를 잡고 복잡한 아키텍처 설계와 기획서를 작성하는 수석 설계자.

물리적 권한: docs/ 폴더 내의 마크다운 문서 작성 및 수정.

접근 통제: 초기 기획, 스키마 설계, 방향성 조정 등 고도의 추론이 필요한 작업에만 투입하여 비용(토큰) 낭비를 막음. CLAUDE.md의 규칙을 기반으로 문서를 작성함.

🤖 Agent B: Claude 4.6 Sonnet (Maker / 터미널 CLI)
역할: 코드를 실제로 타이핑하고 파일을 생성/수정하는 메인 일꾼 (Data / Frontend).

물리적 권한: 전역 쓰기 권한(Global Write Access)을 가짐. (단, PM의 지시가 있을 때만 실행)

접근 통제 (PM의 프롬프팅 가이드):

[Read-Only] docs/ 폴더: 기획서를 읽고 참고만 할 것. 절대 기획서를 임의로 수정하지 말 것.

[Write-Allowed] src/: 코드를 작성하고 수정하는 주 무대.

[Mandatory Context] 터미널에서 실행될 때 프로젝트 최상단의 CLAUDE.md를 자동으로 읽어 보안 규칙과 코딩 컨벤션을 뼈에 새기고 시작함.

명령 예시: claude -p "너는 프론트엔드 개발자야. src/frontend/components/SeoContent.tsx 파일을 만들어." (규칙은 CLAUDE.md가 알아서 주입)

🕵️‍♂️ Agent C: Gemini 3.1 Pro (Reviewer & QA / Continue 사이드바)
역할: Maker(Sonnet)가 짠 코드를 기획서 및 보안 규칙에 비추어 교차 검증하는 감사관.

물리적 권한: 읽기 전용(Read-Only). 코드를 직접 덮어쓰지 않고, 문제점과 수정된 코드 스니펫만 PM에게 제안함.

접근 통제 (PM의 프롬프팅 가이드):

[Mandatory Context - Architecture] DB나 API 관련 검증 시 항상 @docs/plan-v3.md와 @docs/schema_design.md를 첨부하여 기준점을 잡아줄 것.

[Mandatory Context - Security] 컴포넌트 검증 시 항상 @CLAUDE.md를 첨부하여 XSS 방어가 제대로 되었는지 깐깐하게 물어볼 것.

[Cross-Check] 프론트엔드 타입을 검증할 때 파이프라인의 스키마 파일(@src/pipeline/schemas/seo_content_schema.json)과 프론트엔드의 타입 파일(@src/frontend/types/seo-content.ts)을 동시에 첨부하여 구조 불일치를 잡아낼 것.

⚡ Agent D: Haiku (DevOps / 단순 스크립트 및 로그)
역할: 속도가 빠르고 비용이 매우 저렴한 특성을 살려, 단순 반복 작업이나 인프라 설정 파일을 작성하는 보조 일꾼.

물리적 권한: supabase/migrations/, .github/workflows/ 폴더 쓰기 권한 및 에러 로그 분석.

접근 통제: 복잡한 비즈니스 로직(src/) 컨텍스트 주입 없이, 뻔한 SQL 테이블 생성이나 GitHub Actions YAML 설정 등에 가볍게 투입. 최상단 CLAUDE.md의 기본 컨벤션을 준수함.

3. 💡 PM을 위한 효율성 극대화 워크플로우 (요약)
설계 및 지시: PM이 docs/plan-v3.md (Opus 4.6 작성)를 보고 터미널의 **Claude 4.6 Sonnet (Maker)**에게 주요 로직 작업 지시. (최상단 CLAUDE.md가 자동 적용됨)

작업 수행: Sonnet과 Haiku가 각각의 담당 구역(src/ 또는 supabase/) 내부에 파일을 생성/수정함.

검증 요청: PM이 Continue 창에서 변경된 src/ 파일과 기준이 되는 docs/ 파일, 그리고 @CLAUDE.md를 첨부하여 **Gemini 3.1 Pro (Reviewer)**에게 검토 지시.

피드백 적용: Gemini가 문제점을 발견하면, PM은 그 내용을 복사하여 다시 터미널의 Sonnet에게 "Gemini가 이 부분 보안 취약하대. 수정해" 라고 전달(Handoff).