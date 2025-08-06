# Samsung AI Experience Group Dashboard

Samsung AI Experience Group을 위한 대시보드 웹 애플리케이션입니다.

## 🚀 기능

- 팀원 정보 관리
- 사용량 데이터 시각화
- 지출 데이터 분석
- 실시간 데이터 업데이트

## 🛠️ 기술 스택

- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Backend**: Flask (Python)
- **API**: Cursor Admin API
- **배포**: Vercel

## 📦 설치 및 실행

### 로컬 개발 환경

1. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

2. **환경 변수 설정**
   ```bash
   export CURSOR_API_KEY="your_cursor_api_key_here"
   ```

3. **애플리케이션 실행**
   ```bash
   python app.py
   ```

4. **브라우저에서 접속**
   ```
   http://localhost:8001
   ```

### Vercel 배포

1. **Vercel CLI 설치**
   ```bash
   npm i -g vercel
   ```

2. **환경 변수 설정**
   - Vercel 대시보드에서 `CURSOR_API_KEY` 환경 변수 설정

3. **배포**
   ```bash
   vercel --prod
   ```

## 🔧 환경 변수

| 변수명 | 설명 | 필수 |
|--------|------|------|
| `CURSOR_API_KEY` | Cursor Admin API 키 | ✅ |

## 📁 프로젝트 구조

```
├── app.py              # Flask 애플리케이션 (Vercel 배포용)
├── index.html          # 대시보드 프론트엔드
├── proxy_server.py     # 로컬 개발용 프록시 서버
├── requirements.txt    # Python 의존성
├── vercel.json        # Vercel 배포 설정
├── runtime.txt        # Python 런타임 버전
└── README.md         # 프로젝트 문서
```

## 🔌 API 엔드포인트

### 프록시 API
- `GET /api/*` - Cursor Admin API GET 요청 프록시
- `POST /api/*` - Cursor Admin API POST 요청 프록시

### 헬스 체크
- `GET /health` - 서비스 상태 확인

## 🚨 주의사항

1. **API 키 보안**: `CURSOR_API_KEY`는 환경 변수로 관리해야 합니다.
2. **CORS 설정**: 프론트엔드에서 API 호출 시 CORS 이슈가 없도록 설정되어 있습니다.
3. **로컬 개발**: 로컬 개발 시에는 `proxy_server.py`를 사용하세요.

## 📝 라이선스

이 프로젝트는 Samsung AI Experience Group 내부 사용을 위한 것입니다.

## 🤝 기여

프로젝트 개선을 위한 제안사항이 있으시면 언제든지 연락주세요. 
