"""Brechas priorizadas sin ponderaciones ocultas."""


class GapPrioritizationAgent:
    def prioritize(self, factors: list[dict]) -> list[dict]:
        rank = {"absent": 0, "not_evaluable": 1, "partial": 2, "present": 3}
        gaps = [factor.copy() for factor in factors if factor["status"] != "present"]
        for item in gaps:
            item["priority"] = "Alta" if item["status"] == "absent" else "Media"
        return sorted(gaps, key=lambda item: (rank[item["status"]], item["dimension"], item["name"]))
