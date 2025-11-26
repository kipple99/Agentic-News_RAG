# Agentic News RAG

프론트엔드에서 질문을 입력하면 백엔드의 RAG 에이전트가 자동으로 내부 DB 검색과 웹 검색을 판단하여 최적의 답변을 생성합니다.

## 빠른 시작

### 1. 저장소 클론
```bash
git clone https://github.com/kipple99/Agentic-News_RAG.git
cd Agentic-News_RAG
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

모든 필수 패키지가 `requirements.txt`에 포함되어 있습니다.

### 3. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하여 환경 변수를 설정하세요:

```env
# OpenAI API 키 (필수)
OPENAI_API_KEY=sk-proj-...

# Gemini API 키 (필수)
GEMINI_API_KEY=...

# Naver API 키 (필수)
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...

# Elasticsearch 설정 (선택사항, 없으면 웹 검색만 사용)
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
```

또는 `backend/config.py` 파일을 직접 수정할 수 있습니다. 환경 변수가 설정되어 있으면 우선 사용됩니다.

### 4. Elasticsearch 설정 (선택사항)

Elasticsearch가 없어도 웹 검색만으로 동작합니다. ES를 사용하려면:

#### Docker로 실행 (권장)
```bash
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  -p 9300:9300 \
  -e "discovery.type=single-node" \
  -e "xpack.security.enabled=false" \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0
```

#### ES 인덱싱 (데이터가 있는 경우)
```bash
cd backend/rag
python es_indexer.py  # 데이터 경로 지정 필요
```

### 5. 백엔드 서버 실행
```bash
cd backend
python app.py
```

서버가 `http://localhost:8000`에서 실행됩니다.

### 6. 프론트엔드 실행 (새 터미널)
```bash
cd frontend
streamlit run search_app.py
```

프론트엔드가 `http://localhost:8501`에서 실행됩니다.

### 7. 사용하기

1. 브라우저에서 `http://localhost:8501` 접속
2. 질문 입력 (예: "오늘의 자동차 관련 뉴스 탑 3 알려줘")
3. "Search" 버튼 클릭
4. 답변 확인

## 프로젝트 구조

```
Agentic-News_RAG/
├── backend/
│   ├── app.py                 # FastAPI 서버
│   ├── config.py              # 환경 설정
│   ├── agent/                 # LLM 팩토리
│   ├── external/              # 외부 API 클라이언트
│   ├── search/                # Elasticsearch 검색
│   └── rag/                   # RAG 워크플로우
│       ├── integrated_graph.py    # 메인 워크플로우
│       ├── nodes/                 # 각 단계별 노드
│       ├── prompts/               # 프롬프트 템플릿
│       ├── cache/                 # 캐싱 시스템
│       ├── logging/               # 로깅 시스템
│       └── utils/                 # 유틸리티
├── frontend/
│   └── search_app.py          # Streamlit UI
└── docs/
    ├── STRUCTURE_GUIDE.md     # 상세 구조 가이드
    └── PROMPT_ENHANCEMENT_GUIDE.md  # 프롬프트 가이드
```

## 주요 기능

### 1. 지능형 검색 전략
- 쿼리 분석을 통한 검색 전략 자동 결정
- 내부 DB 검색 vs 웹 검색 자동 판단
- 시간 민감성 자동 감지

### 2. 하이브리드 검색
- Elasticsearch Hybrid Search (BM25 + Dense Vector)
- Naver API + DuckDuckGo 병렬 검색
- 검색 결과 재순위화

### 3. 품질 향상 기능
- 소스 인용 및 출처 표시
- 캐싱 시스템 (LRU, TTL)
- 상세한 로깅 시스템
- 답변 검증

## 문제 해결

### 백엔드 실행 오류
- **ImportError**: 필요한 패키지가 설치되지 않았습니다. `pip install -r requirements.txt` 실행
- **API Key Error**: `backend/config.py`에서 API 키를 확인하세요
- **Elasticsearch 연결 실패**: ES가 없어도 웹 검색만으로 동작합니다. 경고 메시지는 무시해도 됩니다

### 프론트엔드 연결 오류
- 백엔드 서버가 실행 중인지 확인 (`http://localhost:8000`)
- CORS 오류가 발생하면 `backend/app.py`의 CORS 설정 확인

### 검색 결과가 없을 때
- Naver API 키가 올바른지 확인
- 네트워크 연결 확인
- 백엔드 로그 확인

## 추가 문서

- [STRUCTURE_GUIDE.md](docs/STRUCTURE_GUIDE.md) - 상세한 구조 및 워크플로우 설명
- [PROMPT_ENHANCEMENT_GUIDE.md](docs/PROMPT_ENHANCEMENT_GUIDE.md) - 프롬프트 튜닝 가이드

## 라이선스

MIT License

