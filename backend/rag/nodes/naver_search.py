"""
Naver Search 노드
Naver Search API를 사용하여 외부 뉴스를 검색합니다.
"""

import sys
import os
from typing import List

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rag.agent_state import AgentState
from external.naver_client import UnifiedSearchClient, SearchResult


def search_naver(state: AgentState) -> AgentState:
    """
    Naver 검색 노드 (노트북 개선 버전)
    
    - need_websearch 리스트의 각 쿼리에 대해 검색
    - Naver Search API 호출 (또는 DuckDuckGo 폴백)
    - 검색 결과 포맷팅
    
    Args:
        state: 현재 상태
    
    Returns:
        naver_results와 web_results가 추가된 상태
    """
    import time
    start_time = time.time()
    
    print("\n" + "="*80)
    print("[4단계] NAVER SEARCH - 외부 웹 검색 시작")
    print("="*80)
    
    need_web = state.get("need_websearch", [])
    web_results = {}
    naver_results = []
    
    if not need_web:
        print("[WARN] 웹 검색이 필요하지 않습니다. 이 노드는 건너뛰어야 합니다.")
        print("="*80 + "\n")
        state["naver_results"] = []
        state["web_results"] = {}
        return state
    
    print(f"검색할 쿼리 수: {len(need_web)}")
    for i, q in enumerate(need_web, 1):
        print(f"   {i}. {q}")
    
    # 노트북 방식: need_websearch 리스트의 각 쿼리에 대해 검색
    for idx, q in enumerate(need_web, 1):
        print(f"\n   [{idx}/{len(need_web)}] 검색 중: '{q}'")
        try:
            # 옵션 1: Naver Search API 사용 (우선)
            try:
                print(f"      [INFO] Naver Search API 호출 중...")
                client = UnifiedSearchClient()
                results: List[SearchResult] = client.search(
                    query=q,
                    num_results=5,
                    provider="naver"
                )
                web_results[q] = "\n".join([
                    f"{i+1}. {r.title}\n   {r.link}\n   {r.snippet[:200]}..."
                    for i, r in enumerate(results)
                ])
                naver_results.extend(results)
                print(f"      [OK] Naver 검색 성공: {len(results)}개 결과")
            except Exception as e1:
                print(f"      [WARN] Naver 검색 실패: {e1}")
                # 옵션 2: DuckDuckGo 폴백 (노트북 방식)
                try:
                    print(f"      [INFO] DuckDuckGo 폴백 시도 중...")
                    from langchain_community.tools import DuckDuckGoSearchRun
                    ddg = DuckDuckGoSearchRun()
                    result = ddg.run(q)
                    web_results[q] = result
                    print(f"      [OK] DuckDuckGo 검색 성공")
                except Exception as e2:
                    print(f"      [ERROR] DuckDuckGo 검색도 실패: {e2}")
                    web_results[q] = "웹 검색 실패"
        except Exception as e:
            print(f"      [ERROR] 웹 검색 실패: {e}")
            web_results[q] = "웹 검색 실패"
    
    print(f"\n[OK] 웹 검색 완료")
    print(f"   총 Naver 결과: {len(naver_results)}개")
    print(f"   검색된 쿼리 수: {len(web_results)}개")
    
    elapsed_time = time.time() - start_time
    print(f"소요 시간: {elapsed_time:.2f}초")
    print("="*80 + "\n")
    
    state["naver_results"] = naver_results
    state["web_results"] = web_results
    
    return state

