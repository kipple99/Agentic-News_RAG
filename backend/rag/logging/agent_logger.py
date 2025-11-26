"""
Agent 실행 로깅 시스템
"""

import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class AgentLogger:
    """
    Agent 실행 로깅 클래스
    """
    
    def __init__(
        self,
        log_dir: str = "logs",
        log_level: int = logging.INFO,
        enable_file_logging: bool = True,
        enable_console_logging: bool = True
    ):
        """
        Args:
            log_dir: 로그 파일 저장 디렉토리
            log_level: 로그 레벨
            enable_file_logging: 파일 로깅 활성화
            enable_console_logging: 콘솔 로깅 활성화
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 로거 생성
        self.logger = logging.getLogger("AgentLogger")
        self.logger.setLevel(log_level)
        
        # 기존 핸들러 제거
        self.logger.handlers.clear()
        
        # 포맷터 설정
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 콘솔 핸들러
        if enable_console_logging:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 파일 핸들러
        if enable_file_logging:
            log_file = self.log_dir / f"agent_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def log_query_start(self, query: str, session_id: Optional[str] = None):
        """쿼리 시작 로깅"""
        self.logger.info(f"[QUERY START] Session: {session_id}, Query: {query}")
    
    def log_query_end(
        self,
        query: str,
        answer: str,
        execution_time: float,
        session_id: Optional[str] = None,
        stats: Optional[Dict[str, Any]] = None
    ):
        """쿼리 종료 로깅"""
        stats_str = f", Stats: {stats}" if stats else ""
        self.logger.info(
            f"[QUERY END] Session: {session_id}, Query: {query[:50]}..., "
            f"Time: {execution_time:.2f}s, Answer Length: {len(answer)}{stats_str}"
        )
    
    def log_node_execution(
        self,
        node_name: str,
        query: str,
        execution_time: float,
        details: Optional[Dict[str, Any]] = None
    ):
        """노드 실행 로깅"""
        details_str = f", Details: {details}" if details else ""
        self.logger.info(
            f"[NODE] {node_name}, Query: {query[:50]}..., "
            f"Time: {execution_time:.2f}s{details_str}"
        )
    
    def log_search_results(
        self,
        search_type: str,
        query: str,
        result_count: int,
        execution_time: float
    ):
        """검색 결과 로깅"""
        self.logger.info(
            f"[SEARCH] Type: {search_type}, Query: {query[:50]}..., "
            f"Results: {result_count}, Time: {execution_time:.2f}s"
        )
    
    def log_error(self, error: Exception, context: Optional[str] = None):
        """에러 로깅"""
        context_str = f", Context: {context}" if context else ""
        self.logger.error(f"[ERROR] {type(error).__name__}: {str(error)}{context_str}", exc_info=True)
    
    def log_warning(self, message: str, context: Optional[str] = None):
        """경고 로깅"""
        context_str = f", Context: {context}" if context else ""
        self.logger.warning(f"[WARN] {message}{context_str}")
    
    def log_decision(
        self,
        decision_type: str,
        query: str,
        decision: str,
        reasoning: Optional[str] = None
    ):
        """의사결정 로깅"""
        reasoning_str = f", Reasoning: {reasoning}" if reasoning else ""
        self.logger.info(
            f"[DECISION] Type: {decision_type}, Query: {query[:50]}..., "
            f"Decision: {decision}{reasoning_str}"
        )
    
    def log_cache_hit(self, query: str):
        """캐시 히트 로깅"""
        self.logger.debug(f"[CACHE HIT] Query: {query[:50]}...")
    
    def log_cache_miss(self, query: str):
        """캐시 미스 로깅"""
        self.logger.debug(f"[CACHE MISS] Query: {query[:50]}...")
    
    def log_metrics(self, metrics: Dict[str, Any]):
        """메트릭 로깅"""
        self.logger.info(f"[METRICS] {metrics}")


# 전역 로거 인스턴스
_global_logger: Optional[AgentLogger] = None


def get_logger(
    log_dir: str = "logs",
    log_level: int = logging.INFO,
    enable_file_logging: bool = True,
    enable_console_logging: bool = True
) -> AgentLogger:
    """
    전역 로거 인스턴스 반환 (싱글톤 패턴)
    
    Args:
        log_dir: 로그 파일 저장 디렉토리
        log_level: 로그 레벨
        enable_file_logging: 파일 로깅 활성화
        enable_console_logging: 콘솔 로깅 활성화
    
    Returns:
        AgentLogger 인스턴스
    """
    global _global_logger
    
    if _global_logger is None:
        _global_logger = AgentLogger(
            log_dir=log_dir,
            log_level=log_level,
            enable_file_logging=enable_file_logging,
            enable_console_logging=enable_console_logging
        )
    
    return _global_logger


