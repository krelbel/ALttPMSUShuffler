import argparse
import logging
import os
from pathlib import Path
import random
import re
import shutil
import glob
import sys

__version__ = '0.6'

# Creates a shuffled MSU-1 pack for ALttP Randomizer from one or more source
# MSU-1 packs.
#
# Usage:
#
# 1) Copy this script to a new subdirectory in the directory containing all
#    of your current MSU packs.  For example, if your MSU pack is in
#    "MSUs\alttp_undertale\alttp_msu-1.pcm", the script should be in
#    "MSUs\ALttPMSUShuffler\Main.py".
#
# 2) DRAG AND DROP METHOD:
#
#     1) Drag one or more ALttP Randomizer ROMs (with background music enabled)
#        on top of Main.py to open the ROMs with the python script; for each ROM
#        opened this way, a shuffled MSU pack matching that ROM's name will be
#        generated next to the ROM in its original directory (with the tracklist
#        in ROMNAME-msushuffleroutput.log).
#
# 3) MANUAL METHOD:
#
#     1) Copy the ALttP Randomizer ROM (with background music enabled) to the
#        same directory as this Main.py script.  The script will rename the ROM
#        to "shuffled.sfc".  The original ROM name and tracklist is printed to
#        "shuffled-msushuffleroutput.log" (handy for retrieving spoilers).  If
#        you don't copy the ROM before running the script, you need to rename
#        the ROM to "shuffled.sfc" yourself.  The script will warn before
#        overwriting "shuffled.sfc" if it already exists.
#
#     2) Run Main.py to execute the script to delete any old pack in this
#        directory and generate a new one.  Track names picked will be saved in
#        "shuffled-msushuffleroutput.log" (cleared on reruns)
#
# 4) Load the ROM in an MSU-compatible emulator (works well with Snes9x 1.60)
#
# Additional options/usage notes:
#
# - By default, the generated pack will pick each track from a matching
#   track number in a random MSU pack in the parent directory of this
#   script.  For dungeon-specific or boss-specific tracks, if the random
#   pack chosen isn't an extended MSU pack, the generic dungeon/boss music
#   is chosen instead.
#
#   Note that if you ONLY have non-extended packs, this
#   default behavior will create an extended pack, which (like all extended
#   packs) prevents you from using music cues to distinguish pendant from
#   crystal dungeons.  If you want this, use --basicshuffle instead.
#
# - If run in the command line as "python Main.py --basicshuffle", each
#   track is chosen from the same track from a random pack.  If you have any
#   extended packs, the dungeon/boss themes from non-extended packs will
#   never be chosen.
#
# - If run in the command line as "python Main.py --fullshuffle", behavior
#   for non-looping tracks (short fanfares, portals, etc.) remains as
#   default, but looping tracks will be in shuffled order, so each track
#   in the generated pack is chosen from a random track number in a random
#   MSU pack.  Pick this if you like shop music in Ganon's Tower.
#
# - If run in the command line as
#   "python Main.py --singleshuffle ../your-msu-pack-name-here", behavior is
#   the same as with --fullshuffle, but a single MSU pack of your choice is
#   chosen as the shuffled source for all tracks in the generated pack.
#
# - If run in the command line as "python Main.py --higan" (along with any
#   other options), the shuffled MSU pack is generated in a higan-friendly
#   subdirectory "./higan.sfc/"
#
#  Debugging options (not necessary for normal use):
#
# - This script uses hardlinks instead of copies by default to reduce disk
#   usage and increase speed; the --realcopy option can be used to create
#   real copies instead of hardlinks.  Real copies are forced if the shuffled
#   MSU pack and the source MSU packs are on different hard drives.
#
# - The --dry-run option can be used to make this script print the filesystem
#   commands (deleting, creating, renaming files) it would have executed
#   instead of executing them.

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
"17 - Generic Light World Dungeon",
"18 - Cave",
"19 - Boss Victory",
"20 - Sanctuary",
"21 - Generic Boss",
"22 - Generic Dark World Dungeon",
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

#List of extended MSU dungeon-specific and boss-specific tracks.
extendedmsutracks = list(range(35,62))

#Since the presence of any dungeon/boss-specific track from an extended MSU
#pack overrides the generic pendant/crystal dungeon or generic boss music,
#a basic shuffle always picking track N as that same track N from a random
#pack will result in no boss/dungeon music from a non-extended pack ever
#being chosen if the user has a single extended pack.
#
#To allow dungeon/boss music to be played, the dungeon/boss-specific
#extended MSU tracks are shuffled differently; for each extended
#dungeon/boss-specific track, a pack is chosen randomly, then its
#corresponding dungeon/boss-specific track is chosen if present,
#otherwise, the generic dungeon/boss music from that pack is chosen.
#
#This means that a user that ONLY has non-extended packs won't be able to
#listen to dungeon music to determine crystal/pendant status in modes where
#that applies (since EP/DP/TH would always play light world music from a
#random pack regardless of pendant/crystal status).  To preserve that
#behavior, --basicshuffle can be used.

extendedbackupdict = {
  35: 17, #EP
  36: 17, #DP
  37: 16, #AT
  38: 22, #SP
  39: 22, #PD
  40: 22, #MM
  41: 22, #SW
  42: 22, #IP
  43: 17, #TH
  44: 22, #TT
  45: 22, #TR
  46: 22, #GT
  47: 21, #EP Boss
  48: 21, #DP Boss
  49: 21, #AT Boss
  50: 21, #SP Boss
  51: 21, #PD Boss
  52: 21, #MM Boss
  53: 21, #SW Boss
  54: 21, #IP Boss
  55: 21, #TH Boss
  56: 21, #TT Boss
  57: 21, #TR Boss
  58: 21, #GT Boss
  59: 22, #GT2
  60: 2,  #LW2
  61: 9}  #DW2

higandir = "./higan.sfc"

def delete_old_msu(args, rompath):
    if os.path.exists(f"{rompath}-msushuffleroutput.log"):
        os.remove(f"{rompath}-msushuffleroutput.log")

    logger = logging.getLogger('')
    output_file_handler = logging.FileHandler(f"{rompath}-msushuffleroutput.log")
    logger.addHandler(output_file_handler)

    if (args.dry_run):
        logger.info("DRY RUN MODE: Printing instead of executing.")

    foundsrcrom = False
    foundshuffled = False
    for path in glob.glob('*.sfc'):
        romname = os.path.basename(str(path))
        if romname != "shuffled.sfc" and romname != "higan.sfc":
            srcrom = path
            foundsrcrom = True
        else:
            foundshuffled = True

    if args.higan:
        if os.path.isdir(higandir):
            if args.dry_run:
                logger.info("DRY RUN MODE: Would rmtree " + higandir)
            else:
                shutil.rmtree(higandir)
        if args.dry_run:
            logger.info("DRY RUN MODE: Would make " + higandir + "/msu1.rom")
        else:
            os.mkdir(higandir)
            open(higandir + "/msu1.rom", 'a').close()

    if foundsrcrom and rompath == './shuffled':
        if args.higan:
            if args.dry_run:
                logger.info("DRY RUN MODE: Would copy " + os.path.basename(srcrom) + " to " + higandir + "/program.rom")
            else:
                logger.info("Copying " + os.path.basename(srcrom) + " to " + higandir + "/program.rom")
                shutil.copy(srcrom, higandir + "/program.rom")
        else:
            replace = "Y"
            if foundshuffled:
                replace = str(input("Replace shuffled.sfc with " + os.path.basename(srcrom) + "? [Y/n]") or "Y")
            if (replace == "Y") or (replace == "y"):
                if (args.dry_run):
                    logger.info("DRY RUN: Would rename " + os.path.basename(srcrom) + " to shuffled.sfc.")
                else:
                    logger.info("Renaming " + os.path.basename(srcrom) + " to shuffled.sfc.")
                    shutil.move(srcrom, "./shuffled.sfc")

    if not args.higan:
        for path in glob.glob(f'{rompath}-*.pcm'):
            if (args.dry_run):
                logger.info("DRY RUN: Would remove " + str(path))        
            else:
                os.remove(str(path))

def copy_track(logger, args, srcpath, src, dst, printsrc, rompath):
    if args.higan:
        dstpath = higandir + "/track-" + str(dst) + ".pcm"
    else:
        dstpath = f"{rompath}-{dst}.pcm"

    if printsrc:
        srctitle = titles[src-1]
        shorttitle = srctitle[4:]
        logger.info(titles[dst-1] + ': (' + shorttitle.strip() + ') ' + srcpath)
    else:
        logger.info(titles[dst-1] + ': ' + srcpath)

    if (not args.dry_run):
        if (args.forcerealcopy):
            shutil.copy(srcpath, dstpath)
        else:
            os.link(srcpath, dstpath)

def pick_random_track(logger, args, src, dst, printsrc, rompath):
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
    copy_track(logger, args, str(winner), src, dst, printsrc, rompath)

def generate_shuffled_msu(args, rompath):
    logger = logging.getLogger('')

    if (not os.path.exists(f'{rompath}.msu')):
        logger.info(f"'{rompath}.msu' doesn't exist, creating it.")
        if (not args.dry_run):
            with open(f'{rompath}.msu', 'w'):
                pass

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
    if (args.basicshuffle or args.fullshuffle):
        loopingfoundtracks = [i for i in foundtracks if i not in nonloopingtracks]
    else:
        nongenericshufflelist = nonloopingtracks + extendedmsutracks
        loopingfoundtracks = [i for i in foundtracks if i not in nongenericshufflelist]

    shuffledloopingfoundtracks = loopingfoundtracks.copy()
    random.shuffle(shuffledloopingfoundtracks)
    nonloopingfoundtracks = [i for i in foundtracks if i in nonloopingtracks]

    #For all found non-looping tracks, pick a random track with a matching
    #track number from a random pack in the target directory.
    logger.info("Non-looping tracks:")
    for i in nonloopingfoundtracks:
        srcstr = str(i)
        pick_random_track(logger, args, i, i, False, rompath)

    #For all found looping tracks, pick a random track from a random pack
    #in the target directory, with a matching track number by default, or
    #a shuffled different looping track number if fullshuffle or
    #singleshuffle are enabled.
    logger.info("Looping tracks:")
    for i in loopingfoundtracks:
        if (args.fullshuffle or args.singleshuffle):
            dst = i
            src = shuffledloopingfoundtracks[loopingfoundtracks.index(i)]
            printsrc = True
        else:
            dst = i
            src = i
            printsrc = False
        pick_random_track(logger, args, src, dst, printsrc, rompath)

    if (args.basicshuffle or args.fullshuffle):
        logger.info('Done.')
        return

    logger.info("Extended MSU tracks:")

    #Make a list of all directories with .pcm tracks except this one
    allpacks = list()
    for path in Path(searchdir).rglob('*.pcm'):
        pack = os.path.dirname(str(path))
        name = os.path.basename(str(path))[:8]
        if pack not in allpacks and name != "shuffled":
            allpacks.append(pack)

    if not allpacks:
        logger.info("ERROR: Couldn't find any MSU packs in " + os.path.abspath(str(searchdir)))
        return

    #For each extended track, pick a random directory, if it has either the
    #corresponding extended track or backup generic track, pick it, otherwise
    #pick another random directory.  Try 1000 times then give up (should only
    #fail if running this script where the parent directory contains no
    #completed MSU packs)
    for i in extendedmsutracks:
        foundtrack = ""
        tries = 0
        src = i
        printsrc = False
        while tries < 1000 and not foundtrack:
            tries += 1
            randompack = random.choice(allpacks)
            for path in Path(randompack).rglob("*-" + str(i) + ".pcm"):
                foundtrack = path
                break

            if not foundtrack:
                src = extendedbackupdict[i]
                printsrc = True
                for path in Path(randompack).rglob("*-" + str(src) + ".pcm"):
                    foundtrack = path
                    break

        if not foundtrack:
            logger.info("ERROR: Couldn't find extended track " + str(i) + " or generic track " + str(extendedbackupdict[i]) + " in " + os.path.abspath(str(searchdir)))
            return

        copy_track(logger, args, str(foundtrack), src, i, printsrc, rompath)

def main(args):
    if args.version:
        print("ALttPMSUShuffler version " + __version__)
        return

    for rom in roms:
        args.forcerealcopy = args.realcopy
        try:
            # determine if the supplied rom is ON the same drive as the script. If not, realcopy is mandatory.
            os.path.commonpath([os.path.abspath(rom), __file__])
        except:
            args.forcerealcopy = True
        delete_old_msu(args, rom)
        generate_shuffled_msu(args, rom)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--loglevel', default='info', const='info', nargs='?', choices=['error', 'info', 'warning', 'debug'], help='Select level of logging for output.')
    parser.add_argument('--fullshuffle', help="Choose each looping track randomly from all looping tracks from all packs, rather than the default behavior of only mixing track numbers for dungeon/boss-specific tracks.  Good if you like shop music in Ganon's Tower.", action='store_true', default=False)
    parser.add_argument('--basicshuffle', help='Choose each track with the same track from a random pack.  If you have any extended packs, the dungeon/boss themes from non-extended packs will never be chosen in this mode.  If you only have non-extended packs, this preserves the ability to tell crystal/pendant dungeons by music.', action='store_true', default=False)
    parser.add_argument('--singleshuffle', help='Choose each looping track randomly from all looping tracks from a single MSU pack.  Enter the path to a subfolder in the parent directory containing a single MSU pack.')
    parser.add_argument('--higan', help='Creates files in higan-friendly directory structure.', action='store_true', default=False)
    parser.add_argument('--realcopy', help='Creates real copies of the source tracks instead of hardlinks', action='store_true', default=False)
    parser.add_argument('--dry-run', help='Makes script print all filesystem commands that would be executed instead of actually executing them.', action='store_true', default=False)
    parser.add_argument('--version', help='Print version number and exit.', action='store_true', default=False)

    args, roms = parser.parse_known_args()
    roms = [os.path.splitext(rom)[0] for rom in roms]
    if not roms:
        roms.append('./shuffled')
    args.roms = roms

    if ((args.fullshuffle and args.basicshuffle)) or (args.singleshuffle and (args.fullshuffle or args.basicshuffle)):
        parser.print_help()
        sys.exit()

    # When shuffling a single pack, don't auto-extend non-extended packs.
    if (args.singleshuffle):
        args.basicshuffle = True

    # set up logger
    loglevel = {'error': logging.ERROR, 'info': logging.INFO, 'warning': logging.WARNING, 'debug': logging.DEBUG}[args.loglevel]
    logging.basicConfig(format='%(message)s', level=loglevel)

    main(args)

