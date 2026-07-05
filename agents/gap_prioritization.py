"""Brechas priorizadas por impacto operativo observable."""

from agents.recommendations import GROUP_ORDER, IMPACT_GROUPS, STATUS_ORDER


class GapPrioritizationAgent:
    def prioritize(self, factors: list[dict]) -> list[dict]:
        gaps = [factor.copy() for factor in factors if factor["status"] != "present"]
        for item in gaps:
            group, reason = IMPACT_GROUPS.get(item["id"], ("Otros", "Factor complementario de madurez e-commerce."))
            item["impact_group"] = group
            item["reason"] = reason
            item["priority"] = "Alta" if group in {"Compra", "Confianza"} and item["status"] == "absent" else "Media"
            if item["status"] == "not_evaluable":
                item["priority"] = "Revision"
        return sorted(
            gaps,
            key=lambda item: (
                GROUP_ORDER.get(item["impact_group"], 9),
                STATUS_ORDER.get(item["status"], 9),
                item["id"],
            ),
        )
