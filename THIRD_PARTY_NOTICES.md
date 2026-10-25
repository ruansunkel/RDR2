# Third-party provenance

`config/engine-upstream.json` is an unchanged snapshot from Highball at commit
`cabadb4cfaaad0ece66f7fad2206fdd7a0b41ffb`, published under GPL-3.0.
The upstream license is preserved in `licenses/Highball-GPL-3.0.txt`.
Source: https://github.com/gauthierpiarrette/highball.

`config/recipes/*.json` are unchanged Highball DB snapshots at commit
`813666d7901969d683715f662cc686b03fc8267a`, published under CC0.
The dedication/license is preserved in `licenses/Highball-DB-CC0.txt`.
Source: https://github.com/gauthierpiarrette/highball-db.

The launcher is an independent implementation using these documented runtime
settings. No HighballKit code or third-party executable is included in source
control. Downloaded source checkouts/build artifacts are ignored.

Wine/runtime/DXMT/MoltenVK source and redistribution obligations must be reviewed
before bundling them. Manifest license labels and an SBOM do not substitute for
corresponding source, required notices or a compliant offer. Build scripts require
a separately reviewed runtime `licenses/` directory. No Apple D3DMetal, game or
client binaries, credentials or authenticated prefix may be distributed.
