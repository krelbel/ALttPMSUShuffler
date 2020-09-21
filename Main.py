import logging
import argparse
import os
import random
from pathlib import Path
import shutil

__version__ = '0.2-dev'

# Finds all PCM files in all subdirectories of the parent directory of this
# script, and creates a new shuffled full MSU-1 pack for ALttP Randomizer;
# for each of the 61 tracks, it finds all matching *-$N.pcm tracks from all
# MSU packs in all subdirectories of the parent directory and picks one at
# random to copy to this directory as shuffled-$N.pcm.
#
# Usage:
# 1) Copy this script to a new subdirectory in the directory containing all
#    of your current MSU packs
# 2) Run Main.py to execute the script to delete any old pack in this directory
#    and generate a new one.  Track names picked will be saved in "output.log"
#    (cleared on reruns)
# 3) (first time only) Create a new empty file named "shuffled.msu" in this
#    directory
# 4) Copy the ALttP Randomizer ROM (with background music enabled) to this
#    directory and rename it to "shuffled.sfc".  Load it in an MSU-compatible
#    emulator (works well with Snes9x 1.60)

# Tracklist from https://pastebin.com/zjqQZu5M
titles = [
"Opening Theme",
"Light World Overworld",
"Rain State Overworld",
"Bunny Overworld",
"Lost Woods",
"Prologue",
"Kakariko",
"Portal",
"Dark World Overworld",
"Pull Pedestal",
"File Select/Game Over",
"Guards Summoned",
"Dark Death Mountain",
"Minigame",
"Skull Woods Overworld",
"Castle",
"Light World Dungeon",
"Cave",
"Boss Victory",
"Sanctuary",
"Boss",
"Dark World Dungeon",
"Shop/Fortune Teller",
"Cave 2",
"Zelda's Rescue (unused in rando)",
"Crystal Cutscene (only the beginning is heard in rando)",
"Fairy Fountain",
"Agahnim's Theme (top floor of Castle Tower)",
"Ganon Reveals Himself (after Agahnim 2)",
"Agahnim's Theme (drop in to Ganon)",
"Ganon Fight",
"Triforce Room",
"Ending Sequence",
"Credits",

#Dungeon-specific tracks

"Eastern Palace",
"Desert Palace",
"Agahnim's Tower",
"Swamp Palace",
"Palace of Darkness",
"Misery Mire",
"Skull Woods",
"Ice Palace",
"Tower of Hera",
"Thieves' Town",
"Turtle Rock",
"Ganon's Tower",

#Bosses

"Boss Eastern Palace",
"Boss Desert Palace",
"Boss Agahnim's Tower",
"Boss Swamp Palace",
"Boss Palace of Darkness",
"Boss Misery Mire",
"Boss Skull Woods",
"Boss Ice Palace",
"Boss Tower of Hera",
"Boss Thieves' Town",
"Boss Turtle Rock",
"Boss Ganon's Tower",

#Extra Tracks

"Ganon's Tower 2 (Plays in upstairs GT instead of the normal GT music once you've found the Big Key)",
"Light World 2 (Replaces track 2 after the pedestal item has been obtained)",
"Dark World 2 (Replaces tracks 9, 13 and 15 after obtaining all 7 crystals)"]

def delete_old_msu(args):
    if os.path.exists("output.log"):
        os.remove("output.log")
    for path in Path('./').rglob('*.pcm'):
        os.remove(str(path))

def generate_shuffled_msu(args):
    logger = logging.getLogger('')
    output_file_handler = logging.FileHandler("output.log")
    logger.addHandler(output_file_handler)

    for i in range(61):
        istr = str(i + 1)
        match = "*-" + istr + ".pcm"
        dstname = "./shuffled-" + istr + ".pcm"

        l = list()
        for path in Path('../').rglob(match):
            l.append(path)

        winner = random.choice(l)
        logger.info(titles[i] + ': ' + str(winner))
        shutil.copy(str(winner), dstname)

    logger.info('Done.')

def main(args):
    delete_old_msu(args)
    generate_shuffled_msu(args)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--loglevel', default='info', const='info', nargs='?', choices=['error', 'info', 'warning', 'debug'], help='Select level of logging for output.')

    args = parser.parse_args()

    # set up logger
    loglevel = {'error': logging.ERROR, 'info': logging.INFO, 'warning': logging.WARNING, 'debug': logging.DEBUG}[args.loglevel]
    logging.basicConfig(format='%(message)s', level=loglevel)

    main(args)

