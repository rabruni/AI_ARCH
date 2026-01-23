# Rollout

## Deployment Steps

1. Create script: check_runbook_complete.py
2. Create spec pack: SPEC-002 directory
3. Update runbook: Remove all TODO placeholders
4. Verify locally: Run smoke test
5. Commit: Tag as validated state

## Rollback

If gates fail, check G3.log for specific failure and fix accordingly.
