import time
from typing import Dict, Tuple

_requests: Dict[str, int] = {}
_lat_total: Dict[str, float] = {}
_cache_hits: Dict[str, int] = {}
_cache_sets: Dict[str, int] = {}

def record(endpoint: str, duration_ms: int, status: int) -> None:
    key = f"{endpoint}|{status}"
    _requests[key] = _requests.get(key, 0) + 1
    _lat_total[endpoint] = _lat_total.get(endpoint, 0.0) + duration_ms

def render_metrics() -> str:
    lines = []
    lines.append("# HELP sureflights_requests_total Requests by endpoint and status")
    lines.append("# TYPE sureflights_requests_total counter")
    for key, count in _requests.items():
        ep, status = key.split("|")
        lines.append(f'sureflights_requests_total{{endpoint="{ep}",status="{status}"}} {count}')
    lines.append("# HELP sureflights_endpoint_latency_ms_total Total latency by endpoint (ms)")
    lines.append("# TYPE sureflights_endpoint_latency_ms_total counter")
    for ep, tot in _lat_total.items():
        lines.append(f'sureflights_endpoint_latency_ms_total{{endpoint="{ep}"}} {int(tot)}')
    # Cache metrics
    lines.append("# HELP sureflights_cache_hits_total Cache hits by name")
    lines.append("# TYPE sureflights_cache_hits_total counter")
    for name, cnt in _cache_hits.items():
        lines.append(f'sureflights_cache_hits_total{{name="{name}"}} {cnt}')
    lines.append("# HELP sureflights_cache_sets_total Cache sets by name")
    lines.append("# TYPE sureflights_cache_sets_total counter")
    for name, cnt in _cache_sets.items():
        lines.append(f'sureflights_cache_sets_total{{name="{name}"}} {cnt}')
    return "\n".join(lines) + "\n"

def record_cache_hit(name: str) -> None:
    _cache_hits[name] = _cache_hits.get(name, 0) + 1

def record_cache_set(name: str) -> None:
    _cache_sets[name] = _cache_sets.get(name, 0) + 1

