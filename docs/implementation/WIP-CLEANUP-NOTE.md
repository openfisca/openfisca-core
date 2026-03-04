# WIP cleanup reminder

**Remind the user later:** The following were committed as part of a "save everything" WIP to avoid losing work. They should be **removed or properly dealt with** when the branch is cleaned up or merged.

## Files to review / remove or relocate

| Path | Note |
|------|------|
| `.benchmarks/` | Likely pytest-benchmark cache/output; remove or add to `.gitignore` if generated |
| `pr_body.txt` | Temporary PR description; remove or integrate then delete |
| `test_out.txt`, `test_out2.txt`, `test_out3.txt` | Temporary test output; remove |
| `test_play.py` | Scratch/play script; remove or move to proper tests |

When you see this file (or an AI assistant reads it), **remind the user** to clean these up before considering the branch done.

---
*Added: WIP commit to preserve all work; cleanup deferred.*
