# nursing_home_website_v1

## QA 검증 흐름 (Agent C)

Claude Code에서 태스크 코딩 작업이 끝나면 자동으로 QA 검증 알림이 표시됩니다.

### 사용 방법

1. Claude Code에서 태스크 코딩 완료 → Stop hook이 변경 파일 목록을 자동 출력
   ```
   ========================================
     QA 검증 대기: 변경된 파일 목록
   ========================================
   src/pipeline/step1_load_xlsx.py
   src/__tests__/test_step1.py
   ----------------------------------------
     Continue IDE에서 @agentC-qa 실행하세요
     첨부: 위 변경 파일들 @멘션
   ========================================
   ```
2. Continue IDE 사이드바를 열고 `@agentC-qa` 입력
3. 변경된 파일들을 `@` 멘션으로 첨부 (예: `@src/pipeline/step1_load_xlsx.py`)
4. 태스크 번호를 함께 전달 (예: `T06 검증해줘`)
5. Gemini가 `.claude/agents/agentC.md` 기준으로 보안(S1~S7) + 품질 + 정합성 검증 수행
6. 판정 결과 확인: **승인** / **수정필요** / **블로커**

### 관련 파일

| 파일 | 역할 |
|------|------|
| `.continue/agents/agentC-qa.yaml` | Continue IDE QA 에이전트 설정 |
| `.claude/agents/agentC.md` | 검증 가이드라인 (S1~S7 + 6가지 검증 유형) |
| `.claude/settings.json` | Stop hook (변경 파일 감지 + 알림) |