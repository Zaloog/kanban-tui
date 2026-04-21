{
  description = "customizable task tui powered by textual usable by agents";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      systems = [ "x86_64-linux" "aarch64-linux" "x86_64-darwin" "aarch64-darwin" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      packages = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python3;

          textual-jumper = python.pkgs.buildPythonPackage {
            pname = "textual-jumper";
            version = "0.2.1";
            format = "wheel";

            src = pkgs.fetchurl {
              url = "https://files.pythonhosted.org/packages/py3/t/textual_jumper/textual_jumper-0.2.1-py3-none-any.whl";
              hash = "sha256-WA1CRbfGCxy6o63YEFq1zq/zkSs8uGyCPqaA3F4C3Es=";
            };

            dependencies = [ python.pkgs.textual ];

            doCheck = false;

            meta = {
              description = "A jump/easymotion plugin for Textual";
              homepage = "https://github.com/zaloog/textual-jumper";
              license = pkgs.lib.licenses.mit;
            };
          };
        in
        {
          default = python.pkgs.buildPythonApplication {
            pname = "kanban-tui";
            version = "0.21.0";
            pyproject = true;

            src = ./.;

            build-system = [ python.pkgs.hatchling ];

            dependencies = with python.pkgs; [
              click
              textual
              textual-plotext
              tzdata
              python-dateutil
              pydantic
              pydantic-settings
              tomli-w
              xdg-base-dirs
              textual-jumper
            ];

            # Skip tests during nix build (they require a running environment)
            doCheck = false;

            meta = with pkgs.lib; {
              description = "customizable task tui powered by textual usable by agents";
              homepage = "https://github.com/Zaloog/kanban-tui";
              license = licenses.mit;
              mainProgram = "ktui";
            };
          };
        }
      );

      apps = forAllSystems (system: {
        default = {
          type = "app";
          program = "${self.packages.${system}.default}/bin/ktui";
        };
      });

      devShells = forAllSystems (system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python3;
        in
        {
          default = pkgs.mkShell {
            buildInputs = [
              (python.withPackages (ps: with ps; [
                click
                textual
                textual-plotext
                tzdata
                python-dateutil
                pydantic
                pydantic-settings
                tomli-w
                xdg-base-dirs
                hatchling
              ]))
              pkgs.ruff
              pkgs.mypy
            ];
          };
        }
      );
    };
}
