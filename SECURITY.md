# Security policy

## Supported versions

Only the latest build published in the `ruijie_rg-x60-new` release is supported.

## Reporting

Report a vulnerability privately through GitHub's **Security → Report a
vulnerability** form. Do not open a public issue for a vulnerability that can
be used to take over a device.

## Firmware-specific notes

- The default root password is `password`. Change it on first login; the build
  workflow input can set a stronger one.
- The OTA client requires HTTPS, a SHA256 in the index, and a successful
  `sysupgrade -T` check before flashing. Plain HTTP is only possible when the
  user explicitly enables *allow insecure connections* on the device.
- The build workflow uses the repository-scoped `GITHUB_TOKEN` to publish the
  release and the `gh-pages` branch. No long-lived source token is required.
- GitHub Actions masks the workflow inputs, but a password typed into a public
  workflow run is still visible to repository administrators in the run
  metadata. Use a repository secret or a throwaway password if that matters.
