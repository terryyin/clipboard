{
  description = "Clipboard development environment";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs = { nixpkgs, ... }:
    let
      systems = [ "aarch64-darwin" "x86_64-darwin" "aarch64-linux" "x86_64-linux" ];
      forAllSystems = nixpkgs.lib.genAttrs systems;
    in
    {
      devShells = forAllSystems (system:
        let pkgs = nixpkgs.legacyPackages.${system};
        in {
          default = pkgs.mkShell {
            packages = [ pkgs.python313 pkgs.uv pkgs.gnumake pkgs.actionlint ];
            # Use Nix's interpreter; uv manages only the project's virtualenv.
            UV_PYTHON_DOWNLOADS = "never";
            UV_PYTHON = "${pkgs.python313}/bin/python3";
            shellHook = ''
              echo "Run 'make deps' to sync the locked Python environment."
            '';
          } // nixpkgs.lib.optionalAttrs pkgs.stdenv.isLinux {
            # libX11 for `make test-package`'s installed X11 clear helper
            # check only (it would otherwise report "libx11", not "display").
            # Not on LD_LIBRARY_PATH, so system tools such as xclip keep
            # their own libX11.
            CLIPBOARD_PACKAGE_CHECK_LIBX11_DIR = "${pkgs.libx11}/lib";
          };
        });
    };
}
