"""
Query Analysis 노드
사용자 쿼리를 분석하여 검색 전략을 결정합니다.
"""

import json
import re
import sys
import os
from typing import Dict, Any

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agent_state import AgentState
from langchain_core.language_models import BaseChatModel
from rag.prompts import get_query_analysis_prompt


def analyze_query(state: AgentState, llm: BaseChatModel) -> AgentState:
    """
    쿼리 분석 노드
    
    - 쿼리 의도 파악
    - 검색 전략 결정
    - 서브쿼리 생성 (선택적)
    
    Args:
        state: 현재 상태
        llm: LLM 객체
    
    Returns:
        query_analysis가 추가된 상태
    """
    import time
    start_time = time.time()
    
    print("\n" + "="*80)
    print("[1단계] QUERY ANALYSIS - 쿼리 분석 시작")
    print("="*80)
    
    user_query = state["user_query"]
    print(f"사용자 질문: {user_query}")
    print(f"LLM 모델: {type(llm).__name__}")
    
    # 시간 관련 키워드 감지 (최신 정보 필요 여부 판단)
    time_keywords = ["오늘", "최신", "최근", "현재", "지금", "요즘", "이번", "오늘의", "최신 뉴스", "최근 뉴스"]
    needs_recent_info = any(keyword in user_query for keyword in time_keywords)
    
    if needs_recent_info:
        print(f"[INFO] 시간 관련 키워드 감지: 최신 정보 필요")
    
    # 강화된 프롬프트 템플릿 사용
    prompt = get_query_analysis_prompt(
        user_query=user_query,
        needs_recent_info=needs_recent_info
    )
    
    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        
        # JSON 파싱
        match = re.search(r"```json\s*([\s\S]*?)\s*```", content)
        if match:
            json_string = match.group(1).strip()
        else:
            json_string = content
        
        analysis = json.loads(json_string)
        
        # 기본값 설정
        if "intent" not in analysis:
            analysis["intent"] = "검색"
        if "search_strategy" not in analysis:
            analysis["search_strategy"] = "internal_and_external"
        if "sub_queries" not in analysis or not isinstance(analysis["sub_queries"], list):
            analysis["sub_queries"] = [user_query]
        
        # 시간 관련 키워드가 있으면 강제로 external 검색 전략 설정
        if needs_recent_info:
            analysis["search_strategy"] = "internal_and_external"
            analysis["needs_web_search"] = True
            print(f"   [WARN] 시간 관련 키워드 감지: 웹 검색 전략 강제 설정")
        
        print(f"[OK] 쿼리 분석 완료")
        print(f"   의도: {analysis.get('intent', 'N/A')}")
        print(f"   검색 전략: {analysis.get('search_strategy', 'N/A')}")
        print(f"   생성된 서브쿼리 수: {len(analysis.get('sub_queries', []))}")
        for i, sq in enumerate(analysis.get('sub_queries', []), 1):
            print(f"      {i}. {sq}")
        
    except Exception as e:
        print(f"[ERROR] 쿼리 분석 실패: {e}")
        import traceback
        traceback.print_exc()
        # 기본값 사용
        analysis = {
            "intent": "검색",
            "search_strategy": "internal_and_external",
            "sub_queries": [user_query]
        }
        print(f"[WARN] 기본값 사용: 서브쿼리 = [{user_query}]")
    
    elapsed_time = time.time() - start_time
    print(f"소요 시간: {elapsed_time:.2f}초")
    print("="*80 + "\n")
    
    state["query_analysis"] = analysis
    return state

