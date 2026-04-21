#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
FLAKE="$PROJECT_DIR/flake.nix"
PYPROJECT="$PROJECT_DIR/pyproject.toml"

cd "$PROJECT_DIR"

# Colors
red() { printf '\033[0;31m%s\033[0m\n' "$*"; }
green() { printf '\033[0;32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[0;33m%s\033[0m\n' "$*"; }
bold() { printf '\033[1m%s\033[0m\n' "$*"; }

usage() {
    cat <<EOF
Usage: $(basename "$0") <command>

Commands:
  sync-version    Sync version from pyproject.toml into flake.nix
  update-lock     Update flake.lock to latest nixpkgs
  verify          Run the full verification checklist
  release         Run sync-version + verify (use before committing a release)

EOF
}

# Extract version from pyproject.toml
get_pyproject_version() {
    grep '^version' "$PYPROJECT" | head -1 | sed 's/.*"\(.*\)".*/\1/'
}

# Extract version from flake.nix (the kanban-tui version, not sub-packages)
get_flake_version() {
    sed -n '/pname = "kanban-tui"/{n;s/.*version = "\(.*\)".*/\1/p;}' "$FLAKE"
}

cmd_sync_version() {
    local py_version flake_version
    py_version="$(get_pyproject_version)"
    flake_version="$(get_flake_version)"

    if [ "$py_version" = "$flake_version" ]; then
        green "Versions already in sync: $py_version"
        return 0
    fi

    yellow "pyproject.toml: $py_version"
    yellow "flake.nix:      $flake_version"
    bold "Updating flake.nix to $py_version..."

    # Only replace the version line immediately after pname = "kanban-tui"
    sed -i '/pname = "kanban-tui"/{n;s/version = ".*"/version = "'"$py_version"'"/;}' "$FLAKE"
    green "Done. flake.nix version is now $py_version"
}

cmd_update_lock() {
    bold "Updating flake.lock..."
    nix flake update
    green "flake.lock updated."
}

cmd_verify() {
    local failed=0

    bold "Running verification checklist..."
    echo

    printf "  nix build --no-link ... "
    if nix build --no-link 2>/dev/null; then
        green "OK"
    else
        red "FAIL"
        failed=1
    fi

    printf "  nix run . -- --help ... "
    if nix run . -- --help >/dev/null 2>&1; then
        green "OK"
    else
        red "FAIL"
        failed=1
    fi

    printf "  nix flake check ... "
    if nix flake check 2>/dev/null; then
        green "OK"
    else
        red "FAIL"
        failed=1
    fi

    printf "  nix develop -c python --version ... "
    if nix develop -c python --version >/dev/null 2>&1; then
        green "OK"
    else
        red "FAIL"
        failed=1
    fi

    printf "  nix develop -c ruff --version ... "
    if nix develop -c ruff --version >/dev/null 2>&1; then
        green "OK"
    else
        red "FAIL"
        failed=1
    fi

    echo
    if [ "$failed" -eq 0 ]; then
        green "All checks passed!"
    else
        red "Some checks failed."
        return 1
    fi
}

cmd_release() {
    cmd_sync_version
    echo
    cmd_verify
}

case "${1:-}" in
    sync-version) cmd_sync_version ;;
    update-lock)  cmd_update_lock ;;
    verify)       cmd_verify ;;
    release)      cmd_release ;;
    *)            usage; exit 1 ;;
esac
