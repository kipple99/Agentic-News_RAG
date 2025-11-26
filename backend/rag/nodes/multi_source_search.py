"""
다중 검색 소스 통합 노드
여러 검색 소스를 병렬로 검색하고 결과를 통합합니다.
"""

import sys
import os
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agent_state import AgentState


def search_multi_source(state: AgentState) -> AgentState:
    """
    다중 검색 소스 통합 노드
    
    여러 검색 소스(Naver, Google, DuckDuckGo 등)를 병렬로 검색하고 결과를 통합합니다.
    
    Args:
        state: 현재 상태
    
    Returns:
        통합된 검색 결과가 포함된 상태
    """
    import time
    start_time = time.time()
    
    print("\n" + "="*80)
    print("[4-1단계] MULTI-SOURCE SEARCH - 다중 검색 소스 통합 시작")
    print("="*80)
    
    need_web = state.get("need_websearch", [])
    
    if not need_web:
        print("[INFO] 웹 검색이 필요하지 않습니다.")
        print("="*80 + "\n")
        return state
    
    print(f"검색할 쿼리 수: {len(need_web)}")
    print(f"사용 가능한 검색 소스: Naver, DuckDuckGo")
    
    all_results = {}
    naver_results = []
    duckduckgo_results = []
    
    def search_naver_api(query: str) -> tuple:
        """Naver API 검색"""
        try:
            from external.naver_client import UnifiedSearchClient, SearchResult
            client = UnifiedSearchClient()
            results = client.search(query=query, num_results=5, provider="naver")
            return ("naver", query, results, None)
        except Exception as e:
            return ("naver", query, [], str(e))
    
    def search_duckduckgo(query: str) -> tuple:
        """DuckDuckGo 검색"""
        try:
            from langchain_community.tools import DuckDuckGoSearchRun
            ddg = DuckDuckGoSearchRun()
            result = ddg.run(query)
            return ("duckduckgo", query, result, None)
        except Exception as e:
            return ("duckduckgo", query, "", str(e))
    
    # 병렬 검색 실행
    with ThreadPoolExecutor(max_workers=min(len(need_web) * 2, 10)) as executor:
        futures = []
        
        for query in need_web:
            # 각 쿼리에 대해 여러 소스 검색
            futures.append(executor.submit(search_naver_api, query))
            futures.append(executor.submit(search_duckduckgo, query))
        
        # 결과 수집
        for future in as_completed(futures):
            try:
                source_type, query, result, error = future.result()
                
                if error:
                    print(f"   [WARN] {source_type} 검색 실패 ({query[:30]}...): {error}")
                    continue
                
                if source_type == "naver":
                    if result:
                        naver_results.extend(result)
                        if query not in all_results:
                            all_results[query] = []
                        all_results[query].extend([
                            f"{i+1}. {r.title}\n   {r.link}\n   {r.snippet[:200]}..."
                            for i, r in enumerate(result)
                        ])
                        print(f"   [OK] Naver 검색 성공 ({query[:30]}...): {len(result)}개")
                
                elif source_type == "duckduckgo":
                    if result:
                        duckduckgo_results.append((query, result))
                        if query not in all_results:
                            all_results[query] = []
                        all_results[query].append(f"[DuckDuckGo] {result[:500]}")
                        print(f"   [OK] DuckDuckGo 검색 성공 ({query[:30]}...)")
            
            except Exception as e:
                print(f"   [ERROR] 검색 결과 처리 실패: {e}")
    
    # 결과 통합 및 중복 제거
    web_results = {}
    for query in need_web:
        if query in all_results:
            # 중복 제거 (간단한 방법: 제목 기준)
            seen_titles = set()
            unique_results = []
            for result_text in all_results[query]:
                # 제목 추출 시도
                lines = result_text.split("\n")
                title = lines[0] if lines else ""
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    unique_results.append(result_text)
                elif not title:
                    unique_results.append(result_text)
            
            web_results[query] = "\n".join(unique_results[:10])  # 최대 10개
        else:
            web_results[query] = "검색 결과 없음"
    
    # 상태 업데이트
    state["naver_results"] = naver_results
    state["web_results"] = web_results
    
    elapsed_time = time.time() - start_time
    print(f"\n[OK] 다중 검색 소스 통합 완료")
    print(f"   Naver 결과: {len(naver_results)}개")
    print(f"   DuckDuckGo 결과: {len(duckduckgo_results)}개")
    print(f"   통합된 쿼리 수: {len(web_results)}개")
    print(f"   소요 시간: {elapsed_time:.2f}초")
    print("="*80 + "\n")
    
    return state


