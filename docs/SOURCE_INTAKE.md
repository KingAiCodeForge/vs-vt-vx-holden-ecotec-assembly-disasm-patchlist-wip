# Source promotion contract

Promote one bounded, reviewed source change at a time. Keep the original local
file and its SHA-256 record; use an isolated checkout and preserve source refs.
Never use an existing dirty working directory as the integration workspace.

Before adding an ignored file, record:

1. Its origin, author, license and any upstream modifications. An unverified
   grant remains a hold; third-party notices and exclusions remain explicit.
2. Purpose, every CLI/API entry point, dependencies, supported runtime and
   import behavior. Import must not build patches, read firmware or write files.
3. Actual tests and defects, including unsupported or untested behaviors.
4. Exact target identity when target-specific: platform, L36/L67, calibration,
   source length and SHA-256, plus separately proven bank/address relations.
   A VS, VT, VX or VY name alone is insufficient; unknown identities remain
   unqualified. A donor address is never promoted as another target's address.
5. A data review: no credentials, customer/private data, proprietary firmware,
   scraped attachments, local machine configuration, absolute personal paths
   or embedded firmware byte excerpts without an explicit lawful source grant.

Before qualification, replace machine paths with arguments/configuration or
package resources. Reject missing dependencies/inputs with useful diagnostics;
validate types, integer bounds, target IDs and hash syntax. Protect inputs from
output aliases (including hard links/symlinks), avoid silent overwrites, and
validate all outputs before publishing any. Keep generated paths explicit and
reports deterministic where practical. Document paths/byte previews exposed
by reports so users can control their release.

Use synthetic, redistributable test data. Test negative inputs and boundaries,
import without side effects, a clean environment and working directories with
spaces. Check Windows paths and run any claimed supported platform in CI.
Publish exact limitations when a runtime/platform has not been exercised.

Review tracked deletions, ignores and local excludes before integration.
Admission of one file must not expose the rest of an ignored directory. Retain
secrets, firmware/data, machine configuration and generated-output protections.
Archive prototypes with an explicit unqualified status; do not present an old
static experiment as a recommended patch or flash artifact.

Merge qualified changes without forcing history, test the exact merged source,
then build and hash the release artifacts. State which scripts, tests and
platforms were actually checked. Software checks never establish bench or
vehicle qualification.
