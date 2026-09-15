"""Model IDs and claimed originals cannot choose their own validation evidence."""

import pytest

from app.core.openai_client import ModelRuntime
from app.schemas.jd import BulletDiff, BulletOption
from app.services.jd.tailor import generate_bullet_options, tailor_resume_to_jd
from app.services.resume.hallucination_guard import HallucinationError
from tests.core.test_model_manifests import fake_provider, jd_fixture, plan_fixture, response
from tests.fixtures.resume_doc_json import make_resume


def provider(diff, *, options=False):
    plan = plan_fixture()
    plan.bullets = [diff]
    client, call = fake_provider(response(parsed=diff if options else plan))
    return ModelRuntime(client_factory=lambda: client), call


@pytest.mark.asyncio
async def test_unknown_id_cannot_validate_against_its_own_fabricated_old():
    runtime, call = provider(BulletDiff(
        bullet_id="private-unknown-id", old="Shipped to 9000 users",
        new="Shipped to 9000 users", reason="private-reason",
    ))
    with pytest.raises(HallucinationError):
        await tailor_resume_to_jd(make_resume(), jd_fixture(), runtime=runtime)
    call.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("section", ["experience", "projects"])
async def test_returned_old_and_truth_evidence_are_canonical(section):
    doc = make_resume()
    bullet = getattr(doc, section)[0].bullets[0]
    runtime, call = provider(BulletDiff(
        bullet_id=bullet.id, old="Fabricated claimed source", new=bullet.text, reason="Safe",
    ))
    plan = await tailor_resume_to_jd(doc, jd_fixture(), runtime=runtime)
    diff = plan.bullets[0]
    assert diff.old == bullet.text
    assert diff.truth_check.source_evidence == [bullet.text]
    assert diff.options[0].truth_check.source_evidence == [bullet.text]
    call.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("section", ["experience", "projects"])
@pytest.mark.parametrize("options", [False, True])
async def test_each_alternative_uses_stored_source_not_claimed_old(section, options):
    doc = make_resume()
    bullet = getattr(doc, section)[0].bullets[0]
    fabricated = "Shipped to 9000 users"
    runtime, call = provider(BulletDiff(
        bullet_id=bullet.id, old=fabricated, new=bullet.text, reason="Safe main text",
        options=[BulletOption(option_id="impact", text=fabricated, reason="Unsafe alternative")],
    ), options=options)
    with pytest.raises(HallucinationError):
        if options:
            await generate_bullet_options(doc=doc, jd=jd_fixture(), bullet_id=bullet.id,
                                          original=bullet.text, runtime=runtime)
        else:
            await tailor_resume_to_jd(doc, jd_fixture(), runtime=runtime)
    call.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("returned_id", ["unknown", "b2", "p1"])
async def test_options_reject_mismatched_response_id(returned_id):
    doc = make_resume()
    original = doc.experience[0].bullets[0].text
    runtime, call = provider(BulletDiff(
        bullet_id=returned_id, old=original, new=original, reason="Wrong target",
    ), options=True)
    with pytest.raises(HallucinationError):
        await generate_bullet_options(doc=doc, jd=jd_fixture(), bullet_id="b1",
                                      original=original, runtime=runtime)
    call.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", ["unknown_id", "wrong_original", "ambiguous_source"])
async def test_options_reject_invalid_source_before_provider_call(invalid):
    doc = make_resume()
    original = doc.experience[0].bullets[0].text
    if invalid == "ambiguous_source":
        doc.projects[0].bullets[0].id = "b1"
    runtime, call = provider(BulletDiff(bullet_id="b1", old=original, new=original, reason="Safe"), options=True)
    with pytest.raises(HallucinationError):
        await generate_bullet_options(
            doc=doc, jd=jd_fixture(), bullet_id="unknown" if invalid == "unknown_id" else "b1",
            original="Fabricated source" if invalid == "wrong_original" else original, runtime=runtime,
        )
    call.assert_not_awaited()


@pytest.mark.asyncio
async def test_tailor_rejects_ambiguous_source_ids_before_provider_call():
    doc = make_resume()
    doc.projects[0].bullets[0].id = "b1"
    runtime, call = provider(BulletDiff(bullet_id="b1", old="500+ GitHub stars.",
                                      new="500+ GitHub stars.", reason="Ambiguous"))
    with pytest.raises(HallucinationError):
        await tailor_resume_to_jd(doc, jd_fixture(), runtime=runtime)
    call.assert_not_awaited()
