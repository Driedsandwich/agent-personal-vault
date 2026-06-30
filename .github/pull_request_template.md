# プルリクエストテンプレート

## Summary

Describe the change without including personal data.

## Safety Checklist

- [ ] I did not include real personal data, screenshots, vault files, local absolute paths, or raw logs.
- [ ] I ran `python3 scripts/check_release.py` or `make release-check`.
- [ ] The change does not add raw-value output paths without explicit review.
- [ ] The change does not weaken consent, audit, MCP raw-free boundaries, or file-permission behavior.

## Notes

Use dummy data only. If reproducing a personal-data issue requires real values, do not put them in this PR.
