"""
쿼리 결과 캐싱 시스템
"""

import hashlib
import json
import time
from typing import Dict, Any, Optional
from functools import lru_cache


class QueryCache:
    """
    쿼리 결과 캐싱 클래스
    LRU (Least Recently Used) 방식으로 동작
    """
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        Args:
            max_size: 최대 캐시 항목 수
            ttl: Time To Live (초 단위, 기본 1시간)
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
    
    def _generate_key(self, query: str, context: Dict[str, Any] = None) -> str:
        """
        캐시 키 생성
        
        Args:
            query: 사용자 쿼리
            context: 추가 컨텍스트 (선택)
        
        Returns:
            MD5 해시된 캐시 키
        """
        key_data = {
            "query": query.lower().strip(),
            "context": context or {}
        }
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def get(self, query: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """
        캐시에서 조회
        
        Args:
            query: 사용자 쿼리
            context: 추가 컨텍스트
        
        Returns:
            캐시된 결과 또는 None
        """
        key = self._generate_key(query, context)
        
        if key not in self.cache:
            self.misses += 1
            return None
        
        cached_item = self.cache[key]
        
        # TTL 확인
        if time.time() - cached_item["timestamp"] > self.ttl:
            # 만료된 항목 제거
            del self.cache[key]
            self.misses += 1
            return None
        
        # 캐시 히트
        self.hits += 1
        cached_item["access_count"] = cached_item.get("access_count", 0) + 1
        cached_item["last_accessed"] = time.time()
        
        return cached_item["result"]
    
    def set(self, query: str, result: Dict[str, Any], context: Dict[str, Any] = None):
        """
        캐시에 저장
        
        Args:
            query: 사용자 쿼리
            result: 저장할 결과
            context: 추가 컨텍스트
        """
        key = self._generate_key(query, context)
        
        # 캐시 크기 제한
        if len(self.cache) >= self.max_size:
            # LRU: 가장 오래 접근하지 않은 항목 제거
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k].get("last_accessed", self.cache[k]["timestamp"])
            )
            del self.cache[oldest_key]
        
        self.cache[key] = {
            "result": result,
            "timestamp": time.time(),
            "last_accessed": time.time(),
            "access_count": 1,
            "query": query
        }
    
    def clear(self):
        """캐시 전체 삭제"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """캐시 통계 반환"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "ttl": self.ttl
        }
    
    def remove_expired(self):
        """만료된 항목 제거"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.cache.items()
            if current_time - item["timestamp"] > self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)


# 전역 캐시 인스턴스
_global_cache: Optional[QueryCache] = None


def get_cache(max_size: int = 1000, ttl: int = 3600) -> QueryCache:
    """
    전역 캐시 인스턴스 반환 (싱글톤 패턴)
    
    Args:
        max_size: 최대 캐시 항목 수
        ttl: Time To Live (초)
    
    Returns:
        QueryCache 인스턴스
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = QueryCache(max_size=max_size, ttl=ttl)
    
    return _global_cache


def clear_cache():
    """전역 캐시 초기화"""
    global _global_cache
    if _global_cache:
        _global_cache.clear()


