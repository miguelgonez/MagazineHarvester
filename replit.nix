{pkgs}: {
  deps = [
    pkgs.zlib
    pkgs.xcodebuild
    pkgs.playwright-driver
    pkgs.gitFull
    pkgs.chromedriver
    pkgs.chromium
    pkgs.geckodriver
    pkgs.postgresql
    pkgs.bash
  ];
}
