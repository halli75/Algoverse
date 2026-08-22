"""Locked METHOD cell for method_compare.ipynb.

Default is CORE_METHOD. The old coeff=20 / late / last-token encoding is
`obsolete_dry_run`, not "Arnav current". Arnav's current science already uses
norm-scaled steering and a fractional gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from affect_core import ALPHA_REF, CORE_METHOD, NAMED_VARIANTS, core_pin, gate_window

METHODS = {
    "core": dict(CORE_METHOD),
    "charlotte": dict(CORE_METHOD),  # same method; [8,20) is recovered at L=34
    "obsolete_dry_run": dict(layers="late", proj="last", steer="coeff", coeff=20.0),
}

METHOD_NAME = "core"
METHOD = dict(METHODS[METHOD_NAME])

# Historical rows for a reproduction section titled obsolete_dry_run_reproduction:
OBSOLETE_DRY_RUN_REPRODUCTION = {
    "charlotte_historical": dict(layers="gate", proj="mean", steer="normscaled", alpha=0.008),
    "arnav_obsolete_dry_run": dict(layers="late", proj="last", steer="coeff", coeff=20.0),
}

PIN = core_pin()
VARIANTS = dict(NAMED_VARIANTS)

if __name__ == "__main__":
    print("METHOD_NAME", METHOD_NAME)
    print("METHOD", METHOD)
    print("ALPHA_REF", ALPHA_REF)
    print("pin", PIN["sha256"][:16])
    print("L34 window", gate_window(34)[0], gate_window(34)[-1] + 1)
