# Maintaining the Nix Flake

All maintenance tasks are available via `scripts/maintain-nix-flake.sh`.

## Quick Reference

```bash
# Sync version from pyproject.toml into flake.nix
./scripts/maintain-nix-flake.sh sync-version

# Update flake.lock to latest nixpkgs
./scripts/maintain-nix-flake.sh update-lock

# Run the full verification checklist
./scripts/maintain-nix-flake.sh verify

# Release: sync version + verify (run before committing)
./scripts/maintain-nix-flake.sh release
```

## Release Process

When releasing a new version:

1. Bump `version` in `pyproject.toml`
2. Run `./scripts/maintain-nix-flake.sh release` — this syncs the version into `flake.nix` and runs all verification checks
3. If Python dependencies changed in `pyproject.toml`, update the `dependencies` list in `flake.nix` to match
4. If a new dependency was added that isn't in nixpkgs, add it as a custom derivation (see `textual-jumper` in `flake.nix` for an example)
5. Commit all changes together

## Updating flake.lock

The `flake.lock` file pins the exact nixpkgs revision. Update it periodically to get newer Python packages:

```bash
./scripts/maintain-nix-flake.sh update-lock
./scripts/maintain-nix-flake.sh verify
```

## Adding Dependencies Not in nixpkgs

If a Python dependency is not available in nixpkgs, you can package it locally in `flake.nix`. See the `textual-jumper` derivation as an example. For packages using `uv_build` as their build backend, fetch the wheel directly instead of the source tarball.

## Verification Checklist

Run `./scripts/maintain-nix-flake.sh verify` to check all of the following:

- `nix build --no-link` succeeds
- `nix run . -- --help` shows correct output
- `nix flake check` passes
- `nix develop -c python --version` works
- `nix develop -c ruff --version` works
