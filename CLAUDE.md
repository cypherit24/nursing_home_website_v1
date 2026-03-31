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
- 소스 코드: `src/` 폴더에 작성 (아직 없으면 생성)
- 연습 결과물: `outputs/` 폴더에 저장
- 계획 결과물: 변경 계획을 확인 요청하기 **전에** 반드시 `plans/` 폴더에 .md 형식으로 저장한다 (아직 없으면 생성, 파일명: 작업명-v1.md / 재작업 시 v2.md)
- 계획 검증 결과물 : plans 폴더의 계획을 검증하면, 결과물을 `plans_verificated/` 폴더에 저장
- 폴더/에이전트 구조 계획 결과물 : `/agents_folder_plan/`폴더에 저장

## Working Style
- 수정 전에 항상 변경 계획을 먼저 보여준다
- 수정 후에는 무엇을 바꿨는지 5줄 이내로 요약한다
- 불확실한 부분이 있으면 추측하지 말고 질문한다
