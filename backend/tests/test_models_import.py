def test_phase1_models_import():
    from app.models.resume_document import ResumeDocument, ResumeVersion
    from app.models.resume_evaluation_v2 import ResumeEvaluationV2
    from app.models.jd_evaluation import JDEvaluation
    from app.models.credit_ledger import CreditLedger
    assert ResumeDocument.__tablename__ == "resume_documents"
    assert ResumeVersion.__tablename__ == "resume_versions"
    assert ResumeEvaluationV2.__tablename__ == "resume_evaluations_v2"
    assert JDEvaluation.__tablename__ == "jd_evaluations"
    assert CreditLedger.__tablename__ == "credit_ledger"
