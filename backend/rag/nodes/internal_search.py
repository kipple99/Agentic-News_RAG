"""
Internal DB Search 노드
Elasticsearch에서 Hybrid Search를 수행합니다.
"""

import sys
import os
from typing import Dict, Any, Optional
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from rag.agent_state import AgentState
from search.es_client import search_multiple_queries


def search_internal_db(
    state: AgentState,
    es_client: Optional[Elasticsearch],
    es_index: str,
    embedder: Optional[SentenceTransformer]
) -> AgentState:
    """
    내부 DB 검색 노드
    
    - Elasticsearch Hybrid Search 실행
    - BM25 + Dense Vector 검색
    - RRF Fusion
    
    Args:
        state: 현재 상태
        es_client: Elasticsearch 클라이언트
        es_index: 인덱스 이름
        embedder: 임베딩 모델
    
    Returns:
        es_results가 추가된 상태
    """
    import time
    start_time = time.time()
    
    print("\n" + "="*80)
    print("[2단계] INTERNAL DB SEARCH - 내부 DB 검색 시작")
    print("="*80)
    
    query_analysis = state.get("query_analysis", {})
    sub_queries = query_analysis.get("sub_queries", [state["user_query"]])
    
    print(f"검색할 서브쿼리 수: {len(sub_queries)}")
    for i, q in enumerate(sub_queries, 1):
        print(f"   {i}. {q}")
    print(f"Elasticsearch 인덱스: {es_index}")
    
    # ES 클라이언트 확인
    if es_client is None:
        print(f"[WARN] Elasticsearch가 연결되지 않았습니다. 내부 DB 검색을 건너뜁니다.")
        print(f"   -> 웹 검색으로 진행합니다.")
        state["es_results"] = {
            "queries": {},
            "total": 0
        }
        elapsed_time = time.time() - start_time
        print(f"소요 시간: {elapsed_time:.2f}초")
        print("="*80 + "\n")
        return state
    
    # 여러 쿼리에 대해 검색 수행
    try:
        print(f"[INFO] Hybrid Search 실행 중... (BM25 + Dense Vector + RRF)")
        all_results = search_multiple_queries(
            es_client=es_client,
            es_index=es_index,
            queries=sub_queries,
            embedder=embedder,
            size=10
        )
        
        # 전체 결과 통합
        total_hits = sum(
            res.get("hits", {}).get("total", {}).get("value", 0)
            for res in all_results.values()
        )
        
        print(f"[OK] 검색 완료")
        print(f"   총 검색 결과 수: {total_hits}개")
        
        # 각 쿼리별 결과 요약
        for q, res in all_results.items():
            hits_count = res.get("hits", {}).get("total", {}).get("value", 0)
            top_score = 0.0
            if res.get("hits", {}).get("hits"):
                top_score = res["hits"]["hits"][0].get("_score", 0.0)
            print(f"   '{q[:50]}...': {hits_count}개 결과, 최고 점수: {top_score:.4f}")
        
        state["es_results"] = {
            "queries": all_results,
            "total": total_hits
        }
        
    except Exception as e:
        print(f"[ERROR] 내부 DB 검색 실패: {e}")
        import traceback
        traceback.print_exc()
        state["es_results"] = {
            "queries": {},
            "total": 0
        }
        print(f"[WARN] 빈 결과 반환")
    
    elapsed_time = time.time() - start_time
    print(f"소요 시간: {elapsed_time:.2f}초")
    print("="*80 + "\n")
    
    return state

