"""Export the running application's contract; no database connection required."""
import json
import re
from pathlib import Path
from backend.app.main import app

ROOT = Path(__file__).resolve().parents[2]


def main():
    target = ROOT / "backend" / "openapi.json"
    target.write_text(json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source = (ROOT / "docs/architecture/api-contract.md").read_text(encoding="utf-8-sig")
    fence = chr(96) * 3
    examples = [json.loads(block) for block in re.findall(fence + r"json\s*\n(.*?)\n" + fence, source, re.S)]
    (ROOT / "backend" / "contract-examples.json").write_text(json.dumps(dict(zip(("error", "expected_strings", "upload_metadata", "screenshot"), examples)), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Exported {len(app.openapi()['paths'])} paths and four synthetic architecture examples")


if __name__ == "__main__":
    main()
