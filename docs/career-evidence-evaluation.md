# Career Evidence evaluation baseline

From `backend/`, run:

```sh
python -m app.evaluation.career tests/fixtures/career_eval/suite.json tests/fixtures/career_eval/observations.json
```

The two versioned files separate the expected behavior from recorded candidate
outputs. A future adapter can supply observations in the same shape. The runner
uses PRI-30 contracts and deterministic checks. The report includes case IDs,
failure codes, and SHA-256 hashes of the inputs, runner, contract definitions,
and release manifest. The release manifest identifies the adapter and model
along with the recorder’s prompt and schema digests. The report separately
hashes the contract used by the replay grader. These fields record provenance
without proving that a particular provider produced the outputs. Exit codes are 0 for a passing
suite, 1 for a grading failure, and 2 for invalid input. CI runs the same command.

The experienced-candidate case spans project intake and a later application.
It checks that the later bullet uses the confirmed API and tests, cites the
current revisions, leaves out the teammate's UI and unmeasured estimate, and
keeps the job description's Kubernetes requirement separate from the
candidate's experience. The student case checks rejection of an invented
number and selection of the safe bullet. Its fairness pair changes a synthetic
university label and checks that the recorded decisions stay equivalent.

This baseline grades recorded traces. It exercises neither a live model nor
persistence across real sessions. In the synthetic cases, approved and invalid
wording are reviewed fixture strings. Different wording can be added after
human review. The runner does not infer semantic support from arbitrary prose.
The fixture checks cover a specific fairness counterfactual and source trust
boundary. Runtime privacy, ownership, model behavior, and broader fairness need
their own evaluation when the production components exist.

Keep public regression fixtures entirely synthetic. For a release holdout,
keep a separate access-controlled synthetic suite and expected results outside
Git. Restrict them to evaluation owners and reviewers. Keep them out of
prompts, tuning data, and ordinary CI. Run the same runner on an isolated
review machine with separately recorded observations. Share aggregate outcomes
and approved identifiers or hashes. Do not publish held-out questions or
expected results. If a case is exposed during debugging, move it into the public
regression suite and replace it in the holdout. This branch does not introduce a
private dataset or a live provider dependency.
