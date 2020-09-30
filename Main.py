import argparse
import logging
import os
from pathlib import Path
import random
import re
import shutil

__version__ = '0.3-dev'

# Creates a shuffled MSU-1 pack for ALttP Randomizer from one or more source
# MSU-1 packs.
#
# Usage:
# 1) Copy this script to a new subdirectory in the directory containing all
#    of your current MSU packs
# 2) Run Main.py to execute the script to delete any old pack in this directory
#    and generate a new one.  Track names picked will be saved in "output.log"
#    (cleared on reruns)
#    - By default, the generated pack will pick each track from a matching
#      track number in a random MSU pack in the parent directory of this
#      script.
#    - If run in the command line as "python Main.py --trackshuffle", behavior
#      for non-looping tracks (short fanfares, portals, etc.) remains as
#      default, but looping tracks will be in shuffled order, so each track
#      in the generated pack is chosen from a random track number in a random
#      MSU pack.  Pick this if you like shop music in Ganon's Tower.
#    - If run in the command line as
#      "python Main.py --singleshuffle ../your-msu-pack-name-here", behavior is
#      the same as with --trackshuffle, but a single MSU pack of your choice is
#      chosen as the shuffled source for all tracks in the generated pack.
#    - If run in the command line as
#      "python Main.py --xshuffle", behavior will only shuffle dungeon and
#      boss tracks. This is more-interesting with Extended MSU Packs.
# 3) (first time only) Create a new empty file named "shuffled.msu" in this
#    directory
# 4) Copy the ALttP Randomizer ROM (with background music enabled) to this
#    directory and rename it to "shuffled.sfc".  Load it in an MSU-compatible
#    emulator (works well with Snes9x 1.60)

# Tracklist from https://pastebin.com/zjqQZu5M
titles = [
"1 - Opening Theme",
"2 - Light World Overworld",
"3 - Rain State Overworld",
"4 - Bunny Overworld",
"5 - Lost Woods",
"6 - Prologue",
"7 - Kakariko",
"8 - Portal",
"9 - Dark World Overworld",
"10 - Pull Pedestal",
"11 - File Select/Game Over",
"12 - Guards Summoned",
"13 - Dark Death Mountain",
"14 - Minigame",
"15 - Skull Woods Overworld",
"16 - Castle",
"17 - Light World Dungeon",
"18 - Cave",
"19 - Boss Victory",
"20 - Sanctuary",
"21 - Boss",
"22 - Dark World Dungeon",
"23 - Shop/Fortune Teller",
"24 - Cave 2",
"25 - Zelda's Rescue (unused in rando)",
"26 - Crystal Cutscene (only the beginning is heard in rando)",
"27 - Fairy Fountain",
"28 - Agahnim's Theme (top floor of Castle Tower)",
"29 - Ganon Reveals Himself (after Agahnim 2)",
"30 - Agahnim's Theme (drop in to Ganon)",
"31 - Ganon Fight",
"32 - Triforce Room",
"33 - Ending Sequence",
"34 - Credits",

#Dungeon-specific tracks

"35 - Eastern Palace",
"36 - Desert Palace",
"37 - Agahnim's Tower",
"38 - Swamp Palace",
"39 - Palace of Darkness",
"40 - Misery Mire",
"41 - Skull Woods",
"42 - Ice Palace",
"43 - Tower of Hera",
"44 - Thieves' Town",
"45 - Turtle Rock",
"46 - Ganon's Tower",

#Bosses

"47 - Boss Eastern Palace",
"48 - Boss Desert Palace",
"49 - Boss Agahnim's Tower",
"50 - Boss Swamp Palace",
"51 - Boss Palace of Darkness",
"52 - Boss Misery Mire",
"53 - Boss Skull Woods",
"54 - Boss Ice Palace",
"55 - Boss Tower of Hera",
"56 - Boss Thieves' Town",
"57 - Boss Turtle Rock",
"58 - Boss Ganon's Tower",

#Extra Tracks

"59 - Ganon's Tower 2 (Plays in upstairs GT instead of the normal GT music once you've found the Big Key)",
"60 - Light World 2 (Replaces track 2 after the pedestal item has been obtained)",
"61 - Dark World 2 (Replaces tracks 9, 13 and 15 after obtaining all 7 crystals)"]

#Tracks that don't loop; this is used to prevent a non-looping track from
#being shuffled with a looping track (nobody wants the boss fanfare as
#light world overworld music)
nonloopingtracks = [1, 8, 10, 19, 29, 33, 34]

#List of generic and specific dungeon & boss tracks.  Weighted so generic
#tracks are more likely to show up since otherwise specific tracks get
#shuffled in way more often.
genericboss = [21] * 10
genericdungeon = [0] * 14
genericdungeon[:7] = [17] * 7
genericdungeon[7:] = [22] * 7
specificdungeon = list(range(35,46)) + [59]
specificboss = list(range(47,58))

def delete_old_msu(args):
    if os.path.exists("output.log"):
        os.remove("output.log")
    for path in Path('./').rglob('*.pcm'):
        os.remove(str(path))

def pick_random_track(logger, args, src, dst, printsrc):
    dststr = str(dst)
    dstname = "./shuffled-" + dststr + ".pcm"
    match = "*-" + str(src) + ".pcm"

    l = list()
    if (args.singleshuffle):
        searchdir = args.singleshuffle
    else:
        searchdir = '../'

    for path in Path(searchdir).rglob(match):
        l.append(path)

    if not l:
        #This should never happen
        logger.info("Failed to find " + match + " in " + searchdir)
        return;

    winner = random.choice(l)
    if printsrc:
        logger.info(titles[dst-1] + ': ' + str(winner) + " (" + titles[src-1] + ")")
    else:
        logger.info(titles[dst-1] + ': ' + str(winner))
    shutil.copy(str(winner), dstname)

def generate_shuffled_msu(args):
    logger = logging.getLogger('')
    output_file_handler = logging.FileHandler("output.log")
    logger.addHandler(output_file_handler)

    #For all packs in the target directory, make a list of found track numbers.
    if (args.singleshuffle):
        searchdir = args.singleshuffle
    else:
        searchdir = '../'

    foundtracks = list()
    for path in Path(searchdir).rglob('*.pcm'):
        for match in re.finditer(r'\d+', os.path.basename(str(path))):
            pass
        if (int(match.group(0)) not in foundtracks):
            foundtracks.append(int(match.group(0)))
    foundtracks = sorted(foundtracks)

    #Separate this list into looping tracks and non-looping tracks, and make a
    #shuffled list of the found looping tracks.
    loopingfoundtracks = [i for i in foundtracks if i not in nonloopingtracks]
    shuffledloopingfoundtracks = loopingfoundtracks.copy()
    random.shuffle(shuffledloopingfoundtracks)
    nonloopingfoundtracks = [i for i in foundtracks if i in nonloopingtracks]

	#Merge some lists
    bosstracks = genericboss + specificboss
    dungeontracks = genericdungeon + specificdungeon
    #Shuffle shuffle shuffle
    shuffledbosstracks = bosstracks.copy()
    random.shuffle(shuffledbosstracks)
    shuffleddungeontracks = dungeontracks.copy()
    random.shuffle(shuffleddungeontracks)
    #Also I guess we should remove tracks if they're not present
    #There's probably a better way to do this but python is a dumb language #hottakes
    for i in shuffledbosstracks:
        if i not in foundtracks:
            shuffledbosstracks.pop()

    for i in shuffleddungeontracks:
        if i not in foundtracks:
            shuffleddungeontracks.pop()

    #For all found non-looping tracks, pick a random track with a matching
    #track number from a random pack in the target directory.
    logger.info("Non-looping tracks:")
    for i in nonloopingfoundtracks:
        srcstr = str(i)
        pick_random_track(logger, args, i, i, False)

    #For all found looping tracks, pick a random track from a random pack
    #in the target directory, with a matching track number by default, or
    #a shuffled different looping track number if trackshuffle or
    #singleshuffle are enabled.
    logger.info("Looping tracks:")
    for i in loopingfoundtracks:
        if (args.trackshuffle or args.singleshuffle):
            dst = i
            src = shuffledloopingfoundtracks[loopingfoundtracks.index(i)]
            printsrc = True
        else:
            dst = i
            src = i

            #Okay we're shuffling extra tracks so do that I guess
            if (args.xshuffle):
                if (i in specificdungeon):
                    src = random.choice(shuffleddungeontracks)
                elif (i in specificboss):
                    src = random.choice(shuffledbosstracks)
            printsrc = False
        pick_random_track(logger, args, src, dst, printsrc)

    logger.info('Done.')

def main(args):
    if args.version:
        print("ALttPMSUShuffler version " + __version__)
        return

    delete_old_msu(args)
    generate_shuffled_msu(args)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--loglevel', default='info', const='info', nargs='?', choices=['error', 'info', 'warning', 'debug'], help='Select level of logging for output.')
    parser.add_argument('--trackshuffle', help='Choose each looping track randomly from all looping tracks from all packs, rather than the default behavior of only exchanging each track with that same track from a random pack.', action='store_true')
    parser.add_argument('--singleshuffle', help='Choose each looping track randomly from all looping tracks from a single MSU pack.  Enter the path to a subfolder in the parent directory containing a single MSU pack.')
    parser.add_argument('--version', help='Print version number and exit.', action='store_true')
    parser.add_argument('--xshuffle', help='Shuffles generic dungeon/boss tracks into specific dungeon/boss tracks.', action='store_true')


    args = parser.parse_args()

    # set up logger
    loglevel = {'error': logging.ERROR, 'info': logging.INFO, 'warning': logging.WARNING, 'debug': logging.DEBUG}[args.loglevel]
    logging.basicConfig(format='%(message)s', level=loglevel)

    main(args)
