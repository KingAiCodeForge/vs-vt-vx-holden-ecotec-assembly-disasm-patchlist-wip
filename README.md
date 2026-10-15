# Holden VS/VT/VX Ecotec 68HC11 Reverse Engineering

Work in progress for the Delco PCM used with Holden L36 and L67 Ecotec
engines. The project is intended to document factory code, import TunerPro XDF
labels into Ghidra, and develop patch manifests that can be reviewed byte by
byte.

Nothing in this repository is ready to flash.

## Target Order

| Priority | Platform | Calibration | Current purpose |
|---:|---|---|---|
| 1 | VS L36 | `$51` Enhanced v1.4g | Primary disassembly and labelling target |
| 2 | VS L67 | `$51` Enhanced v1.0d | Supercharged comparison |
| 3 | VT L36 | `$A5G` Enhanced v1.0i | Later-generation comparison |
| 4 | VT L67 | `$A5G` Enhanced v1.3i | Supercharged comparison |
| 5 | VX/VY L36 | `$060A` Enhanced v1.0a | Reference with the Antus v2.09b XDF against existing VY research |
| 6 | VX/VY L67 | `$07` Enhanced v2.6i | Supercharged reference |

Each calibration is a separate reverse-engineering target. Similar table names
do not prove that code addresses, RAM locations, bank layouts, or patch hooks
are portable between them.

For the VX/VY L36 reference, `v1.0a` is the 131,072-byte executable calibration
revision and `v2.09b` is the matching Antus XDF revision. The exact v1.0a source
used by the existing VY work has SHA-256
`5cb8bd1c61da37a3846b6c28600cdc21db3ceef0c764232d0cd7ec8d6e836abd`.

## Current State

This first public revision contains the project boundary and license only. The
working disassemblies, scripts, XDF copies, PCM binaries, logs, and generated
Ghidra projects remain local while they are reviewed.

No patch binary, tune, or claimed working hook is published here. In
particular, there is no tested ghost-cam, spark-cut, limiter, launch-control,
anti-lag, or boosted calibration.

## Evidence Standard

A future patch will not be marked as validated until it has:

1. An exact source file identity and SHA-256 hash.
2. Verified original bytes at every modified offset.
3. Proven CPU address, file offset, and bank or alias relationship.
4. A bounded byte diff and reproducible checksum repair.
5. A documented call path showing that the hook is reached as intended.
6. A recoverable bench write and full readback comparison.
7. Scope or logger evidence for the affected input or output.
8. Vehicle testing with a documented rollback path.

Static disassembly can support the first five items. It cannot establish the
last three by itself.

## Planned Public Layout

```text
asm_patch_formats/  Reviewed manifest and assembly formats
config/             Target metadata without copyrighted binaries
docs/               Source-backed reverse-engineering notes
patchlists/         Target-specific patch status
tools/              Reproducible labelling and verification scripts
```

Local binaries, XDF/ADX archives, logs, scraped forum material, generated
reports, and Ghidra projects are deliberately excluded.

## Sources and Credits

- [PCMHacking VS-VY Enhanced Factory Bins thread](https://pcmhacking.net/forums/viewtopic.php?f=27&t=2518)
- [PCMHacking Holden XDF index](https://pcmhacking.net/forums/viewtopic.php?t=5)
- The1 and Antus for the Enhanced definitions and published PCM research
- The PCMHacking community for accumulated Delco and 68HC11 knowledge
- The existing
  [VY V6 assembly research](https://github.com/KingAiCodeForge/kingaustraliagg-vy-l36-060a-enhanced-asm-patches)
  used as a comparison, not as proof that VY addresses apply to VS or VT

Third-party files retain their original ownership and licenses. They are not
redistributed by this initial revision.

## License

Original material in this repository is available under the [MIT License](LICENSE).
