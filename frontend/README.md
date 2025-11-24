# 뉴스 검색 웹 애플리케이션

Naver 뉴스 검색 API를 사용하는 Streamlit 기반 웹 애플리케이션입니다.

## 기능

- 🔍 실시간 뉴스 검색
- 📰 Naver 뉴스 API 연동
- 🎨 깔끔한 UI/UX
- 📊 검색 결과 개수 및 정렬 옵션 설정
- 🔗 원문 링크 제공

## 실행 방법

### 1. Windows

```bash
cd frontend
run_app.bat
```

### 2. Linux/Mac

```bash
cd frontend
chmod +x run_app.sh
./run_app.sh
```

### 3. 직접 실행

```bash
cd frontend
streamlit run search_app.py
```

## 사용 방법

1. 애플리케이션이 실행되면 브라우저가 자동으로 열립니다 (기본: http://localhost:8501)
2. 검색창에 검색어를 입력합니다 (예: "경제", "주식", "부동산" 등)
3. "검색" 버튼을 클릭합니다
4. 검색 결과가 카드 형태로 표시됩니다
5. 각 결과의 "원문 보기" 링크를 클릭하여 원문을 확인할 수 있습니다

## 설정 옵션

사이드바에서 다음 옵션을 설정할 수 있습니다:

- **검색 결과 개수**: 5~50개 (기본: 10개)
- **정렬 방식**: 날짜순(최신순) 또는 관련도순

## 요구사항

- Python 3.7+
- Streamlit
- backend/external/naver_client.py 모듈
- Naver API Client ID 및 Secret (backend/config.py에 설정)

## 문제 해결

### "Naver API 설정 필요" 오류가 표시되는 경우

1. `backend/config.py` 파일에 Naver API 키가 설정되어 있는지 확인
2. 또는 환경 변수 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` 설정

### 모듈을 찾을 수 없다는 오류

프로젝트 루트 디렉토리에서 실행하거나, `frontend` 디렉토리에서 실행하세요.

## 스크린샷

애플리케이션 실행 시 다음과 같은 화면이 표시됩니다:

- 상단: 검색창
- 사이드바: 설정 및 정보
- 메인 영역: 검색 결과 카드

## 개발자 정보

Agentic News RAG 프로젝트의 프론트엔드 컴포넌트입니다.

