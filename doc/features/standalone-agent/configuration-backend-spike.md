# ConfigurationBackend spike — Salt vs WinGet/DSC on WSL

## Status

Prototype code added. Real Windows/WSL execution is still required before choosing the v0.1 backend.

## Purpose

Validate that Salt and WinGet/DSC can be hidden behind the same backend-neutral contract:

```text
inspect()
plan()
apply()
verify()
```

The prototype intentionally supports one target only:

```text
shell-environment
Ubuntu 24.04
amd64
via WSL on Windows 11
```

## Prototype files

- `scripts/environment_agent_backend_spike.py`
- `tests/test_environment_agent_backend_spike.py`

## What the prototype demonstrates

Both adapters return the same canonical model:

- `EnvironmentAssessment`;
- `BackendPlan`;
- `ApplyResult`;
- `VerifyResult`.

No caller needs to know Salt CLI syntax, WinGet Configuration syntax, DSC resources, PowerShell commands or backend-specific output.

## Salt adapter

Prototype strategy:

```text
salt-call --local state.apply <state> test=True
salt-call --local state.apply <state>
```

Expected strengths to validate on Windows:

- masterless/local execution;
- cross-platform path to Linux/Live/PXE;
- desired-state and idempotence;
- possible later transition to centrally managed Salt;
- structured output.

Open questions requiring a real host:

- Salt footprint/bootstrap on a student Windows machine;
- exact WSL state/resource implementation;
- reboot behavior;
- Windows UAC/elevation;
- quality/stability of structured output for failure cases.

## WinGet/DSC adapter

Prototype strategy:

```text
winget configure test --file <config>
winget configure --file <config>
```

Expected strengths to validate:

- Windows-native tooling;
- Windows Optional Features / DSC integration;
- low conceptual distance from WSL/Windows configuration;
- configuration test before apply.

Open questions requiring a real host:

- precise exit-code semantics across partial/non-compliant states;
- reboot signaling and continuation;
- distro lifecycle beyond Optional Features;
- availability/version consistency across school/student Windows 11 hosts;
- portability is intentionally Windows-only.

## Preliminary architectural conclusion

The contract is feasible: Salt and WinGet/DSC can be placed behind the same generic interface without exposing either backend to consumers.

The likely architecture remains:

```text
Generic Environment Agent
        ↓
ConfigurationBackend
        ├── SaltBackend
        └── WinGetDscBackend
```

The current hypothesis is:

- Salt: candidate generic backend for cross-platform/local-to-managed convergence;
- WinGet/DSC: candidate Windows-native backend/helper for Windows features and configuration.

This is **not yet a backend selection**. Selection requires the real-machine matrix defined in issue #803.

## Real-machine experiment required

Run both implementations, or equivalent minimal states/configurations, against:

1. Windows 11 with WSL absent;
2. WSL working + Ubuntu 24.04 present;
3. WSL present, distro absent;
4. reboot-required transition;
5. non-admin user.

Measure:

- installation footprint;
- setup time;
- preview/no-op fidelity;
- apply idempotence;
- reboot/resume;
- structured diagnostics;
- amount of adapter-specific code;
- ability to reuse the same approach on Linux/Live/PXE.

## Decision gate

Do not rewrite M2/M3 around one backend until this matrix has been executed on real Windows machines.
