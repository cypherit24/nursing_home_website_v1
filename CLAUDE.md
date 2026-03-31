# Project Contract — nursing_home_project_v1

## 프로젝트 설명
이 저장소는 nursing_home_project_v1 작업 공간이다.

## Commands
- test: `npm test`
- test:watch: `npm run test:watch`
- test:coverage: `npm run test:coverage`
- lint: `npm run lint`
- lint:fix: `npm run lint:fix`

## Safety Rules
- `.env` 파일과 `.env.*` 파일은 절대 읽거나 수정하지 않는다
- 파일을 삭제하기 전에 반드시 사람에게 먼저 확인한다
- 외부 패키지를 설치하기 전에 반드시 사람에게 먼저 확인한다
- `.devcontainer/` 폴더는 사람의 명시적 허가 없이 수정하지 않는다

## Structure
- 프로젝트 루트: `/workspaces/nursing_home_website_v1`
- 설정 파일: 프로젝트 루트에 위치
- 소스 코드: `src/` 폴더에 작성
- 설계 문서: 변경 계획을 확인 요청하기 **전에** 반드시 `docs/` 폴더에 .md 형식으로 저장한다 (읽기 전용, 파일명: 작업명-v1.md / 재작업 시 v2.md)
- 에이전트 구조 설계: `docs/agents/` 폴더에 저장
- 양식/템플릿: `docs/templates/` 폴더에 저장
- 작업 산출물: `outputs/` 폴더에 저장 (reviews/, handoff/ 등)
- 검증 결과물: `outputs/reviews/` 폴더에 저장
- 인수인계 기록: `outputs/handoff/` 폴더에 저장 (파일명: `from-to-작업명-v1.md`, 예: `opus-sonnet-schema-design-v1.md`)

## Working Style
- 수정 전에 항상 변경 계획을 먼저 보여준다
- 수정 후에는 무엇을 바꿨는지 5줄 이내로 요약한다
- 불확실한 부분이 있으면 추측하지 말고 askuserquestion으로 질문한다
