# ALttPMSUShuffler
 Script that generates a new shuffled MSU-1 pack for use in ALttP Randomizer

Finds all PCM files in all subdirectories of the parent directory of this
script, and creates a new shuffled full MSU-1 pack for ALttP Randomizer;
for each of the 61 tracks, it finds all matching \*-$N.pcm tracks from all
MSU packs in all subdirectories of the parent directory and picks one at
random to copy to this directory as shuffled-$N.pcm.

Usage:
1) Copy this script to a new subdirectory in the directory containing all
   of your current MSU packs
2) Run Main.py to execute the script to delete any old pack in this directory
   and generate a new one.  Track names picked will be saved in "output.log"
   (cleared on reruns)
3) (first time only) Create a new empty file named "shuffled.msu" in this
   directory
4) Copy the ALttP Randomizer ROM (with background music enabled) to this
   directory and rename it to "shuffled.sfc".  Load it in an MSU-compatible
   emulator (works well with Snes9x 1.60)
