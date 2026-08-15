"""Persistence operations for JD evaluations."""

from sqlalchemy.orm import Session

from app.models.jd_evaluation import JDEvaluation


class JDEvaluationRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_owned(self, evaluation_id: str, user_id: str) -> JDEvaluation | None:
        row = self.session.get(JDEvaluation, evaluation_id)
        return row if row and row.user_id == user_id else None

    def get(self, evaluation_id: str | None) -> JDEvaluation | None:
        return self.session.get(JDEvaluation, evaluation_id) if evaluation_id else None

    def add(self, evaluation: JDEvaluation) -> None:
        self.session.add(evaluation)
