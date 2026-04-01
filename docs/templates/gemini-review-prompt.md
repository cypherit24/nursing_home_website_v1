# Gemini Review Prompt Template (Agent C)

> Continue IDE 사이드바에서 Gemini 3.1 Pro에게 리뷰 요청 시 사용하는 프롬프트 템플릿

---

## 사용법

1. Continue IDE 사이드바에서 아래 프롬프트 중 하나를 복사
2. 변경된 파일을 `@` 멘션으로 첨부
3. 필수 기준 문서도 함께 첨부

---

## A. 코드 리뷰 + 보안 감사 통합 프롬프트

> 필수 첨부: `@CLAUDE.md` + `@docs/plan-v3.md` + 변경된 파일들

```
당신은 코드 리뷰어 겸 보안 감사관입니다.
@CLAUDE.md 와 @docs/plan-v3.md 를 기준으로 아래 체크리스트를 검증하세요.

### 보안 체크리스트 (S1~S7)
1. [S1] dangerouslySetInnerHTML 사용 여부
2. [S2] RLS 정책 정합성 (anon=SELECT only)
3. [S3] CSP 헤더 유지 여부 (script-src 'self')
4. [S4] 개인정보(representative_name) 비표시 준수
5. [S5] JSON 스키마와 TS 타입 동기화 여부
6. [S6] 시크릿 하드코딩 여부
7. [S7] 외부 입력 검증 (facility_code 등)

### 기능 정합성
- plan-v3.md의 해당 태스크 요구사항 충족 여부
- 에러 핸들링 + 원자적 업데이트 패턴 준수

### 출력 형식
판정: 승인 / 수정필요 / 블로커

수정이 필요한 경우:
| 파일 | 라인 | 이슈 유형 | 설명 | 수정 코드 |
|---|---|---|---|---|
```

---

## B. 스키마 교차 검증 전용 프롬프트

> 필수 첨부: `@src/pipeline/schemas/seo_content_schema.json` + `@src/frontend/types/seo-content.ts`

```
아래 두 파일의 구조를 비교하여 불일치를 검출하세요:

1. 필드 이름/타입 불일치
2. additionalProperties: false 유지 여부
3. minLength/maxLength 제약이 TS 코드에서 런타임 검증되는지
4. Python 스키마의 required 필드가 TS에서 optional(?)로 선언되어 있지 않은지

### 출력 형식
| 필드명 | Python 스키마 | TS 타입 | 불일치 내용 |
|---|---|---|---|
```

---

## C. 파이프라인 코드 리뷰 전용 프롬프트

> 필수 첨부: `@docs/plan-v3.md` + `@CLAUDE.md` + 변경된 step 파일

```
당신은 데이터 파이프라인 코드 리뷰어입니다.
다음 항목을 검증하세요:

1. Semaphore 값이 plan-v3 기준과 일치하는가 (step2: 5, step3: 20)
2. 원자적 업데이트 패턴 준수 (부분 실패 시 NULL 유지)
3. pipeline_errors 테이블 로깅 구현 여부
4. 정합성 검증 SQL 실행 여부
5. pytest 단위 테스트 존재 여부
6. 지수 백오프 구현 여부 (429/503 응답)

### 출력 형식
판정: 승인 / 수정필요 / 블로커

수정이 필요한 경우:
| 파일 | 라인 | 이슈 유형 | 설명 | 수정 코드 |
|---|---|---|---|---|
```

---

## D. 마일스톤 완료 전체 보안 감사 프롬프트

> 필수 첨부: `@CLAUDE.md` + `@docs/plan-v3.md` + 해당 마일스톤의 모든 변경 파일

```
마일스톤 [M?] 완료 전 전체 보안 감사를 수행하세요.
S1~S7 전체 항목을 빠짐없이 검증합니다.

추가 검증:
- 코드베이스에 dangerouslySetInnerHTML이 단 한 건도 없는지 확인
- .github/workflows/ 내 모든 YAML에서 하드코딩된 시크릿이 없는지 확인
- supabase/migrations/ 내 모든 SQL에서 RLS 정책이 포함되어 있는지 확인

### 출력 형식
| S# | 검증 항목 | 결과 | 비고 |
|---|---|---|---|

최종 판정: 통과 / 미통과 (미통과 항목 상세)
```

---

## 핵심 원칙

Gemini는 코드를 직접 수정하지 않습니다.
문제점 + 수정된 코드 스니펫을 PM에게 제안하는 역할만 수행합니다.
PM이 이 출력을 Sonnet에게 전달하여 실제 수정을 진행합니다.
