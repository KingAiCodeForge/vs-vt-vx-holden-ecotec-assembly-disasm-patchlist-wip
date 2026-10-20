# Public source review — 20 October 2026

This alpha admits one generic metadata diff helper after source review and
synthetic tests. No compiler, disassembler, patch builder, firmware, XDF,
executable calibration or hardware qualification is included.

## Reviewed baseline and preservation

The public `main` baseline was `04b2dab4699011298f6e1b02298c7d910834566a`.
Its complete tracked tree contains only `.gitignore`, `LICENSE` and `README.md`.
There were no public pull requests, scripts or release artifacts to execute.
All original public refs were retained and a complete Git bundle was verified
before editing an isolated clone. The existing local checkout was left intact.

The repository MIT license covers original material. It does not establish
ownership or redistribution rights for every ignored local file.

## Local script intake held

A read-only inventory confirmed that an existing local checkout has this exact
public repository as its remote. Four ignored helper files were then read as
source. None was executed against firmware. Only the generic first-party diff
helper was adapted into this release, after preserving and hashing its original.
No private repository implementation or factory data was inspected.

| Local candidate | Actual interface and purpose | Observed coverage and defects | Decision |
|---|---|---|---|
| `tools/hc11_decode.py` | Python `decode_one`, `decode_run`, `is_reachable_reference`; instruction lengths and reference heuristics; no CLI | Local test module below. Negative offsets are accepted by Python indexing; out-of-range offsets raise incidental exceptions; CPU-relative results do not wrap to 16 bits. `decode_run` documents a hard stop but never uses `FLOW_STOP`. Claimed complete opcode accuracy has not been independently qualified. Convergence is a boundary heuristic, not control-flow reachability. | Held: correctness, bounds and provenance review required. |
| `tools/test_hc11_decode.py` | `unittest` script; representative opcode/length assertions plus image-dependent routine and convergence tests | Some synthetic vectors, but routine/convergence classes read an excluded local BIN without an explicit optional fixture contract. The suite cannot run from the public checkout. No test run or opcode qualification is claimed here. | Held with its original decoder. Replace image dependencies with lawful synthetic fixtures before promotion. |
| `tools/vs_vt_vx_addressing.py` | Python bank-window, offset/CPU-alias, range and program-name helpers; no CLI | No coverage identified in the inspected file. Shared constants assume a 128 KiB three-window layout across named platforms. Unknown banks silently receive a full address range; bank detection uses a substring and ambiguous fallback. No exact-image identity gate or strict integer bounds. | Held: target-specific evidence/adapters and fail-closed validation required. Constants are not public target qualification. |
| `tools/bin_diff_report.py` | Positional `original modified`; optional hash, JSON/Markdown output, size rejection; metadata diff only | Original source had no accompanying tests inspected. Outputs could overwrite inputs or each other and hash/size rejection followed publication. Invalid hashes/missing inputs lacked deliberate diagnostics. Reads/ranges were unbounded and reports exposed paths/bytes. | Promoted as a thin adapter to the shared `holden_wip.binary_diff` core after fixing these defects and adding synthetic tests. No target-specific mapping is inferred. |

None of these four files has an author/license notice in its inspected header.
The local source-asset manifest separately identifies the diff and addressing
helpers as added in this repository, rather than copied upstream. Together with
the owner's public-source promotion instruction and this project's MIT grant
for original material, that supports promotion of the generic diff helper.
It contains no embedded firmware, target addresses or external dependencies.
Its preserved original SHA-256 is
`f5ca7d4d02ef27da77bce828c55f7a01e0bf43407575d4965feeab342fd4ddbb`.
The local manifest itself is not redistributed because it includes local paths
and third-party staging details. The decoder's provenance remains unverified;
the addressing helper remains unqualified for correctness even though its local
manifest identifies it as added here. Every original file remains untouched.

The [per-file ledger](script-review-ledger.json) inventories 75 local candidate
sources: four inspected and 71 **not individually reviewed or qualified**.
All 74 unpromoted candidates remain local. The three new core/package/test
modules are recorded separately. A filename/hash inventory is not source review.

## Public additions

`config/targets.json` transcribes the six target descriptions already in the
public README. Unknown exact image sizes/hashes remain null; no target identity
is inferred from a similar calibration name. The VX/VY L36 reference preserves
the already-public 131,072-byte v1.0a identity and separates its v2.09b XDF
revision. This metadata does not verify bank mappings, hooks or patch safety.

The ignore policy continues to deny unreviewed source, local firmware, XDF/ADX,
Ghidra projects, machine settings, private notes and generated output. Only the
specific reviewed source/test/package files, documentation and metadata are
newly admitted. There is one implementation core; the compatibility script
delegates to it instead of duplicating it. No target adapter is published.

## Verification and remaining work

Checks parse the metadata, require six distinct target IDs, preserve the public
baseline files, and exercise Git ignore decisions for each admitted file and
representative protected files. Synthetic tests exercise hash/size rejection,
range and input bounds, API types, private detail defaults, missing inputs,
overwrite/alias protection, failed-output cleanup and import behavior.
The installed wheel passed **17 synthetic tests**, including a Windows
hard-link alias check, in a clean Windows Python 3.13 environment and a working
directory with spaces. The installed console command and compatibility adapter
also passed help and synthetic input/output smoke checks outside the checkout.
An independent enumeration checked 961 short binary pairs against exact changed
positions. Other platforms/runtimes remain pending CI evidence; see the release
receipt for exact commands, source/artifact hashes and any later results.

PR #1's GitHub Actions jobs did not start: the account is locked by a billing
issue. These are infrastructure failures, not passing or failing software tests.
No billing setting was changed and no paid service was enabled. This alpha's
measured platform qualification is Windows/Python 3.13; Linux and the other
declared syntax-compatible Python versions remain unverified.

Cleanup deliberately preserves a path when the filesystem cannot establish
file identity; the error identifies that leftover for inspection. A process or
power failure can also leave a partial report. No filesystem transaction is
claimed.

Future source promotion follows [SOURCE_INTAKE.md](SOURCE_INTAKE.md). Each tool
needs an individual source/rights record, portable API/CLI, meaningful synthetic
tests and clean-install checks before its ignore exception is introduced.

No hardware, flash, ECU connection or factory-binary processing occurred in
this review. Static source review cannot satisfy physical validation gates.
