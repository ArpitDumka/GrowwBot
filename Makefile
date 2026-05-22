.PHONY: deploy phase10-check corpus-refresh-smoke

deploy:
	powershell -ExecutionPolicy Bypass -File phase-10/scripts/deploy.ps1

phase10-check:
	powershell -ExecutionPolicy Bypass -File phase-10/scripts/verify_phase10.ps1

corpus-refresh-smoke:
	powershell -ExecutionPolicy Bypass -File phase-10/scripts/run_scheduler_once.ps1 -SkipIngest -SkipIndex
