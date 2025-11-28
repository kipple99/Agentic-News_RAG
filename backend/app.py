# -*- coding: utf-8 -*-
"""
Agentic News RAG Backend Server
통합 LangGraph 에이전트 시스템 사용 (이미지 워크플로우 기반)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 통합 에이전트 시스템 import (우선)
INTEGRATED_AGENT_AVAILABLE = False
try:
    from rag.integrated_graph import initialize_agent_system, run_query
    INTEGRATED_AGENT_AVAILABLE = True
    print("[OK] Integrated agent system available")
except ImportError as e:
    print(f"Warning: Integrated agent not available: {e}")
    print("Falling back to simple news_agent...")
    INTEGRATED_AGENT_AVAILABLE = False

# 폴백: 기존 news_agent (통합 에이전트가 없을 때)
NewsAgent = Any
create_news_agent = None
AGENT_AVAILABLE = False

if not INTEGRATED_AGENT_AVAILABLE:
    try:
        from agent.news_agent import create_news_agent, NewsAgent
        AGENT_AVAILABLE = True
    except ImportError as e:
        print(f"Warning: Agent not available: {e}")
        print("Please install required packages: pip install langchain langchain-core langchain-community langchain-openai")
        AGENT_AVAILABLE = False

app = FastAPI(title="Agentic News RAG API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 통합 에이전트 시스템 (우선)
_graph = None
_llm = None
_es_client = None
_embedder = None

# 폴백: 기존 에이전트
_agent: Optional[Any] = None

def get_integrated_agent():
    """통합 에이전트 시스템 초기화 및 반환"""
    global _graph, _llm, _es_client, _embedder
    
    if _graph is None:
        if not INTEGRATED_AGENT_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="Integrated agent not available. Please check if required packages are installed."
            )
        try:
            _graph, _llm, _es_client, _embedder = initialize_agent_system(
                es_index="rag_news_db",
                llm_model_type="openai"
            )
            print("[OK] Integrated agent system initialized successfully")
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            print(f"Error initializing integrated agent: {error_detail}")
            raise HTTPException(
                status_code=503, 
                detail=f"Failed to initialize integrated agent: {str(e)}"
            )
    return _graph

def get_agent() -> Any:
    """기존 에이전트 (폴백용)"""
    global _agent
    if _agent is None:
        if not AGENT_AVAILABLE:
            raise HTTPException(status_code=503, detail="Agent not available. Please check if langchain packages are installed.")
        try:
            _agent = create_news_agent(model_type="gemini", use_memory=True)
            print("Agent initialized successfully")
        except Exception as e:
            import traceback
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            print(f"Error initializing agent: {error_detail}")
            raise HTTPException(status_code=503, detail=f"Failed to initialize agent: {str(e)}")
    return _agent

def convert_es_results_to_frontend_format(es_results: Dict[str, Any], max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Elasticsearch 결과를 프론트엔드용 형태로 변환
    
    Args:
        es_results: es_results 딕셔너리 (queries와 total 포함)
        max_results: 최대 반환 결과 수
    
    Returns:
        프론트엔드용 내부 DB 결과 리스트
    """
    internal_db_results = []
    queries_results = es_results.get("queries", {})
    
    # 모든 쿼리 결과를 통합하여 상위 결과 추출
    all_hits = []
    for query, result in queries_results.items():
        hits = result.get("hits", {}).get("hits", [])
        for hit in hits:
            source = hit.get("_source", {})
            score = hit.get("_score", 0.0)
            
            # RRF 점수가 있으면 사용 (RRF fusion 결과)
            rrf_score = hit.get("rrf_score", score)
            
            all_hits.append({
                "title": source.get("title", source.get("source", "제목 없음")),
                "text": source.get("text", source.get("content", "")),
                "url": source.get("url", ""),
                "date": source.get("date", ""),
                "score": rrf_score,
                "es_score": score,
                "source_type": "internal_db"
            })
    
    # 점수 기준으로 정렬 (내림차순)
    all_hits.sort(key=lambda x: x["score"], reverse=True)
    
    # 중복 제거 (제목 기준) 및 상위 결과만 선택
    seen_titles = set()
    for hit in all_hits:
        if len(internal_db_results) >= max_results:
            break
        title = hit["title"]
        if title not in seen_titles:
            seen_titles.add(title)
            internal_db_results.append(hit)
    
    return internal_db_results

class QueryRequest(BaseModel):
    query: str
    chat_history: Optional[List[Dict[str, str]]] = None

class QueryResponse(BaseModel):
    answer: str
    method: str  # "api_search", "llm_generate", or "integrated_rag"
    sub_queries: Optional[List[str]] = None
    is_relevant_enough: Optional[bool] = None
    relevance_score: Optional[float] = None
    es_results_count: Optional[int] = None
    naver_results_count: Optional[int] = None
    internal_db_results: Optional[List[Dict[str, Any]]] = None
    naver_results: Optional[List[Dict[str, Any]]] = None

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    # 통합 에이전트 우선 확인
    if INTEGRATED_AGENT_AVAILABLE:
        agent_status = "available"
        try:
            if _graph is None:
                get_integrated_agent()
            agent_status = "initialized" if _graph is not None else "available"
        except:
            agent_status = "error"
        
        return {
            "status": "healthy",
            "agent_available": True,
            "agent_status": agent_status,
            "agent_type": "integrated_rag"
        }
    else:
        # 폴백: 기존 에이전트
        agent_status = "available" if AGENT_AVAILABLE else "unavailable"
        if AGENT_AVAILABLE:
            try:
                if _agent is None:
                    get_agent()
                agent_status = "initialized" if _agent is not None else "available"
            except:
                agent_status = "error"
        
        return {
            "status": "healthy",
            "agent_available": AGENT_AVAILABLE,
            "agent_status": agent_status,
            "agent_type": "simple_agent"
        }

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """통합 에이전트 시스템으로 쿼리 처리 (우선) 또는 기존 에이전트 (폴백)"""
    try:
        # 통합 에이전트 시스템 사용 (우선)
        if INTEGRATED_AGENT_AVAILABLE:
            graph = get_integrated_agent()
            
            # 쿼리 실행
            result = run_query(
                graph=graph,
                user_query=request.query,
                chat_history=request.chat_history
            )
            
            answer = result.get("answer", "답변 생성 실패")
            method = "integrated_rag"
            
            # 추가 정보 추출
            query_analysis = result.get("query_analysis", {})
            sub_queries = query_analysis.get("sub_queries", [])
            
            is_relevant = result.get("is_relevant_enough", False)
            relevance_score = result.get("relevance_score", 0.0)
            
            es_results = result.get("es_results", {})
            es_count = es_results.get("total", 0)
            
            naver_results_raw = result.get("naver_results", [])
            naver_count = len(naver_results_raw)
            
            # 내부 DB 결과를 프론트엔드용 형태로 변환
            internal_db_results = convert_es_results_to_frontend_format(es_results, max_results=10)
            
            # Naver 결과를 프론트엔드용 형태로 변환
            naver_results = []
            for item in naver_results_raw:
                if hasattr(item, 'title'):
                    naver_results.append({
                        "title": item.title,
                        "link": item.link if hasattr(item, 'link') else "",
                        "snippet": item.snippet if hasattr(item, 'snippet') else "",
                        "source": item.source if hasattr(item, 'source') else "Naver",
                        "published_date": item.published_date if hasattr(item, 'published_date') else None
                    })
                elif isinstance(item, dict):
                    naver_results.append(item)
            
            return QueryResponse(
                answer=answer,
                method=method,
                sub_queries=sub_queries,
                is_relevant_enough=is_relevant,
                relevance_score=relevance_score,
                es_results_count=es_count,
                naver_results_count=naver_count,
                internal_db_results=internal_db_results,
                naver_results=naver_results
            )
        else:
            # 폴백: 기존 에이전트
            agent = get_agent()
            
            chat_history = None
            if request.chat_history:
                try:
                    from langchain_core.messages import HumanMessage, AIMessage
                    chat_history = []
                    for msg in request.chat_history:
                        if msg.get("role") == "user":
                            chat_history.append(HumanMessage(content=msg.get("content", "")))
                        elif msg.get("role") == "assistant":
                            chat_history.append(AIMessage(content=msg.get("content", "")))
                except ImportError as e:
                    print(f"Warning: langchain_core.messages import failed: {e}")
                    chat_history = None
            
            answer = agent.run(request.query, chat_history=chat_history)
            
            # 판단 결과 추출 (간단히 키워드로 판단)
            method = "api_search" if any(kw in request.query.lower() for kw in ["검색", "찾아", "뉴스", "기사", "최신", "오늘"]) else "llm_generate"
            
            return QueryResponse(answer=answer, method=method)
            
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error in process_query: {error_detail}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/clear-history")
async def clear_history():
    """대화 기록 초기화"""
    # 통합 에이전트는 각 요청마다 chat_history를 받으므로 서버 측 메모리 초기화 불필요
    # 하지만 호환성을 위해 유지
    try:
        if INTEGRATED_AGENT_AVAILABLE:
            return {"message": "Chat history cleared (client-side only)"}
        else:
            agent = get_agent()
            agent.clear_memory()
            return {"message": "Chat history cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


