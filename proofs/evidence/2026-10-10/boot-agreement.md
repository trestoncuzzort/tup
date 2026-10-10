# t cross-kernel agreement, 2026-10-10 12:02Z

Cell = real outcome / twin outcome. Agreement means `verified / refuted` in every present column. A real-VERIFIED, twin-VERIFIED cell reads `verified / decorative` (the spec cannot tell real and twin apart) or `verified / unsound` (the twin's own measured witness says a sound kernel must refute it, and this one did not); neither counts as agreement.

| task | dafny | lean |
|---|---|---|
| boot_accept | verified / refuted | verified / refuted |

Kernels present: 2 of 2 (dafny, lean)

Backends:
- dafny: dafny 4.11.0+fcb2042d6d043a2634f0854338c08feeaaaf4ae2
- lean: Lean (version 4.33.1

Verdict basis: every source file hashed.

## Sole blockers

| kernel | sole blocker of | co-blocker of | tasks it alone keeps out of all two |
|---|---|---|---|
| dafny | 0 | 0 | (none) |
| lean | 0 | 0 | (none) |

Of the 0 tasks in one, none are blocked alone.

## Per kernel

| kernel | carried | real verified | twin refuted where the real is verified | abstains by name |
|---|---|---|---|---|
| dafny | 1 | 1 | 1 of 1 (100%) | 0 |
| lean | 1 | 1 | 1 of 1 (100%) | 0 |

Verified with the twin refuted in all two columns: 1 of 1 tasks.
