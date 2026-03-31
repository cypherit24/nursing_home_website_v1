# Gemini Onboarding Handoff

- **From**: PM (Human) → **To**: Gemini 3.1 Pro (Reviewer / Agent C)
- **Date**: 2026-03-31
- **Status**: 프로젝트 코딩 시작 전 (설계 완료 단계)

---

## 1. 프로젝트 한줄 요약

전국 요양원 2만 곳의 공공데이터를 자동 수집하고, AI(GPT-4o-mini)가 기관별 SEO 소개글을 JSON으로 생성하여 Next.js 15 정적 페이지로 배포하는 **완전 자동화 SEO 수익화 시스템**.

---

## 2. 아키텍처 요약

```
공공데이터 xlsx → Supabase DB → GitHub Actions 파이프라인(3단계) → Next.js 15 SSG+ISR → Vercel
```

| 레이어 | 기술 | 핵심 포인트 |
|---|---|---|
| 데이터 수집 | Python + B550928 API (XML) | xmltodict 파싱, Semaphore(10), 기관코드 단건 조회 |
| DB | Supabase (PostgreSQL) | nursing_homes 테이블, seo_content JSONB, RLS 적용 |
| AI 생성 | gpt-4o-mini, JSON 출력 | 6필드 스키마, jsonschema 검증, Semaphore(20) |
| 프론트엔드 | Next.js 15 App Router + Tailwind | SSG 1000건 + ISR 19000건, Server Components |
| 보안 | CSP only | dangerouslySetInnerHTML **완전 제거**, React JSX 자동 이스케이핑 |
| Rate Limiting | Vercel KV | 60회/분, 봇 예외 |
| CI/CD | GitHub Actions | 매월 자동 스케줄 (3일 API → 5일 SEO → 6일 배포) |

---

## 3. 현재 폴더 구조

```
nursing_home_website_v1/
├── CLAUDE.md                          # 전역 행동 지침 (보안 규칙, 코딩 컨벤션)
├── docs/                              # 설계 문서 (읽기 전용)
│   ├── plan-v3.md                     # ★ 현재 승인본 마스터 기획서
│   ├── plan-v1.md, plan-v2.md         # 이전 버전 (참고용)
│   ├── prompt_for_plan.md             # 초기 프롬프트 원문
│   ├── agents/
│   │   ├── folder_agents_plan_v1.md   # 에이전트 역할/권한 정의서
│   │   └── folder_agents_plan_v1_review.md  # 에이전트 구조 검증 결과
│   ├── templates/
│   │   └── handoff_template.md        # 인수인계 양식
│   └── xml_related/                   # API 응답 스크린샷 참고자료
├── src/                               # 소스 코드 (아직 빈 구조)
│   ├── pipeline/                      # Python 데이터 파이프라인
│   │   └── schemas/                   # seo_content JSON 스키마 위치
│   ├── frontend/                      # Next.js 프론트엔드
│   │   ├── app/
│   │   ├── components/                # SeoContent 템플릿 컴포넌트 위치
│   │   └── types/                     # TS 타입 (pipeline/schemas와 동기화 필수)
│   └── __tests__/
├── supabase/migrations/               # DB 마이그레이션 SQL
├── .github/workflows/                 # CI/CD 워크플로우
├── outputs/                           # 작업 산출물
│   ├── handoff/                       # 인수인계 기록
│   └── reviews/                       # 검증 결과물
└── .devcontainer/                     # Codespaces 개발환경 설정 (수정 금지)
```

---

## 4. 에이전트 분리 체계

| Agent | 모델 | 역할 | 담당 영역 | 권한 |
|---|---|---|---|---|
| A (Architect) | Claude Opus 4.6 | 설계, 방향 재조정 | docs/ | Write |
| B (Maker) | Claude Sonnet 4.6 | 코드 작성 | src/, supabase/, .github/ | Write (PM 지시 시) |
| **C (Reviewer)** | **Gemini 3.1 Pro** | **코드 검증, QA** | **전체** | **Read-Only** |
| D (DevOps) | Haiku | 인프라 보조 | supabase/, .github/ | Write |

### Gemini (Agent C) 구체 임무

1. **기획 정합성 검증**: Maker가 작성한 코드가 `docs/plan-v3.md` 기획과 일치하는지 확인
2. **보안 감사 (S1~S7)**: `CLAUDE.md`의 보안 규칙 준수 여부 확인
   - S1: 환경변수 노출 여부
   - S2: dangerouslySetInnerHTML 사용 금지 확인
   - S3: SQL injection 방어 (RLS + parameterized query)
   - S4: Rate Limiting 정상 적용
   - S5: CSP 헤더 적용
   - S6: API 키 하드코딩 여부
   - S7: 입력 검증 (facility_code 등)
3. **스키마 교차 검증**: `src/pipeline/schemas/` ↔ `src/frontend/types/` 구조 일치 확인
4. **코드 품질 리뷰**: 수정 코드 스니펫 제안 (직접 파일 수정 금지)

---

## 5. 핵심 설계 결정 (v3 기준)

| 결정 | 내용 | 이유 |
|---|---|---|
| SEO 콘텐츠 형식 | HTML이 아닌 **구조화 JSON (JSONB)** | 디자인 변경 시 2만 건 재생성 불필요, XSS 원천 차단 |
| 렌더링 방식 | SeoContent 템플릿 컴포넌트 (React JSX) | dangerouslySetInnerHTML 제거 |
| HTML 정화 | nh3 제거, sanitize-html 제거 | JSON이므로 HTML 정화 자체가 불필요 |
| 검증 도구 | jsonschema (Python), Zod 또는 TS 타입 (Frontend) | 6필드 JSON 스키마 규격 검증 |
| 빌드 전략 | SSG 1000건 + ISR 19000건 (30일 revalidate) | Vercel 빌드 타임아웃 방지 |

---

## 6. 미해결 이슈 (리뷰 시 참고)

| 이슈 | 상태 | 현재 방침 |
|---|---|---|
| 평가등급 API 제공 불가 | 미해결 | 런칭 후 추가 (C안) |
| 시설 사진 API 제공 불가 | 미해결 | 홈페이지 URL 링크로 대체 (A안) |
| 비급여 금액 단위 불명확 | 주의 | 금액 그대로 저장 + 면책 고지 |
| adminPttnCd xlsx 미포함 | 주의 | OP1 먼저 호출하여 추출, 실패 시 폴백 |

---

## 7. 리뷰 시 필수 첨부 컨텍스트

검증 작업 시 아래 파일을 반드시 함께 참조할 것:

| 검증 대상 | 필수 첨부 파일 |
|---|---|
| DB/API 관련 코드 | `docs/plan-v3.md` + `src/pipeline/schemas/seo_content_schema.json` |
| 프론트엔드 컴포넌트 | `CLAUDE.md` + `src/frontend/types/` |
| 타입 정합성 | `src/pipeline/schemas/` + `src/frontend/types/` 동시 |
| 보안 전반 | `CLAUDE.md` (S1~S7 체크리스트) |
| 전체 아키텍처 | `docs/plan-v3.md` + `outputs/handoff/handoff_v1.md` |

---

## 8. 작업 흐름에서 Gemini의 위치

```
PM 지시 → Sonnet(Maker) 코드 작성 → PM이 변경 파일 + 기준 문서 첨부
                                         ↓
                                    Gemini(Reviewer) 검토
                                         ↓
                              문제 발견 시 수정 스니펫 제안 → PM이 Sonnet에게 전달
                              문제 없으면 "승인" → PM이 다음 단계 진행
```

**핵심 원칙**: Gemini는 코드를 직접 수정하지 않는다. 문제점 + 수정된 코드 스니펫을 PM에게 제안하는 역할만 수행한다.
