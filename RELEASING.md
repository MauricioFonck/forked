# Releasing FORKED

Maintainers only. A release is public and some steps cannot be undone (a name on PyPI is
permanent, and a published version number is never reused), so this is a checklist, not a script.

## 0. Preconditions

- [ ] CI is green on `main` (Linux 3.11–3.14, Windows, macOS).
- [ ] The [prior-art matrix](docs/15-prior-art-matrix.md) was re-run for this release and says what is
      and is not covered. Novelty words stay out of the docs until its gate is closed (a test enforces this).
- [ ] `uv run python -m benchmarks.fcrb --out results/` passes; note whether it has been independently reproduced.
- [ ] The [guarantees and limits](docs/guide/05-guarantees-and-limits.md) and `SECURITY.md` match what the code does.

## 1. Version

Change the version in **every** place, then `uv lock`:

| File | What |
|---|---|
| `pyproject.toml` | `version` (PEP 440, e.g. `0.1.0a2`) |
| `src/forked/__init__.py` | `__version__` |
| `CITATION.cff` | `version`, `date-released` |
| `CHANGELOG.md` | move `[Unreleased]` under a dated heading |
| `docs/release-notes/vX.md` | new notes; update the links in `README.md` and `docs/README.md` |
| `SECURITY.md` | the version in "Current guarantees and limits" |

## 2. Verify

```bash
uv sync --locked
uv run ruff check . && uv run ruff format --check . && uv run mypy && uv run pytest
uv build --out-dir dist
uvx twine check dist/*                   # both files must PASS
```

Install the wheel in a clean environment, with and without extras, and run it from outside the
repository (CI does the same on every push):

```bash
uv run --isolated --no-project --with dist/forked_runtime-X-py3-none-any.whl python -m forked record toy-agent
```

## 3. Tag and GitHub release

```bash
git tag -a vX -m "FORKED vX"
git push origin vX
gh release create vX --prerelease --title "FORKED vX" --notes-file notes.md dist/*.whl dist/*.tar.gz
```

- Alphas and betas are **pre-releases**.
- Release notes use **absolute** links (relative ones break on the release page) and list the
  SHA-256 of each artifact. Re-download the assets and compare the checksums.
- State what is **not** done: PyPI, independent reproduction, prior-art status.

## 4. PyPI (owner only)

The distribution name is `forked-runtime` (`forked` is taken, see ADR-002); the import and the command are `forked`.

1. Rehearse on TestPyPI: `uv publish --publish-url https://test.pypi.org/legacy/ dist/*`.
2. Make the README render on PyPI: its relative links do not resolve there. Convert them to absolute
   `https://github.com/MauricioFonck/forked/blob/vX/...` URLs for the published build (the hero image already is).
3. Prefer **Trusted Publishing** (PyPI → project → Publishing → add a GitHub trusted publisher) over a long-lived
   token. With a token: `uv publish --token "$PYPI_TOKEN" dist/*`.
4. Verify from a clean machine: `pip install forked-runtime==X` and `forked --version`.

## 5. After

- Update `contexto/forked/estado-actual.md` and add the session log and impact analysis.
- Announce honestly: what is new, what is **not**, the prior-art status, and a link to the call for
  independent reproduction.
