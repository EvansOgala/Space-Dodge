# Space Dodge

## Fast-paced space survival game

### Description

Space Dodge is a fast-paced space survival game where players dodge falling stars, defeat bosses, and survive as long as possible.

### Project Metadata

* Package ID: `org.evans.SpaceDodge`
* Launchable desktop ID: `org.evans.SpaceDodge.desktop`
* License: MIT (Project), CC0-1.0 (Metadata)

### Gameplay

* Dodge falling stars
* Defeat bosses
* Survive for as long as possible

### Building

If using Flatpak:

```bash
flatpak-builder build-dir manifest.json --force-clean
```

### Running

```bash
flatpak run org.evans.SpaceDodge
```

For a local checkout:

```bash
python3 games_final.py
```

### AUR Packaging

This repo includes an AUR-ready `PKGBUILD` for version `1.0.2`.

Before publishing, create and push the matching upstream git tag:

```bash
git tag -a v1.0.2 -m "Space Dodge 1.0.2"
git push origin v1.0.2
```

Then test the package locally:

```bash
makepkg -si
```

If the build works, refresh `.SRCINFO`:

```bash
makepkg --printsrcinfo > .SRCINFO
```

To publish on AUR:

```bash
git clone ssh://aur@aur.archlinux.org/space-dodge.git aur-space-dodge
cp PKGBUILD .SRCINFO aur-space-dodge/
cd aur-space-dodge
git add PKGBUILD .SRCINFO
git commit -m "Initial release 1.0.2"
git push
```

If this is an update instead of a first upload, use the same AUR repo checkout and commit the new `PKGBUILD` and `.SRCINFO` there.

### Files

* `games_final.py` contains the Pygame game logic.
* `space-dodge` is the launcher script used by Flatpak.
* Desktop metadata is defined in `org.evans.SpaceDodge.desktop` and `org.evans.SpaceDodge.appdata.xml`.


---
