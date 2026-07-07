"""STUB — Person B owns this file (Singleton telemetry).

Minimal in-memory singleton so the LLM layer can record token usage today.
B: extend with per-agent latency, call counts, and reporting.
"""


class SystemMetrics:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.events = []
        return cls._instance

    def record(self, component: str, **fields) -> None:
        self.events.append({"component": component, **fields})
