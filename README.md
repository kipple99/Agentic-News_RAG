# Agentic News RAG (8조)

Agentic RAG 기반 경제 뉴스 요약 시스템  
(빅데이터와 정보검색 팀 프로젝트 / 8조)

## 목표

- 내부 경제 뉴스 DB와 외부 뉴스 API(Naver)를 활용하여
- 사용자의 질의에 따라
  - 내부 데이터만으로 충분하면 내부 데이터 기반 요약
  - 내부 데이터에 없으면 외부 최신 뉴스 기반 요약
- 멀티턴 대화(후속 질문)를 지원하는 RAG 시스템 구현

## 기술 스택 (예정)

- Python
- LangChain / LangGraph
- ElasticSearch
- SQLite
- Streamlit (또는 FastAPI + Frontend)
- NaverSearch API
- OpenAI API 또는 기타 LLM API

## 폴더 구조 (초안)

```text
backend/
  app.py
  rag/
    graph.py
    memory.py
  search/
    es_client.py
    indexer.py
  external/
    naver_client.py
data/
  raw/
  processed/
docs/
  mvp.md
  architecture.md
  scenario.md





