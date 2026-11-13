"""Print the offline schema bundle with python -m app.schemas.career."""

import argparse
import json

from . import career_json_schema


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("contract", nargs="?", help="named contract to validate, for example CareerEvidenceItem")
    args = parser.parse_args()
    try:
        schema = career_json_schema(args.contract)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(schema, indent=2, sort_keys=True))
