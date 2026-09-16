"""Load the project's shared contract interface; no independent field aliases here."""
import sys
from pathlib import Path
for _root in Path(__file__).resolve().parents:
    if (_root / "contracts/pipeline_contracts.py").is_file():
        sys.path.insert(0, str(_root / "contracts"))
        break
else:
    raise ImportError("Project contracts/pipeline_contracts.py is required")
from pipeline_contracts import (load_contract, product_path, publish_payload,
                                archive_fingerprint, relative, sha256)
