# Launcher artwork

`RDR2Launcher.png` is the transparent master artwork. `RDR2Launcher.icns` contains
the standard macOS icon sizes from 16 through 1024 pixels, including Retina
variants. Packaging copies the icon to both the launcher and the Wine game bundle.

Generated with the built-in imagegen tool on 2026-10-28. Final prompt:

> Use case: logo-brand. Asset type: production macOS launcher app icon for a personal Red Dead Redemption 2 launcher. Create one polished square 1024x1024 icon: a bold, recognizable black silhouette of a lone western cowboy wearing a broad brim hat, seen shoulders-up, against a warm pale sunset disk on a deep red softly textured rounded-square tile. Strong simple shapes, restrained premium print-poster texture, balanced centered composition, crisp silhouette legible at 32px. The cowboy and sunset are inset comfortably inside the tile. Subtle edge lighting and dimensional tile finish suited to the macOS Dock, no extruded 3D objects. Single icon only, front-on, no mockup, no letters, no numbers, no text, no watermark, no Rockstar logo. Outside the rounded square tile use genuine transparency, with clean antialiased edges. The tile fills approximately 90% of the canvas.

To regenerate the `.icns` from the master on macOS:

```sh
python3 packaging/build-icon.py assets/launcher/RDR2Launcher.png assets/launcher/RDR2Launcher.icns
```

This uses Apple's `sips` and `iconutil`. `iconutil` needs normal macOS service
access; it can reject an otherwise valid icon set inside an agent sandbox.
Normal app builds use the checked-in `.icns` directly.
