"""
Relevance Check 노드
내부 DB 검색 결과의 관련성 및 충분성을 판단합니다.
"""

import sys
import os
from typing import Dict, Any

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agent_state import AgentState
from langchain_core.language_models import BaseChatModel
from rag.prompts import get_relevance_check_prompt


def check_relevance(state: AgentState, llm: BaseChatModel) -> AgentState:
    """
    관련성 판단 노드 (노트북 개선 버전)
    
    - ES 검색 결과의 관련성 평가
    - 각 서브쿼리별로 웹 검색 필요 여부 판단
    - is_relevant_enough 플래그 설정
    
    Args:
        state: 현재 상태
        llm: LLM 객체
    
    Returns:
        is_relevant_enough, relevance_score, need_websearch가 추가된 상태
    """
    import json
    
    es_results = state.get("es_results", {})
    user_query = state["user_query"]
    queries_results = es_results.get("queries", {})
    query_analysis = state.get("query_analysis", {})
    
    need_web = []
    
    print("\n" + "="*80)
    print("[3단계] RELEVANCE CHECK - 관련성 판단 시작")
    print("="*80)
    print(f"사용자 질문: {user_query}")
    print(f"평가할 쿼리 수: {len(queries_results)}")
    
    # 시간 관련 키워드 감지
    time_keywords = ["오늘", "최신", "최근", "현재", "지금", "요즘", "이번", "오늘의", "최신 뉴스", "최근 뉴스"]
    needs_recent_info = any(keyword in user_query for keyword in time_keywords)
    
    # 쿼리 분석에서 웹 검색 필요 플래그 확인
    needs_web_from_analysis = query_analysis.get("needs_web_search", False)
    
    if needs_recent_info or needs_web_from_analysis:
        print(f"[INFO] 시간 관련 키워드 또는 웹 검색 필요 플래그 감지: 모든 쿼리에 웹 검색 필요")
    
    # 디버그: 첫 번째 쿼리의 1순위 문서 출력
    try:
        if queries_results:
            first_query = list(queries_results.keys())[0]
            first_result = queries_results[first_query]
            hits = first_result.get("hits", {}).get("hits", [])
            if hits:
                first_hit = hits[0]
                print(f"\n[DEBUG] FIRST HIT SOURCE DUMP (Query: '{first_query[:30]}...'):")
                print(json.dumps(first_hit.get('_source', {}), indent=2, ensure_ascii=False))
                print("-------------------------------------------------")
    except Exception as e:
        print(f"[DEBUG] SOURCE DUMP 실패: {e}")
    
    # ES 결과가 없으면 모든 쿼리에 웹 검색 필요
    if not queries_results or len(queries_results) == 0:
        print(f"[WARN] ES 검색 결과가 없습니다. 모든 쿼리에 웹 검색이 필요합니다.")
        query_analysis = state.get("query_analysis", {})
        sub_queries = query_analysis.get("sub_queries", [state["user_query"]])
        need_web = sub_queries.copy()
        state["is_relevant_enough"] = False
        state["relevance_score"] = 0.0
        state["need_websearch"] = need_web
        print(f"[OK] 관련성 판단 완료 (ES 없음)")
        print(f"   웹 검색 필요한 쿼리 ({len(need_web)}개):")
        for i, q in enumerate(need_web, 1):
            print(f"      {i}. {q}")
        print("="*80 + "\n")
        return state
    
    # 각 서브쿼리별로 판단 (노트북 방식)
    for q in queries_results.keys():
        q_raw = q
        context = ""
        score = 0.0
        
        # 1. Context 추출 블록 시작
        try:
            result = queries_results[q]
            hits = result.get("hits", {}).get("hits", [])
            
            if hits:
                top_hit = hits[0]
                score = top_hit.get("_score", 0.0)
                
                for h in hits[:3]:  # 상위 3개
                    title = '제목 없음'
                    text_data = '내용 없음'
                    
                    source_dict = h.get('_source', {})
                    
                    if source_dict:
                        # 노트북: title, content 필드를 찾지만 실제로는 source, text 사용
                        title = source_dict.get('title', source_dict.get('source', '제목 없음'))
                        text_data = source_dict.get('text', source_dict.get('content', '내용 없음'))
                    
                    content_snippet = text_data[:200] + "..."
                    context += f"- [ES Content] Title: {title}, Snippet: {content_snippet}\n"
            else:
                context = "내부 DB에서 검색된 문서가 없습니다."
        
        # 1. Context 추출 블록 종료
        except Exception as e:
            print(f"[ERROR] ES 결과 구조 처리 오류 (Key: {q}): {e}")
            context = f"ES 결과 구조 오류: {e}"
            score = 0.0
        
        # ----------------------------------------------------
        # LLM EVALUATION INPUT LOG (노트북 방식)
        print("\n--- LLM EVALUATION INPUT LOG ---")
        print(f"1. Query Key Used: '{q}'")
        print(f"2. RRF Score: {score}")
        print(f"3. Context Snippet:")
        print(context)
        print("----------------------------------")
        # ----------------------------------------------------
        
        # 2. LLM 평가 (강화된 프롬프트 사용)
        # 시간 관련 키워드가 있으면 무조건 웹 검색 필요
        if needs_recent_info or needs_web_from_analysis:
            decision = "web"
            print(f"[DEBUG] 시간 관련 키워드 감지: '{q}' -> 웹 검색 필요 (자동 판단)")
        else:
            # 강화된 프롬프트 템플릿 사용
            prompt = get_relevance_check_prompt(
                sub_query=q_raw,
                es_score=score,
                context_snippet=context,
                user_query=user_query,
                needs_recent_info=needs_recent_info
            )
            
            # NameError 방지: decision 변수 초기화
            decision = "db"
            
            # LLM 호출 블록 시작
            try:
                response = llm.invoke(prompt)
                decision = response.content.strip().lower()
                print(f"[DEBUG] LLM Decision for '{q}': {decision}")
            # LLM 호출 블록 종료
            except Exception as e:
                print(f"[ERROR] LLM 평가 호출 실패: {e}. 기본값 'db' 사용.")
        
        if "web" in decision:
            need_web.append(q_raw)
    
    # 전체 관련성 판단 (하나라도 웹 검색이 필요하면 전체적으로 부족하다고 판단)
    is_relevant = len(need_web) == 0
    
    # 평균 관련성 점수 계산
    if queries_results:
        scores = []
        for q, result in queries_results.items():
            hits = result.get("hits", {}).get("hits", [])
            if hits:
                scores.append(hits[0].get("_score", 0.0))
        relevance_score = sum(scores) / len(scores) if scores else 0.0
    else:
        relevance_score = 0.0
    
    state["is_relevant_enough"] = is_relevant
    state["relevance_score"] = relevance_score
    state["need_websearch"] = need_web  # 노트북 방식: need_websearch 리스트 추가
    
    print(f"\n[OK] 관련성 판단 완료")
    print(f"   평균 관련성 점수: {relevance_score:.4f}")
    print(f"   {'내부 DB로 충분' if is_relevant else '웹 검색 필요'}")
    if need_web:
        print(f"   웹 검색 필요한 쿼리 ({len(need_web)}개):")
        for i, q in enumerate(need_web, 1):
            print(f"      {i}. {q}")
    else:
        print(f"   모든 쿼리가 내부 DB로 충분합니다")
    
    print("="*80 + "\n")
    return state

