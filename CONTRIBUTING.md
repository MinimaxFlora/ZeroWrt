# Contributing

## Before opening a pull request

```bash
python -m unittest discover -v
python -m ruff check scripts tests
```

The tests are offline and do not need a Linux build host.

## Changing the image

- Package selections belong in `configs/ruijie-rg-x60-new.config`. Do not add a
  second package list in Python; `config.py` only appends OTA selections.
- Device-specific defaults (IP, SSID, root password) are workflow inputs and
  validated in `settings.py`.
- Files that have to be edited inside the source tree belong in `customize.py`.
  Add a verification for every new edit; a missed `sed` should fail the build,
  not ship silently.

## Changing a patch

- LuCI patches live in `scripts/0001`–`0005` and apply to `feeds/luci`.
- The GCC patch is `scripts/0006` and applies to the source root.
- Package patches are `scripts/900-*`; they are copied into the package's
  `patches/` directory.
- Regenerate a patch against the current baseline, verify it with
  `git apply --check`, and run the unit tests. See `docs/BUILD.md` §6.
- Do not use fuzzy matching in the pipeline. A context change must be visible.

## Commits

Keep changes focused. Mention the affected workflow step in the commit message
(for example `customize: set the default hostname`). Never commit a real root
password, WiFi password or token.
