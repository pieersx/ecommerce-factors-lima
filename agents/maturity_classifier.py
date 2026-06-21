from agents.scoring_engine import classify_pec


class MaturityClassifier:
    def classify(self, score: float) -> str:
        return classify_pec(score)
