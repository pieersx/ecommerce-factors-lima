class RecommendationAgent:
    def generate(self, factors: list[dict]) -> list[dict]:
        return [
            {
                "factor_id": factor["id"],
                "factor": factor["name"],
                "dimension": factor["dimension"],
                "status": factor["status"],
                "recommendation": factor["recommendation"],
            }
            for factor in factors
            if factor["status"] != "present"
        ]
