# Permanent data folder — 2026-10-27

The main app now uses:

`~/Library/Application Support/RDR2Launcher/`

The Wine prefix is `prefixes/default/` inside that folder. The current game
files are in `SteamLibrary/steamapps/common/Red Dead Redemption 2/` alongside
the prefix. This is the same tested environment and game copy previously under
`RDR2Launcher-MoltenVK-Candidate`, moved into place without downloading or
reinstalling anything.

Before migration, the already existing `RDR2Launcher/` contained an older
~3.8 GB prefix and client state. It had no local RDR2 game installation; its
R: drive pointed to a separate game copy at `~/Games/RDR2/`. That older prefix
is preserved at:

`/Users/ruansunkel/Personal/RDR2-archive-20261027/application-support/RDR2Launcher-before-permanent-name/`

The external `~/Games/RDR2/` game copy remains untouched.

The tested ~124 GB environment was renamed to the permanent name. Its remembered
environment, launcher library setting, Steam library-folder files and R: mapping
now use the permanent path. Originals of the modified files and a migration
record are preserved under the archive's `application-support/permanent-name-migration/`.

A relative symlink at `RDR2Launcher-MoltenVK-Candidate` points to `RDR2Launcher`.
It contains no second game copy. This compatibility link preserves absolute
paths embedded in Wine/client state, private-home document mappings, older
backups and diagnostic records. Keep it unless those dependencies are separately
audited and migrated.

The main app is now the `patched` edition rather than an experimental candidate.
It uses the permanent folder while retaining the dedicated-buffer option and
all accepted renderer changes. The experimental default names remain unchanged;
the candidate name here is now a compatibility alias, so any future experiment
needs a newly copied environment. Experimental launchers refuse the regular
environment. The main renderer policy and marker path also use the permanent
name; the tested driver binary is unchanged.

Verification preserved the inode/size inventory of all 124 game files, the
RDR2 executable checksum and the checksums of all 8 profile/save files. All
18 Python checks and 17 Swift core checks passed, including the patched
edition's permanent default, experimental-isolation guard and allocation/log
settings. Deep/strict signing and runtime integrity checks passed. A native GPU
probe loaded the packaged driver without environment overrides, passed its
buffer/image checks, and wrote policy-on, argument-buffers-on and
dedicated-buffer-no-heap events under the permanent data directory. This did
not start Steam, Rockstar or RDR2; no new gameplay acceptance is claimed.

To revert the data move, first close RDR2, Steam, Rockstar and the launcher.
Remove only the compatibility symlink, move the current permanent folder back
to the candidate name, restore the backed-up path-setting files and R: mapping,
then move the archived older prefix back to the permanent name. Use the prior
app build or revert the main edition/config change as well. Never merge the
two Wine prefixes.
