# Preparing the first public release

The current code uses the [MIT license](../LICENSE), includes English and Spanish instructions, and documents the provenance of its current portraits. This is a community project, without product-owner endorsement.

An earlier portrait retired during development remains in the original private Git history. Replacing a file in the current checkout does not remove its previous revisions. Publish the current source with a **fresh initial history**, rather than making that development history public.

Create a source export with:

```sh
python3 scripts/prepare_public_release.py
```

The output is `build/public-release/` and `build/public-release.zip`. It includes current project files and excludes `.git`, the virtual environment, build products and local diagnostics. Review files and artwork before publishing. The exporter refuses unexpected top-level paths, links and known private-file types; this does not replace a review for accidentally embedded secrets.

Use an empty GitHub repository for the public project. Keep the old repository private if its earlier history needs to remain available. If you want to retain the existing repository name, first choose how to preserve or rename the private development repository. Rewriting an existing remote requires coordination and may leave old copies in forks, pull requests or caches; see [GitHub's history-removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).

Inside the exported directory, initialize a new repository and commit the reviewed files using your chosen Git identity:

```sh
cd build/public-release
git init -b main
git add .
git commit -m "Initial public release"
```

Connect it to the empty GitHub repository through your preferred Git client. Do not copy the original `.git` directory, Git bundle, virtual environment or build directory into the new repository. Check your Git email privacy settings before committing.

The included macOS CI workflow runs tests and compiles both bridges without installing hooks or opening a physical Bluetooth device. Require a successful run, including the real loopback security check, before announcing the release. A sandbox skip is not a completed loopback check. Then check the monitor on both physical device models.

Enable private vulnerability reporting on GitHub if available, and consider requiring passing checks for changes to the default branch. These are repository settings and are not changed by the local exporter.
