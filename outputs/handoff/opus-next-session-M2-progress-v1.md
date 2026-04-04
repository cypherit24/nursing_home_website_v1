# Handoff: M2 데이터 파이프라인 — step1 완료, T08 블로커

- **From**: Agent A (Opus) + Agent B (Sonnet) → **To**: 다음 세션 (Opus)
- **Date**: 2026-04-04
- **Milestone**: M2
- **Status**: 블로커 — T08 환경변수 미설정

---

## 완료 사항
- **T04/T04-b**: Supabase 마이그레이션 적용 확인 (nursing_homes + pipeline_errors, RLS 활성화)
- **T05**: 폴더 구조 + 유틸리티 파일 생성 (seo_content_schema.json, seo-content.ts, requirements.txt, supabase_client.py)
- **T06**: step1_load_xlsx.py 작성 + pytest 18개 통과
- **T06 리뷰 수정**: verify_data_integrity()에서 exec_sql RPC 의존 → supabase-py 필터 쿼리로 교체 (Opus 직접 수정)
- **T07**: manual_step1.yml 작성 + Agent A 보안 리뷰 4항목 통과
- **T07 리뷰 수정**: 정합성 검증 실패 시 RuntimeError raise 추가 (Opus 직접 수정)
- **agentD**: Supabase MCP 도구 5개 권한 부여

## 변경 파일
| 파일 경로 | 변경 유형 | 비고 |
|---|---|---|
| `src/pipeline/schemas/seo_content_schema.json` | 신규 | T05, 6필드 스키마 |
| `src/frontend/types/seo-content.ts` | 신규 | T05, S5 동기화 |
| `requirements.txt` | 신규 | T05, nh3 제거 |
| `src/pipeline/supabase_client.py` | 신규 | T05, lru_cache 싱글턴 |
| `src/pipeline/step1_load_xlsx.py` | 신규 | T06, Opus가 verify_data_integrity 2회 수정 |
| `src/__tests__/test_step1.py` | 신규 | T06, 18개 테스트 |
| `.github/workflows/manual_step1.yml` | 신규 | T07, confirm+test_mode 입력 |
| `.claude/agents/agentD.md` | 수정 | MCP 도구 5개 추가 |
| `outputs/reviews/T07-security-review-v1.md` | 신규 | Agent A 보안 리뷰 |

## 수정 요청 (Reviewer → Maker)
| 파일 | 라인 | 이슈 | 수정 지시 |
|---|---|---|---|
| — | — | 모두 해결됨 | Agent A 리뷰 지적 2건 Opus가 직접 수정 완료 |

## 블로커 (에스컬레이션 → PM)
- **T08 실행 불가**: Codespaces 환경변수(`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`)가 현재 세션에 미설정
- T03에서 Codespaces Secrets 등록은 완료했으나, 현재 Codespace 세션에 반영 안 됨
- **해결 방법**: (1) Codespace 재빌드, 또는 (2) 터미널에서 `export SUPABASE_URL=...` + `export SUPABASE_SERVICE_ROLE_KEY=...` 직접 설정
- Supabase project ID: `njchcyluxhndmditevcw` (ap-northeast-2)

## 다음 단계
- **T08**: 환경변수 설정 후 `TEST_MODE=true python -m src.pipeline.step1_load_xlsx` 실행 → 100건 적재 + 2회 upsert 안전성 검증
- **T09**: step2_fetch_api.py 작성 (Agent B)
- **T10**: step2 TEST_MODE 검증 (5건)
- **T11**: step2 GitHub Actions 워크플로우 (Agent D 또는 B)
- 미커밋 파일: `.claude/agents/architect.md`, `devops.md` 삭제 상태 (git status -D)
