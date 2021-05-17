# ALttPMSUShuffler

Creates a shuffled MSU-1 pack for ALttP Randomizer from one or more source
MSU-1 packs.

Usage:

1) Copy this script to a new subdirectory in the directory containing all
   of your current MSU packs.  For example, if your MSU pack is in
   `"MSUs\alttp_undertale\alttp_msu-1.pcm"`, the script should be in
   `"MSUs\ALttPMSUShuffler\Main.py"`.

2) DRAG AND DROP METHOD:

    1) Drag one or more ALttP Randomizer ROMs (with background music enabled)
       on top of Main.py to open the ROMs with the python script; for each ROM
       opened this way, a shuffled MSU pack matching that ROM's name will be
       generated next to the ROM in its original directory (with the tracklist
       in ROMNAME-msushuffleroutput.log).

3) MANUAL METHOD:

    1) Copy the ALttP Randomizer ROM (with background music enabled) to the
       same directory as this Main.py script.  The script will rename the ROM
       to "shuffled.sfc".  The original ROM name and tracklist is printed to
       "shuffled-msushuffleroutput.log" (handy for retrieving spoilers).  If
       you don't copy the ROM before running the script, you need to rename
       the ROM to "shuffled.sfc" yourself.  The script will warn before
       overwriting "shuffled.sfc" if it already exists.

    2) Run **Main.py** to execute the script to delete any old pack in this
       directory and generate a new one.  Track names picked will be saved in
       "shuffled-msushuffleroutput.log" (cleared on reruns)

    3) LIVE RESHUFFLE METHOD: Instead of simply running 
       **Main.py**, run **LiveReshuffle.py** or run in the command line as
       "python Main.py --live 10" (or any other positive integer) to
       generate a new shuffled MSU pack every few seconds.  Will skip
       replacing any tracks currently being played.  Best if used without
       the --realcopy option, and best if the shuffled MSU pack and source
       packs are all on the same hard drive, to avoid excessive disk usage.
       Edit **LiveReshuffle.py** to set a different reshuffle interval than
       the 10 second default.

    4) LIVE RESHUFFLE + NOW PLAYING VIEW (EXPERIMENTAL): Run the command
       line as "python Main.py --live 10 --nowplaying" to run in live
       reshuffle mode (as described above) while polling qusb2snes for
       the currently playing MSU pack, printed to console and nowplaying.txt
       for use as an OBS streaming text source.

4) Load the ROM in an MSU-compatible emulator (works well with Snes9x 1.60)

Additional options/usage notes:

- By default, the generated pack will pick each track from a matching
  track number in a random MSU pack in the parent directory of this
  script.  For dungeon-specific or boss-specific tracks, if the random
  pack chosen isn't an extended MSU pack, the generic dungeon/boss music
  is chosen instead.

  Note that if you ONLY have non-extended packs, this
  default behavior will create an extended pack, which (like all extended
  packs) prevents you from using music cues to distinguish pendant from
  crystal dungeons.  If you want this, use --basicshuffle instead.

- If run in the command line as "python Main.py --basicshuffle", each
  track is chosen from the same track from a random pack.  If you have any
  extended packs, the dungeon/boss themes from non-extended packs will
  never be chosen.

- If run in the command line as "python Main.py --fullshuffle", behavior
  for non-looping tracks (short fanfares, portals, etc.) remains as
  default, but looping tracks will be in shuffled order, so each track
  in the generated pack is chosen from a random track number in a random
  MSU pack.  Pick this if you like shop music in Ganon's Tower.

- If run in the command line as
  "python Main.py --singleshuffle ../your-msu-pack-name-here", behavior is
  the same as with --fullshuffle, but a single MSU pack of your choice is
  chosen as the shuffled source for all tracks in the generated pack.

- If run in the command line as "python Main.py --higan" (along with any
  other options), the shuffled MSU pack is generated in a higan-friendly
  subdirectory "./higan.sfc/"

- Searches the parent directory of the directory containing the script for
  all MSU packs to be included in the shuffler by default, but will skip
  any tracks with "disabled" (case-insensitive) in the directory name or
  file name; useful for keeping tracks hidden from the shuffler without
  needing to move them out of the collection entirely.

- Caches the track list in ./trackindex.pkl to avoid reindexing the entire
  collection every time the script is run.  If run in the command line as
  "python Main.py --reindex", it will regenerate the track index.  Use this
  to pick up any new MSU packs for the shuffler.

 Debugging options (not necessary for normal use):

- This script uses hardlinks instead of copies by default to reduce disk
  usage and increase speed; the --realcopy option can be used to create
  real copies instead of hardlinks.  Real copies are forced if the shuffled
  MSU pack and the source MSU packs are on different hard drives.

- The --dry-run option can be used to make this script print the filesystem
  commands (deleting, creating, renaming files) it would have executed
  instead of executing them.

