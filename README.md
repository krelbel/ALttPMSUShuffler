# ALttPMSUShuffler

Creates a shuffled MSU-1 pack for ALttP Randomizer from one or more source
MSU-1 packs.

Usage:

1) Copy this script to a new subdirectory in the directory containing all
   of your current MSU packs

2) Run Main.py to execute the script to delete any old pack in this directory
   and generate a new one.  Track names picked will be saved in "output.log"
   (cleared on reruns)
   - By default, the generated pack will pick each track from a matching
     track number in a random MSU pack in the parent directory of this
     script.
   - If run in the command line as "python Main.py --trackshuffle", behavior
     for non-looping tracks (short fanfares, portals, etc.) remains as
     default, but looping tracks will be in shuffled order, so each track
     in the generated pack is chosen from a random track number in a random
     MSU pack.  Pick this if you like shop music in Ganon's Tower.
   - If run in the command line as
     "python Main.py --singleshuffle ../your-msu-pack-name-here", behavior is
     the same as with --trackshuffle, but a single MSU pack of your choice is
     chosen as the shuffled source for all tracks in the generated pack.
   - If run in the command line as
     "python Main.py --xshuffle", behavior will only shuffle dungeon and
     boss tracks. This is more-interesting with Extended MSU Packs.

  Debugging options (not necessary for normal use):
   - This script uses hardlinks instead of copies by default to reduce disk
     usage and increase speed; the --realcopy option can be used to create
     real copies instead of hardlinks.
   - The --debug option can be used to make this script print the filesystem
     commands (deleting, creating, renaming files) it would have executed
     instead of executing them.

3) Copy the ALttP Randomizer ROM (with background music enabled) to this
   directory and rename it to "shuffled.sfc".  Load it in an MSU-compatible
   emulator (works well with Snes9x 1.60)

