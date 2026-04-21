# Maintaining the Nix Flake

## Release Process

When releasing a new version:

1. Update the `version` field in `flake.nix` to match `pyproject.toml`
2. If Python dependencies changed in `pyproject.toml`, the build will automatically pick up the new requirements (they are listed explicitly in `flake.nix` under `dependencies`)
3. If a new dependency was added that isn't in nixpkgs, add it as a custom derivation (see `textual-jumper` in `flake.nix` for an example)
4. Test the build:
   ```bash
   nix build --no-link
   nix run . -- --help
   nix flake check
   ```
5. Update `flake.lock` periodically: `nix flake update`
6. Commit all changes together

## Updating flake.lock

The `flake.lock` file pins the exact nixpkgs revision. Update it periodically to get newer Python packages:

```bash
nix flake update
nix build --no-link
nix run . -- --help
```

## Adding Dependencies Not in nixpkgs

If a Python dependency is not available in nixpkgs, you can package it locally in `flake.nix`. See the `textual-jumper` derivation as an example. For packages using `uv_build` as their build backend, fetch the wheel directly instead of the source tarball.

## Verification Checklist

Before committing flake changes:

- [ ] `nix build --no-link` succeeds
- [ ] `nix run . -- --help` shows correct output
- [ ] `nix flake check` passes
- [ ] `nix develop -c python --version` works
- [ ] `nix develop -c ruff --version` works
