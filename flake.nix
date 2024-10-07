{
  description = "Sceptre development environment";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = {
    nixpkgs,
    flake-utils,
    ...
  }:
    flake-utils.lib.eachDefaultSystem (system: let
      pkgs = import nixpkgs {
        inherit system;
      };
    in {
      devShells.default = pkgs.mkShell {
        # buildInputs = with pkgs; [
        #   poetry
        # ];
        packages = with pkgs; [
          nix-search-cli
          pre-commit
          just
          watchexec

          # Make sure nix works within the shell
          nixStatic

          # Python
          poetry
          python3

          # Other packages needed for compiling python libs
          readline
          libffi
          openssl
          glibcLocalesUtf8
        ];

        shellHook = ''
          poetry env use $(which python3)
          poetry install
          . $(poetry env info -p)/bin/activate
        '';
      };
    });
}
