#tructured JSON logging (structlog) + @log_asset decorator.

import functools
import logging
import time

import structlog

from etl.config import LOG_DIR

# 1. WHERE logs go: terminal (Dagster captures it) + logs/pipeline.log
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",          # structlog already builds the full JSON line
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_DIR / "pipeline.log")],
    force=True,
)

# 2. HOW logs look: each processor adds a field, the last one renders JSON
structlog.configure(
    processors=[
        structlog.stdlib.add_logger_name,                        
        structlog.stdlib.add_log_level,                         
        structlog.processors.TimeStamper(fmt="iso", utc=True),   
        structlog.processors.format_exc_info,                    
        structlog.processors.JSONRenderer(),                     
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
)

log = structlog.get_logger("etl")


# 3. The decorator: wraps an asset function with start / finish / failure logs
def log_asset(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        info = {"step": func.__name__}
        context = next((a for a in args if hasattr(a, "has_partition_key")), None)
        if context is not None and context.has_partition_key:
            info["month"] = context.partition_key[:7]

        log.info("step_started", **info)
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)                     
        except Exception as exc:
            log.exception("step_failed", error=str(exc), **info)
            raise                                              

        # row counts the asset returned
        metadata = {k: getattr(v, "value", v) for k, v in (result.metadata or {}).items()}
        log.info("step_finished", duration_s=round(time.perf_counter() - start, 2),
                 **metadata, **info)
        return result
    return wrapper