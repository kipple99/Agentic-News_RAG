"""
통합 에이전트 상태 정의
이미지 워크플로우에 맞춘 상태 구조
"""

from typing import TypedDict, List, Dict, Any, Optional

# SearchResult는 타입 힌트로만 사용 (실제 import는 선택적)
try:
    from external.naver_client import SearchResult
except ImportError:
    # 타입 힌트용 더미 클래스
    class SearchResult:
        pass


class AgentState(TypedDict):
    """
    LangGraph 에이전트 상태 정의
    
    워크플로우:
    1. User Query → user_query
    2. Query Analysis → query_analysis
    3. Internal DB Search → es_results
    4. Relevance Check → is_relevant_enough
    5. Naver Search (if needed) → naver_results
    6. Build Context → context
    7. Generation → answer
    """
    # 입력
    user_query: str
    chat_history: List[Dict[str, str]]
    
    # Query Analysis 결과
    query_analysis: Dict[str, Any]  # {"intent": str, "search_strategy": str, "sub_queries": List[str]}
    
    # Internal DB Search 결과
    es_results: Dict[str, Any]  # {"hits": {"hits": [...]}, "total": int}
    
    # Relevance Check 결과
    is_relevant_enough: bool  # 내부 DB 결과가 충분한지 여부
    relevance_score: float  # 관련성 점수 (0.0 ~ 1.0)
    need_websearch: List[str]  # 노트북 방식: 웹 검색이 필요한 서브쿼리 리스트
    
    # Naver Search 결과 (필요시)
    naver_results: List[SearchResult]  # Naver API 검색 결과
    web_results: Dict[str, Any]  # 노트북 방식: 쿼리별 웹 검색 결과
    
    # Build Context 결과
    context: str  # ES 결과 + Naver 결과를 통합한 컨텍스트
    sources: List[Dict[str, Any]]  # 사용된 소스 정보 리스트
    
    # Generation 결과
    answer: str  # 최종 답변

