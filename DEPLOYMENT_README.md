# Lost112 Chrome Extension 배포 가이드

## 📦 배포 파일
- `chrome_ext_v1.0.0.zip` - Chrome 확장 프로그램 배포용 압축 파일

## 🚀 Chrome 웹스토어 배포 방법

### 1. Chrome Developer Dashboard 접속
1. [Chrome Developer Dashboard](https://chrome.google.com/webstore/devconsole)에 접속
2. Google 계정으로 로그인
3. 개발자 등록 (첫 회 사용시 $5 등록비 필요)

### 2. 새 확장 프로그램 등록
1. "새 항목" 클릭
2. `chrome_ext_v1.0.0.zip` 파일 업로드
3. 스토어 목록 정보 작성:
   - **이름**: Lost112 Chatbot
   - **요약**: 경찰청 유실물 챗봇 - 분실물을 쉽고 빠르게 찾아보세요
   - **설명**: 상세 설명 작성 (아래 참고)
   - **카테고리**: 생산성
   - **언어**: 한국어

### 3. 스크린샷 및 아이콘 준비
- 확장 프로그램 아이콘: 128x128px (이미 포함됨)
- 스크린샷: 1280x800px 또는 640x400px (최소 1개 필요)
- 프로모션 이미지: 440x280px (선택사항)

### 4. 개인정보보호 및 보안
- 개인정보 처리방침 URL (필요시)
- 권한 사용 목적 설명

## 🔧 로컬 테스트 방법

### Chrome에서 직접 로드
1. Chrome 브라우저 열기
2. 주소창에 `chrome://extensions` 입력
3. 우상단 "개발자 모드" 활성화
4. "압축해제된 확장 프로그램 로드" 클릭
5. `chrome_ext` 폴더 선택

### 테스트 절차
1. 확장 프로그램 아이콘 클릭하여 팝업 열기
2. 이메일 입력 (예: test@example.com)
3. 회원가입/로그인 플로우 테스트
4. 분실물 신고 기능 테스트 (텍스트 + 이미지)

## 🌐 백엔드 URL 설정

현재 설정된 백엔드 주소:
- 로그인: `http://127.0.0.1:8000/auth/login`
- 회원가입: `http://127.0.0.1:8000/auth/register`
- 분실물 등록: `http://127.0.0.1:8000/items`

**배포 전 수정 필요사항:**
1. `chrome_ext/chat_window.js` 파일의 다음 URL들을 실제 서버 주소로 변경:
   - `LOGIN_ENDPOINT`
   - `REGISTER_ENDPOINT`
   - `handleUserLostItem` 함수 내 items 엔드포인트
   - `stopNotification` 함수 내 cease 엔드포인트

## 📋 배포 체크리스트

- [x] manifest.json 버전 업데이트 (1.0.0)
- [x] 아이콘 파일 포함 확인
- [x] 권한 설정 검토
- [x] host_permissions 추가
- [x] 배포용 zip 파일 생성
- [ ] 백엔드 URL을 실제 서버 주소로 변경
- [ ] Chrome 웹스토어 등록
- [ ] 스크린샷 및 설명 작성
- [ ] 개인정보보호 정책 검토

## 🔒 보안 고려사항

1. **HTTPS 사용**: 프로덕션에서는 반드시 HTTPS 사용
2. **CORS 설정**: 백엔드에서 확장 프로그램의 origin 허용
3. **토큰 보안**: 민감한 정보는 chrome.storage.local 사용 권장
4. **API 키**: 환경변수 또는 설정 파일로 관리

## 📞 문제 해결

- **CORS 에러**: 백엔드 서버에서 확장 프로그램 origin 허용 필요
- **권한 에러**: manifest.json의 host_permissions 확인
- **네트워크 에러**: 백엔드 서버 상태 및 URL 확인

## 🔄 업데이트 배포

1. 코드 수정 후 버전 번호 증가 (manifest.json)
2. 새 zip 파일 생성
3. Chrome Developer Dashboard에서 업데이트 업로드
4. 검토 완료 후 자동 배포