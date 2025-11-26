"""
검색 결과 재순위화 노드
Cross-encoder를 사용하여 검색 결과를 재순위화합니다.
"""

import sys
import os
from typing import Dict, Any, Optional

# 상위 디렉토리 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.agent_state import AgentState


def rerank_search_results(
    state: AgentState,
    reranker_model: Optional[Any] = None
) -> AgentState:
    """
    검색 결과 재순위화 노드
    
    Cross-encoder 모델을 사용하여 ES 검색 결과를 재순위화합니다.
    
    Args:
        state: 현재 상태
        reranker_model: Cross-encoder 모델 (None이면 자동 로드)
    
    Returns:
        재순위화된 es_results가 포함된 상태
    """
    import time
    start_time = time.time()
    
    print("\n" + "="*80)
    print("[2-1단계] RERANK - 검색 결과 재순위화 시작")
    print("="*80)
    
    es_results = state.get("es_results", {})
    queries_results = es_results.get("queries", {})
    user_query = state["user_query"]
    
    if not queries_results:
        print("[INFO] 재순위화할 검색 결과가 없습니다.")
        print("="*80 + "\n")
        return state
    
    # Cross-encoder 모델 로드
    if reranker_model is None:
        try:
            from sentence_transformers import CrossEncoder
            print("[INFO] Cross-encoder 모델 로드 중...")
            reranker_model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            print("[OK] 모델 로드 완료")
        except ImportError:
            print("[WARN] sentence-transformers가 설치되지 않았습니다. 재순위화를 건너뜁니다.")
            print("="*80 + "\n")
            return state
        except Exception as e:
            print(f"[WARN] 모델 로드 실패: {e}. 재순위화를 건너뜁니다.")
            print("="*80 + "\n")
            return state
    
    reranked_results = {}
    total_reranked = 0
    
    # 각 쿼리별로 재순위화
    for query, result in queries_results.items():
        try:
            hits = result.get("hits", {}).get("hits", [])
            
            if not hits:
                reranked_results[query] = result
                continue
            
            print(f"[INFO] 쿼리 '{query[:50]}...' 재순위화 중... ({len(hits)}개 결과)")
            
            # 쿼리-문서 쌍 생성
            pairs = []
            for hit in hits:
                source = hit.get("_source", {})
                text = source.get("text", source.get("content", ""))
                if not text:
                    text = source.get("title", "")
                pairs.append((query, text[:512]))  # 최대 길이 제한
            
            # 재순위화 점수 계산
            if pairs:
                scores = reranker_model.predict(pairs)
                
                # 점수 기준으로 정렬
                reranked_hits = sorted(
                    zip(hits, scores),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                # 재순위화된 결과 생성
                reranked_hits_list = []
                for hit, score in reranked_hits:
                    # 원본 hit에 재순위화 점수 추가
                    hit_copy = hit.copy()
                    hit_copy["_rerank_score"] = float(score)
                    # 원본 점수는 유지하되, 재순위화 점수도 저장
                    reranked_hits_list.append(hit_copy)
                
                # 결과 업데이트
                result_copy = result.copy()
                result_copy["hits"]["hits"] = reranked_hits_list
                reranked_results[query] = result_copy
                
                total_reranked += len(reranked_hits_list)
                
                # 상위 3개 점수 출력
                print(f"   상위 3개 재순위화 점수:")
                for i, (hit, score) in enumerate(reranked_hits[:3], 1):
                    title = hit.get("_source", {}).get("title", "제목 없음")
                    print(f"      {i}. {title[:50]}... (점수: {score:.4f})")
            else:
                reranked_results[query] = result
        
        except Exception as e:
            print(f"[ERROR] 재순위화 실패 ({query}): {e}")
            import traceback
            traceback.print_exc()
            # 실패 시 원본 결과 사용
            reranked_results[query] = result
    
    # 재순위화된 결과로 업데이트
    es_results["queries"] = reranked_results
    state["es_results"] = es_results
    
    elapsed_time = time.time() - start_time
    print(f"[OK] 재순위화 완료")
    print(f"   재순위화된 결과 수: {total_reranked}개")
    print(f"   소요 시간: {elapsed_time:.2f}초")
    print("="*80 + "\n")
    
    return state


