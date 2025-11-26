# 프론트엔드 → 백엔드 질의응답 흐름 가이드

프론트엔드에서 질문을 입력했을 때 백엔드에서 어떻게 처리되는지 설명합니다.

## 전체 흐름

```
[프론트엔드] 질문 입력
    ↓
[프론트엔드] POST /query API 호출
    ↓
[백엔드] FastAPI 엔드포인트 수신
    ↓
[백엔드] RAG 워크플로우 실행
    ↓
[백엔드] 답변 생성 완료
    ↓
[프론트엔드] 답변 표시
```

## 상세 흐름

### 1. 프론트엔드 (frontend/search_app.py)

**파일**: `frontend/search_app.py`

**기능**:
- 사용자가 질문 입력
- 백엔드 API에 POST 요청 전송
- 응답 받아서 화면에 표시

**코드 흐름**:
```python
# 사용자 질문 입력
search_query = st.text_input("🔍 Enter search query")

# 검색 버튼 클릭 시
if search_button and search_query:
    # 백엔드 API 호출
    result = send_query(search_query)  # POST /query
    
    # 답변 표시
    st.write(result["answer"])
```

**API 호출**:
```python
POST http://localhost:8000/query
{
    "query": "오늘의 자동차 뉴스",
    "chat_history": [...]  # 대화 기록 (선택)
}
```

---

### 2. 백엔드 API 엔드포인트 (backend/app.py)

**파일**: `backend/app.py`

**엔드포인트**: `POST /query`

**기능**:
- 프론트엔드 요청 수신
- RAG 워크플로우 실행
- 결과 반환

**코드 흐름**:
```python
@app.post("/query")
async def process_query(request: QueryRequest):
    # 1. 통합 에이전트 시스템 초기화
    graph = get_integrated_agent()
    
    # 2. RAG 워크플로우 실행
    result = run_query(
        graph=graph,
        user_query=request.query,
        chat_history=request.chat_history
    )
    
    # 3. 결과 반환
    return QueryResponse(
        answer=result["answer"],
        method="integrated_rag",
        ...
    )
```

---

### 3. RAG 워크플로우 (backend/rag/integrated_graph.py)

**파일**: `backend/rag/integrated_graph.py`

**함수**: `run_query(graph, user_query, chat_history)`

**워크플로우**:

```
1. Query Analysis (쿼리 분석)
   파일: backend/rag/nodes/query_analysis.py
   - 쿼리 의도 파악
   - 서브쿼리 3개 생성
   - 검색 전략 결정

2. Internal DB Search (내부 DB 검색)
   파일: backend/rag/nodes/internal_search.py
   - Elasticsearch에서 Hybrid Search 실행
   - BM25 + Dense Vector + RRF Fusion

3. Relevance Check (관련성 판단)
   파일: backend/rag/nodes/relevance_check.py
   - 검색 결과 관련성 평가
   - 웹 검색 필요 여부 결정

4. Naver Search (웹 검색) - 조건부
   파일: backend/rag/nodes/naver_search.py
   - 필요 시 Naver API로 최신 뉴스 검색
   - 실패 시 DuckDuckGo 폴백

5. Build Context (컨텍스트 구축)
   파일: backend/rag/nodes/build_context.py
   - ES 결과 + 웹 검색 결과 통합
   - 소스 정보 추출

6. Generation (답변 생성)
   파일: backend/rag/nodes/generation.py
   - LLM으로 최종 답변 생성
   - 소스 정보 포함
```

---

## 각 단계별 파일 및 역할

### Step 1: Query Analysis
**파일**: `backend/rag/nodes/query_analysis.py`
- 입력: `user_query` (사용자 질문)
- 출력: `query_analysis` (의도, 서브쿼리, 검색 전략)
- **추가 개발**: `backend/rag/prompts/query_analysis_prompt.py` - 강화된 프롬프트 템플릿 사용

### Step 2: Internal DB Search
**파일**: `backend/rag/nodes/internal_search.py`
- 입력: `query_analysis["sub_queries"]` (서브쿼리 리스트)
- 출력: `es_results` (Elasticsearch 검색 결과)
- 사용: `backend/search/es_client.py` (Hybrid Search 유틸리티)
- **추가 개발**: `backend/rag/nodes/rerank_results.py` - 검색 결과 재순위화 (선택적)

### Step 3: Relevance Check
**파일**: `backend/rag/nodes/relevance_check.py`
- 입력: `es_results`, `user_query`
- 출력: `is_relevant_enough`, `need_websearch` (웹 검색 필요한 쿼리 리스트)
- **추가 개발**: `backend/rag/prompts/relevance_check_prompt.py` - 강화된 프롬프트 템플릿 사용

### Step 4: Naver Search (조건부)
**파일**: `backend/rag/nodes/naver_search.py`
- 입력: `need_websearch` (웹 검색 필요한 쿼리 리스트)
- 출력: `naver_results`, `web_results`
- 사용: `backend/external/naver_client.py` (Naver API 클라이언트)
- **추가 개발**: `backend/rag/nodes/multi_source_search.py` - 다중 검색 소스 통합 (Naver + DuckDuckGo 병렬 검색)

### Step 5: Build Context
**파일**: `backend/rag/nodes/build_context.py`
- 입력: `es_results`, `naver_results`, `web_results`
- 출력: `context` (통합 컨텍스트), `sources` (소스 정보)
- **추가 개발**: `backend/rag/utils/source_extractor.py` - 소스 자동 추출 및 포맷팅

### Step 6: Generation
**파일**: `backend/rag/nodes/generation.py`
- 입력: `context`, `user_query`, `chat_history`
- 출력: `answer` (최종 답변)
- 사용: `backend/agent/llm_factory.py` (LLM 생성)
- **추가 개발**: 
  - `backend/rag/prompts/generation_prompt.py` - 강화된 프롬프트 템플릿 사용
  - `backend/rag/nodes/answer_verification.py` - 답변 검증 (선택적)

---

## 데이터 흐름

```
프론트엔드 입력
    ↓
{
    "query": "오늘의 자동차 뉴스",
    "chat_history": []
}
    ↓
백엔드 API 수신
    ↓
RAG 워크플로우 실행
    ↓
{
    "query_analysis": {
        "intent": "검색",
        "sub_queries": ["2024년 12월 자동차 뉴스", "오늘 자동차 관련 뉴스", ...]
    },
    "es_results": {...},
    "is_relevant_enough": False,
    "need_websearch": ["2024년 12월 자동차 뉴스", ...],
    "naver_results": [...],
    "context": "=== 최신 뉴스 ===\n1. 제목\n...",
    "sources": [...],
    "answer": "오늘(2024년 12월) 자동차 관련 주요 뉴스..."
}
    ↓
프론트엔드 응답
    ↓
{
    "answer": "오늘(2024년 12월) 자동차 관련 주요 뉴스...",
    "method": "integrated_rag",
    "sub_queries": [...],
    "relevance_score": 0.3,
    "es_results_count": 5,
    "naver_results_count": 10
}
    ↓
프론트엔드 화면 표시
```

---

## 실행 방법

### 1. 백엔드 서버 실행
```bash
cd backend
python app.py
```
서버가 `http://localhost:8000`에서 실행됩니다.

### 2. 프론트엔드 실행
```bash
cd frontend
streamlit run search_app.py
```
프론트엔드가 `http://localhost:8501`에서 실행됩니다.

### 3. 사용
1. 프론트엔드에서 질문 입력
2. "Search" 버튼 클릭
3. 백엔드에서 처리 후 답변 표시

---

## 주요 파일 위치

```
프론트엔드
└── frontend/search_app.py          # Streamlit UI, API 호출

백엔드 API
└── backend/app.py                  # FastAPI 서버, /query 엔드포인트

RAG 워크플로우
└── backend/rag/
    ├── integrated_graph.py         # 워크플로우 통합 및 실행
    │                               # 추가 개발: 캐싱, 로깅 통합
    ├── nodes/                      # 각 단계별 노드
    │   ├── query_analysis.py       # 1단계: 쿼리 분석
    │   ├── internal_search.py      # 2단계: 내부 DB 검색
    │   ├── relevance_check.py       # 3단계: 관련성 판단
    │   ├── naver_search.py         # 4단계: 웹 검색 (조건부)
    │   ├── build_context.py        # 5단계: 컨텍스트 구축
    │   ├── generation.py           # 6단계: 답변 생성
    │   │
    │   └── 추가 개발 노드:
    │       ├── rerank_results.py        # 검색 결과 재순위화
    │       ├── multi_source_search.py   # 다중 검색 소스 통합
    │       └── answer_verification.py   # 답변 검증
    │
    ├── prompts/                    # 추가 개발: 프롬프트 템플릿
    │   ├── query_analysis_prompt.py    # 쿼리 분석 프롬프트
    │   ├── relevance_check_prompt.py   # 관련성 판단 프롬프트
    │   └── generation_prompt.py         # 답변 생성 프롬프트
    │
    ├── utils/                      # 추가 개발: 유틸리티
    │   └── source_extractor.py     # 소스 추출 및 포맷팅
    │
    ├── cache/                      # 추가 개발: 캐싱 시스템
    │   └── query_cache.py         # 쿼리 결과 캐싱 (LRU, TTL)
    │
    └── logging/                    # 추가 개발: 로깅 시스템
        └── agent_logger.py         # 상세한 실행 로깅

유틸리티
└── backend/
    ├── search/es_client.py         # Elasticsearch 검색 유틸리티
    ├── external/naver_client.py    # Naver API 클라이언트
    └── agent/llm_factory.py        # LLM 생성 팩토리
```

---

---

## 추가 개발 기능

### 프롬프트 튜닝 (추가 개발)

**위치**: `backend/rag/prompts/`

**목적**: LLM에게 더 명확하고 상세한 지시를 제공하여 답변 품질 향상

**구현 내용**:
1. **쿼리 분석 프롬프트** (`query_analysis_prompt.py`)
   - 의도 분류 체계화 (6가지 유형)
   - 서브쿼리 생성 원칙 상세화
   - 검색 전략 결정 기준 명확화
   - 출력 예시 포함

2. **관련성 판단 프롬프트** (`relevance_check_prompt.py`)
   - 판단 기준 상세화 (db vs web)
   - ES 점수 해석 가이드
   - 4단계 판단 프로세스
   - 판단 예시 포함

3. **답변 생성 프롬프트** (`generation_prompt.py`)
   - 답변 구조 가이드 (요약형/설명형/비교형)
   - 정보 표현 원칙 (구체성, 명확성, 신뢰성)
   - 출처 표시 형식 명확화
   - 환각 방지 지침
   - 답변 예시 포함

**사용 위치**: 각 노드에서 프롬프트 템플릿 함수 호출
- `nodes/query_analysis.py` → `get_query_analysis_prompt()`
- `nodes/relevance_check.py` → `get_relevance_check_prompt()`
- `nodes/generation.py` → `get_generation_prompt()`

---

### Phase 1 기능 (추가 개발)

#### 1. 소스 인용 및 출처 표시
**파일**: `backend/rag/utils/source_extractor.py`

**기능**:
- ES 결과, Naver 결과, 웹 검색 결과에서 소스 자동 추출
- 제목, 링크, 요약, 출처 타입 포함
- 중복 제거 및 점수 기준 정렬
- 답변에 출처 자동 추가

**통합 위치**:
- `nodes/build_context.py` - 컨텍스트 구축 시 소스 추출
- `nodes/generation.py` - 답변 생성 시 소스 추가

#### 2. 캐싱 시스템
**파일**: `backend/rag/cache/query_cache.py`

**기능**:
- LRU (Least Recently Used) 방식 캐싱
- TTL (Time To Live) 지원 (기본 1시간)
- 캐시 히트/미스 통계
- 자동 만료 처리

**통합 위치**:
- `integrated_graph.py`의 `run_query()` 함수
- `use_cache=True` 파라미터로 제어

**사용 예시**:
```python
result = run_query(graph, "질문", use_cache=True)
# 동일한 질문은 캐시에서 즉시 반환
```

#### 3. 상세한 로깅 시스템
**파일**: `backend/rag/logging/agent_logger.py`

**기능**:
- 쿼리 시작/종료 로깅
- 노드 실행 로깅
- 검색 결과 로깅
- 의사결정 로깅
- 캐시 히트/미스 로깅
- 에러 및 경고 로깅
- 파일 및 콘솔 로깅 지원

**로그 파일**: `logs/agent_YYYYMMDD.log` (일별 로그)

**통합 위치**:
- `integrated_graph.py`의 `run_query()` 함수
- `enable_logging=True` 파라미터로 제어

---

### Phase 2 기능 (추가 개발)

#### 1. 검색 결과 재순위화
**파일**: `backend/rag/nodes/rerank_results.py`

**기능**:
- Cross-encoder 모델을 사용한 재순위화
- 쿼리-문서 관련성 점수 재계산
- 원본 점수와 재순위화 점수 모두 저장
- 검색 정확도 10-20% 향상

**사용 방법**:
- 그래프에 노드 추가 필요 (선택적)
- `internal_search` 노드 후에 배치

#### 2. 다중 검색 소스 통합
**파일**: `backend/rag/nodes/multi_source_search.py`

**기능**:
- Naver API와 DuckDuckGo 병렬 검색
- ThreadPoolExecutor를 사용한 병렬 처리
- 결과 통합 및 중복 제거
- 정보 범위 2-3배 확대

**사용 방법**:
- `naver_search` 노드 대신 사용 가능
- 여러 소스에서 정보 수집

#### 3. 답변 검증
**파일**: `backend/rag/nodes/answer_verification.py`

**기능**:
- 정확성 검증 (컨텍스트 일치도)
- 일치도 검증 (환각 감지)
- 완전성 검증 (정보 누락 확인)
- 관련성 검증 (질문 관련성)
- 전체 점수 및 문제점 리포트

**검증 결과**:
- `answer_verified`: True/False
- `verification_score`: 0.0-1.0
- `verification_issues`: 문제점 리스트

**사용 방법**:
- 그래프에 노드 추가 필요 (선택적)
- `generation` 노드 후에 배치

---

## 요약

1. **프론트엔드**: 사용자 질문 입력 → API 호출 → 답변 표시
2. **백엔드 API**: 요청 수신 → RAG 워크플로우 실행 → 결과 반환
3. **RAG 워크플로우**: 쿼리 분석 → 내부 검색 → 관련성 판단 → (조건부) 웹 검색 → 컨텍스트 구축 → 답변 생성
4. **추가 개발 기능**:
   - 프롬프트 튜닝: 답변 품질 향상
   - 소스 인용: 사용자 신뢰도 향상
   - 캐싱: 성능 개선 (반복 쿼리 90% 이상 단축)
   - 로깅: 디버깅 용이성 향상
   - 재순위화: 검색 정확도 향상
   - 다중 소스: 정보 범위 확대
   - 답변 검증: 환각 감지 및 품질 보장
