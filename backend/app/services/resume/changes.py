"""Pure resume-document transformations shared by resume and JD workflows."""

from app.schemas.resume_v2 import ChangeItem, ResumeDocumentJSON


def apply_changes(doc: ResumeDocumentJSON, changes: list[ChangeItem]) -> ResumeDocumentJSON:
    data = doc.model_dump()
    for change in changes:
        if change.type == "bullet_update" and change.bullet_id and change.new_text:
            for container in (data.get("experience", []), data.get("projects", [])):
                for entry in container:
                    for bullet in entry.get("bullets", []):
                        if bullet["id"] == change.bullet_id:
                            bullet["text"] = change.new_text
        elif change.type == "skills_reorder" and change.new_skills_order is not None:
            data["skills"]["hard"] = change.new_skills_order
        elif change.type == "summary_update" and change.new_summary is not None:
            data["summary"] = change.new_summary
    return ResumeDocumentJSON.model_validate(data)


def find_bullet_text(doc: ResumeDocumentJSON, bullet_id: str) -> str | None:
    for item in [*doc.experience, *doc.projects]:
        for bullet in item.bullets:
            if bullet.id == bullet_id:
                return bullet.text
    return None
