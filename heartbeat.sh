#!/bin/bash
while true; do
  # 1. 메인 세션 핑
  cd /workspaces/nursing_home_website_v1
  claude -p "캐시 유지를 위한 자동 핑입니다. ok라고만 대답하세요." < /dev/null
  
  
  # 3. 260초(4분 20초) 대기
  sleep 260
done

#npm install -g pm2
#npx pm2 start heartbeat.sh --name "claude-heartbeat"
#npx pm2 stop claude-heartbeat
#npx pm2 logs claude-heartbeat