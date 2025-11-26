"""
Build Context 노드
ES 결과와 Naver 결과를 통합하여 컨텍스트를 구축합니다.
"""

import sys
import os

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agent_state import AgentState
from rag.utils.source_extractor import extract_sources_from_state, format_sources_for_context


def build_context(state: AgentState) -> AgentState:
    """
    컨텍스트 구축 노드
    
    - ES 결과와 Naver 결과 통합
    - 컨텍스트 문자열 생성
    - 관련성 순으로 정렬
    
    Args:
        state: 현재 상태
    
    Returns:
        context가 추가된 상태
    """
    import time
    start_time = time.time()
    
    print("\n" + "="*80)
    print("[5단계] BUILD CONTEXT - 컨텍스트 구축 시작")
    print("="*80)
    
    context_parts = []
    
    # 1. ES 결과 통합 (노트북 방식: 모든 쿼리 결과를 합침)
    es_results = state.get("es_results", {})
    queries_results = es_results.get("queries", {})
    
    merged_context = ""
    
    # 노트북 방식: 각 쿼리별로 ES 결과 합치기
    for q, res in queries_results.items():
        try:
            hits = res.get("hits", {}).get("hits", [])
            for h in hits:
                # 노트북: h['_source']['content'] 사용하지만 실제로는 'text' 필드
                source = h.get("_source", {})
                text = source.get("text", source.get("content", ""))
                score = h.get("_score", 0.0)
                merged_context += f"\n[ES(RRF Score: {score:.4f})] {text}"
        except Exception as e:
            print(f"[ERROR] ES 결과 처리 오류 ({q}): {e}")
            pass
    
    if merged_context:
        context_parts.append(merged_context)
    
    # 2. 웹 검색 결과 통합 (노트북 방식: web_results 사용)
    web_results = state.get("web_results", {})
    naver_results = state.get("naver_results", [])
    
    # 웹 검색 결과가 있으면 우선적으로 추가 (최신 정보 우선)
    if web_results or naver_results:
        web_context = ""
        
        # Naver 결과가 있으면 구조화된 형식으로 추가
        if naver_results:
            web_context += "\n=== 최신 뉴스 (웹 검색 결과) ===\n"
            for i, result in enumerate(naver_results[:10], 1):  # 상위 10개만
                title = getattr(result, 'title', '제목 없음')
                link = getattr(result, 'link', '링크 없음')
                snippet = getattr(result, 'snippet', '요약 없음')
                web_context += f"\n{i}. {title}\n   링크: {link}\n   요약: {snippet}\n"
        
        # web_results도 추가 (DuckDuckGo 등 다른 소스)
        for q, res in web_results.items():
            if res and res != "웹 검색 실패":
                web_context += f"\n[WEB 검색 - 쿼리: {q}]\n{res}\n"
        
        if web_context:
            context_parts.insert(0, web_context)  # 최신 정보를 맨 앞에 배치
    
    # 3. 컨텍스트 통합
    if context_parts:
        context = "\n".join(context_parts)
    else:
        context = "검색 결과가 없습니다."
    
    # 4. 소스 추출 및 컨텍스트에 추가
    sources = extract_sources_from_state(state, max_sources=10)
    if sources:
        sources_text = format_sources_for_context(sources)
        context += sources_text
        state["sources"] = [s.to_dict() for s in sources]
        print(f"[INFO] 소스 추출 완료: {len(sources)}개")
    else:
        state["sources"] = []
    
    # 통계 출력
    es_count = len(queries_results)
    web_count = len(web_results)
    naver_count = len(naver_results)
    context_length = len(context)
    
    print(f"[OK] 컨텍스트 구축 완료")
    print(f"   ES 결과 쿼리 수: {es_count}개")
    print(f"   웹 검색 결과 쿼리 수: {web_count}개")
    print(f"   Naver 뉴스 결과 수: {naver_count}개")
    print(f"   추출된 소스 수: {len(sources)}개")
    print(f"   컨텍스트 길이: {context_length:,}자")
    if context_length > 0:
        print(f"   컨텍스트 미리보기 (처음 200자):")
        print(f"      {context[:200]}...")
    
    elapsed_time = time.time() - start_time
    print(f"소요 시간: {elapsed_time:.2f}초")
    print("="*80 + "\n")
    
    state["context"] = context
    return state

