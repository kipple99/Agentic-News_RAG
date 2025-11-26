"""
통합 LangGraph 에이전트
이미지 워크플로우에 맞춘 통합 그래프
"""

import os
from typing import Optional, List, Tuple, Union
from langgraph.graph import StateGraph, END
from langchain_core.language_models import BaseChatModel
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

from rag.agent_state import AgentState
from rag.nodes import (
    analyze_query,
    search_internal_db,
    check_relevance,
    search_naver,
    build_context,
    generate_answer
)
from agent.llm_factory import LLMFactory
from config import (
    ELASTICSEARCH_HOST,
    ELASTICSEARCH_PORT,
    GEMINI_API_KEY,
    OPENAI_API_KEY
)


def should_search_naver(state: AgentState) -> str:
    """
    관련성 판단 후 분기 결정 함수 (노트북 방식)
    
    Args:
        state: 현재 상태
    
    Returns:
        "naver_search" 또는 "build_context"
    """
    # 노트북 방식: need_websearch 리스트가 비어있지 않으면 웹 검색 필요
    need_web = state.get("need_websearch", [])
    is_relevant = state.get("is_relevant_enough", False)
    
    print(f"\n[분기 결정] 관련성 판단 결과:")
    print(f"   need_websearch: {len(need_web)}개 쿼리")
    print(f"   is_relevant_enough: {is_relevant}")
    
    # 둘 다 확인 (안전성)
    if len(need_web) > 0 or not is_relevant:
        print(f"   결정: naver_search (웹 검색 필요)")
        return "naver_search"
    else:
        print(f"   결정: build_context (내부 DB로 충분)")
        return "build_context"


def create_integrated_agent_graph(
    llm: Optional[BaseChatModel] = None,
    es_client: Optional[Elasticsearch] = None,
    es_index: str = "rag_news_db",
    embedder: Optional[SentenceTransformer] = None,
    embedding_model_name: str = "all-MiniLM-L6-v2",
    llm_model_type: str = "gemini"
) -> StateGraph:
    """
    통합 에이전트 그래프 생성
    
    워크플로우:
    1. query_analysis - 쿼리 분석
    2. internal_db_search - 내부 DB 검색
    3. relevance_check - 관련성 판단
    4. 조건부 분기:
       - NO → naver_search → build_context
       - YES → build_context
    5. generation - 답변 생성
    6. END
    
    Args:
        llm: LLM 객체 (None이면 자동 생성)
        es_client: Elasticsearch 클라이언트 (None이면 자동 생성)
        es_index: Elasticsearch 인덱스 이름
        embedder: 임베딩 모델 (None이면 자동 생성)
        embedding_model_name: 임베딩 모델 이름
        llm_model_type: LLM 모델 타입 ("gemini", "openai", "ollama" 등)
    
    Returns:
        컴파일된 LangGraph 객체
    """
    # LLM 초기화
    if llm is None:
        try:
            llm = LLMFactory.create_llm(llm_model_type)
        except Exception as e:
            print(f"[WARN] LLM 생성 실패 ({llm_model_type}), 기본 LLM 사용: {e}")
            llm = LLMFactory.get_default_llm()
    
    # Elasticsearch 클라이언트 초기화
    if es_client is None:
        es_host = f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}"
        es_client = Elasticsearch(hosts=[es_host])
    
    # 임베딩 모델 초기화
    if embedder is None:
        embedder = SentenceTransformer(embedding_model_name)
    
    # 그래프 빌더 생성
    graph_builder = StateGraph(AgentState)
    
    # 노드 추가
    graph_builder.add_node(
        "query_analysis",
        lambda state: analyze_query(state, llm)
    )
    
    graph_builder.add_node(
        "internal_db_search",
        lambda state: search_internal_db(state, es_client, es_index, embedder)
    )
    
    graph_builder.add_node(
        "relevance_check",
        lambda state: check_relevance(state, llm)
    )
    
    graph_builder.add_node(
        "naver_search",
        search_naver
    )
    
    graph_builder.add_node(
        "build_context",
        build_context
    )
    
    graph_builder.add_node(
        "generation",
        lambda state: generate_answer(state, llm)
    )
    
    # 엣지 추가
    graph_builder.set_entry_point("query_analysis")
    
    graph_builder.add_edge("query_analysis", "internal_db_search")
    graph_builder.add_edge("internal_db_search", "relevance_check")
    
    # 조건부 분기: relevance_check → naver_search or build_context
    graph_builder.add_conditional_edges(
        "relevance_check",
        should_search_naver,
        {
            "naver_search": "naver_search",
            "build_context": "build_context"
        }
    )
    
    # naver_search 후 build_context로
    graph_builder.add_edge("naver_search", "build_context")
    
    # build_context 후 generation으로
    graph_builder.add_edge("build_context", "generation")
    
    # generation 후 종료
    graph_builder.add_edge("generation", END)
    
    return graph_builder.compile()


def initialize_agent_system(
    es_index: str = "rag_news_db",
    embedding_model_name: str = "all-MiniLM-L6-v2",
    llm_model_type: str = "gemini"
) -> Tuple[StateGraph, BaseChatModel, Optional[Elasticsearch], Optional[SentenceTransformer]]:
    """
    에이전트 시스템 초기화
    
    Args:
        es_index: Elasticsearch 인덱스 이름
        embedding_model_name: 임베딩 모델 이름
        llm_model_type: LLM 모델 타입
    
    Returns:
        (graph, llm, es_client, embedder) 튜플
    """
    # LLM 초기화
    try:
        llm = LLMFactory.create_llm(llm_model_type)
    except Exception as e:
        print(f"[WARN] LLM 생성 실패, 기본 LLM 사용: {e}")
        llm = LLMFactory.get_default_llm()
    
    # Elasticsearch 클라이언트 초기화 (연결 실패 시 None 반환)
    es_client = None
    es_host = f"http://{ELASTICSEARCH_HOST}:{ELASTICSEARCH_PORT}"
    try:
        es_client = Elasticsearch(hosts=[es_host], request_timeout=5)
        # 연결 테스트
        if not es_client.ping():
            print(f"[WARN] Elasticsearch 연결 실패 ({es_host}). 웹 검색만 사용합니다.")
            es_client = None
        else:
            print(f"[OK] Elasticsearch 연결 성공: {es_host}")
    except Exception as e:
        print(f"[WARN] Elasticsearch 연결 실패: {e}")
        print(f"   -> 웹 검색만 사용하여 동작합니다.")
        es_client = None
    
    # 임베딩 모델 초기화 (ES가 없어도 웹 검색에는 필요 없지만, 나중을 위해 초기화)
    embedder = None
    try:
        embedder = SentenceTransformer(embedding_model_name)
    except Exception as e:
        print(f"[WARN] 임베딩 모델 초기화 실패: {e}")
        embedder = None
    
    # 그래프 생성
    graph = create_integrated_agent_graph(
        llm=llm,
        es_client=es_client,
        es_index=es_index,
        embedder=embedder,
        embedding_model_name=embedding_model_name,
        llm_model_type=llm_model_type
    )
    
    return graph, llm, es_client, embedder


def run_query(
    graph: StateGraph,
    user_query: str,
    chat_history: Optional[List[dict]] = None,
    use_cache: bool = True,
    enable_logging: bool = True
) -> dict:
    """
    쿼리 실행
    
    Args:
        graph: LangGraph 객체
        user_query: 사용자 질문
        chat_history: 대화 기록 (선택사항)
        use_cache: 캐싱 사용 여부
        enable_logging: 로깅 활성화 여부
    
    Returns:
        실행 결과 딕셔너리
    """
    import time
    total_start_time = time.time()
    
    # 로깅 초기화
    logger = None
    if enable_logging:
        from rag.logging import get_logger
        logger = get_logger()
        logger.log_query_start(user_query)
    
    # 캐싱 확인
    cache = None
    if use_cache:
        from rag.cache import get_cache
        cache = get_cache()
        cached_result = cache.get(user_query, {"chat_history": chat_history})
        if cached_result:
            if logger:
                logger.log_cache_hit(user_query)
            print("\n[INFO] 캐시에서 결과를 반환합니다.")
            return cached_result
        else:
            if logger:
                logger.log_cache_miss(user_query)
    
    print("\n" + "="*80)
    print("RAG AGENT 실행 시작")
    print("="*80)
    print(f"사용자 질문: {user_query}")
    print(f"대화 기록: {len(chat_history) if chat_history else 0}개")
    print(f"시작 시간: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    if chat_history is None:
        chat_history = []
    
        initial_state: AgentState = {
            "user_query": user_query,
            "chat_history": chat_history,
            "query_analysis": {},
            "es_results": {},
            "is_relevant_enough": False,
            "relevance_score": 0.0,
            "need_websearch": [],  # 노트북 방식 추가
            "naver_results": [],
            "web_results": {},  # 노트북 방식 추가
            "context": "",
            "sources": [],  # 소스 정보 추가
            "answer": ""
        }
    
    try:
        print(f"\n[INFO] LangGraph 실행 중...\n")
        result = graph.invoke(initial_state)
        
        total_elapsed = time.time() - total_start_time
        
        # 통계 수집
        stats = {
            "execution_time": total_elapsed,
            "es_results": result.get('es_results', {}).get('total', 0),
            "relevance_score": result.get('relevance_score', 0.0),
            "web_search_count": len(result.get('naver_results', [])),
            "sources_count": len(result.get('sources', [])),
            "answer_length": len(result.get('answer', ''))
        }
        
        # 캐시에 저장
        if cache:
            cache.set(user_query, result, {"chat_history": chat_history})
        
        # 로깅
        if logger:
            logger.log_query_end(
                user_query,
                result.get('answer', ''),
                total_elapsed,
                stats=stats
            )
        
        print("\n" + "="*80)
        print("[OK] RAG AGENT 실행 완료")
        print("="*80)
        print(f"총 소요 시간: {total_elapsed:.2f}초")
        print(f"실행 단계 요약:")
        print(f"   1. [OK] 쿼리 분석")
        print(f"   2. [OK] 내부 DB 검색 (ES 결과: {stats['es_results']}개)")
        print(f"   3. [OK] 관련성 판단 (점수: {stats['relevance_score']:.4f})")
        if result.get('need_websearch'):
            print(f"   4. [OK] 웹 검색 (Naver 결과: {stats['web_search_count']}개)")
        else:
            print(f"   4. [SKIP] 웹 검색 건너뜀")
        print(f"   5. [OK] 컨텍스트 구축")
        print(f"   6. [OK] 답변 생성")
        print(f"   7. [OK] 소스 추출 ({stats['sources_count']}개)")
        print(f"\n최종 답변:")
        print(f"   {result.get('answer', 'N/A')[:500]}...")
        print("="*80 + "\n")
        
        return result
    except Exception as e:
        total_elapsed = time.time() - total_start_time
        print(f"\n[ERROR] 그래프 실행 실패 (소요 시간: {total_elapsed:.2f}초)")
        print(f"   오류: {e}")
        import traceback
        traceback.print_exc()
        print("="*80 + "\n")
        return {
            "answer": f"오류 발생: {str(e)}",
            "error": str(e)
        }

