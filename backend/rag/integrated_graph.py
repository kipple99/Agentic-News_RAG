"""
통합 RAG 에이전트 워크플로우
LangGraph를 사용한 에이전트 시스템
"""

from typing import Optional, List, Dict, Any, Tuple
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
from config import ELASTICSEARCH_HOST, ELASTICSEARCH_PORT


def _make_result_serializable(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    result 딕셔너리를 JSON 직렬화 가능한 형태로 변환
    SearchResult 객체를 딕셔너리로 변환
    """
    serializable = {}
    for key, value in result.items():
        if key == "naver_results" and isinstance(value, list):
            # SearchResult 객체 리스트를 딕셔너리 리스트로 변환
            serializable[key] = [
                {
                    "title": item.title if hasattr(item, 'title') else str(item),
                    "link": item.link if hasattr(item, 'link') else "",
                    "snippet": item.snippet if hasattr(item, 'snippet') else "",
                    "source": item.source if hasattr(item, 'source') else "",
                    "published_date": item.published_date if hasattr(item, 'published_date') else None
                } if hasattr(item, 'title') else item
                for item in value
            ]
        elif isinstance(value, dict):
            serializable[key] = _make_result_serializable(value)
        elif isinstance(value, list):
            serializable[key] = [
                _make_result_serializable(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            serializable[key] = value
    return serializable


def should_search_naver(state: AgentState) -> str:
    """
    관련성 판단 결과에 따라 웹 검색 여부 결정
    
    Returns:
        "naver_search" 또는 "build_context"
    """
    is_relevant = state.get("is_relevant_enough", False)
    need_websearch = state.get("need_websearch", [])
    
    # 관련성이 충분하지 않거나 웹 검색이 필요한 경우
    if not is_relevant or len(need_websearch) > 0:
        return "naver_search"
    else:
        return "build_context"


def create_integrated_agent_graph(
    llm: Optional[BaseChatModel] = None,
    es_client: Optional[Elasticsearch] = None,
    es_index: str = "rag_news_db",
    embedder: Optional[SentenceTransformer] = None,
    embedding_model_name: str = "all-MiniLM-L6-v2",
    llm_model_type: str = "openai"
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
        llm_model_type: LLM 모델 타입 ("openai", "gemini", "ollama" 등)
    
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
    llm_model_type: str = "openai"
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
        try:
            from rag.logging.agent_logger import get_logger
            logger = get_logger()
            logger.log_query_start(user_query)
        except ImportError:
            pass
    
    # 캐싱 확인
    cache = None
    if use_cache:
        try:
            from rag.cache.query_cache import get_cache
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
        except ImportError:
            pass
    
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
        "need_websearch": [],
        "naver_results": [],
        "web_results": {},
        "context": "",
        "sources": [],
        "answer": ""
    }
    
    try:
        print(f"\n[INFO] LangGraph 실행 중...\n")
        result = graph.invoke(initial_state)
        
        total_elapsed = time.time() - total_start_time
        
        # 통계 수집
        stats = {
            "execution_time": total_elapsed,
            "query_analysis": result.get("query_analysis", {}),
            "es_results_count": result.get("es_results", {}).get("total", 0),
            "naver_results_count": len(result.get("naver_results", [])),
            "is_relevant_enough": result.get("is_relevant_enough", False),
            "relevance_score": result.get("relevance_score", 0.0)
        }
        
        print("\n" + "="*80)
        print("RAG AGENT 실행 완료")
        print("="*80)
        print(f"총 소요 시간: {total_elapsed:.2f}초")
        print(f"ES 검색 결과: {stats['es_results_count']}개")
        print(f"Naver 검색 결과: {stats['naver_results_count']}개")
        print(f"관련성 점수: {stats['relevance_score']:.2f}")
        print("="*80 + "\n")
        
        # 로깅
        if logger:
            answer = result.get("answer", "")
            logger.log_query_end(
                query=user_query,
                answer=answer,
                execution_time=total_elapsed,
                stats=stats
            )
        
        # 캐싱 저장 (SearchResult 객체를 딕셔너리로 변환)
        if cache:
            # result를 직렬화 가능한 형태로 변환
            serializable_result = _make_result_serializable(result)
            cache.set(user_query, {"chat_history": chat_history}, serializable_result)
        
        return result
        
    except Exception as e:
        total_elapsed = time.time() - total_start_time
        error_msg = f"그래프 실행 실패 (소요 시간: {total_elapsed:.2f}초)\n   오류: {str(e)}"
        print(f"\n[ERROR] {error_msg}")
        
        import traceback
        traceback.print_exc()
        
        if logger:
            import traceback as tb
            error_context = f"Query: {user_query}\nTraceback: {tb.format_exc()}"
            logger.log_error(Exception(str(e)), context=error_context)
        
        return {
            "answer": f"오류 발생: {str(e)}",
            "error": str(e),
            "query_analysis": {},
            "es_results": {"total": 0},
            "naver_results": [],
            "is_relevant_enough": False,
            "relevance_score": 0.0
        }

