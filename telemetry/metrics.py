class SystemMetrics:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.calls = {}
            cls._instance.tokens = 0
            cls._instance.cost = 0.0
            cls._instance.events = []
        return cls._instance

    def record(self, component: str, tokens: int = 0, cost: float = 0.0, **fields):
        self.calls[component] = self.calls.get(component, 0) + 1
        self.tokens += tokens
        self.cost += cost
        self.events.append({"component": component, "tokens": tokens, **fields})

    # TODO(B): per-agent latency aggregation + a summary dict for D's /status route.
