import argparse
import logging
import os
from pathlib import Path
import random
import re
import shutil
import glob
import sys
import pprint
import sched, time
import datetime
import websockets
import json
import asyncio
import pickle
from tempfile import TemporaryDirectory

__version__ = '0.8.2'

# Creates a shuffled MSU-1 pack for ALttP Randomizer from one or more source
# MSU-1 packs.
#
# Usage:
#
# 1) Copy this script to a new subdirectory in the directory containing all
#    of your current MSU packs.  For example, if your MSU pack is in
#    `"MSUs\alttp_undertale\alttp_msu-1.pcm"`, the script should be in
#    `"MSUs\ALttPMSUShuffler\Main.py"`.
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
#     2) Run **Main.py** to execute the script to delete any old pack in this
#        directory and generate a new one.  Track names picked will be saved in
#        "shuffled-msushuffleroutput.log" (cleared on reruns)
#
#     3) LIVE RESHUFFLE METHOD: Instead of simply running 
#        **Main.py**, run **LiveReshuffle.py** or run in the command line as
#        "python Main.py --live 10" (or any other positive integer) to
#        generate a new shuffled MSU pack every few seconds.  Will skip
#        replacing any tracks currently being played.  Best if used without
#        the --realcopy option, and best if the shuffled MSU pack and source
#        packs are all on the same hard drive, to avoid excessive disk usage.
#        Edit **LiveReshuffle.py** to set a different reshuffle interval than
#        the 10 second default.
#
#     4) LIVE RESHUFFLE + NOW PLAYING VIEW (EXPERIMENTAL): Run the command
#        line as "python Main.py --live 10 --nowplaying" to run in live
#        reshuffle mode (as described above) while polling qusb2snes for
#        the currently playing MSU pack, printed to console and nowplaying.txt
#        for use as an OBS streaming text source.
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
# - Searches the parent directory of the directory containing the script for
#   all MSU packs to be included in the shuffler by default, but will skip
#   any tracks with "disabled" (case-insensitive) in the directory name or
#   file name; useful for keeping tracks hidden from the shuffler without
#   needing to move them out of the collection entirely.
#
# - Caches the track list in ./trackindex.pkl to avoid reindexing the entire
#   collection every time the script is run.  If run in the command line as
#   "python Main.py --reindex", it will regenerate the track index.  Use this
#   to pick up any new MSU packs for the shuffler.
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

# Globals used by the scheduled reshuffle in live mode (couldn't figure out
# a better way to pass dicts/lists to shuffle_all_tracks when called by
# the scheduler)
global trackindex
trackindex = {}
global nonloopingfoundtracks
nonloopingfoundtracks = list()
global loopingfoundtracks
loopingfoundtracks = list()
global shuffledloopingfoundtracks
shuffledloopingfoundtracks = list()
s = sched.scheduler(time.time, time.sleep)

def delete_old_msu(args, rompath):
    try:
        if os.path.exists(f"{rompath}-msushuffleroutput.log"):
            os.remove(f"{rompath}-msushuffleroutput.log")
    except PermissionError:
        print(f"WARNING: Failed to clear old logfile {rompath}-msushuffleroutput.log")

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
                try:
                    os.remove(str(path))
                except PermissionError:
                    logger.info(f"WARNING: Failed to remove {path}")

def copy_track(logger, srcpath, dst, rompath, dry_run, higan, forcerealcopy, live, tmpdir):
    if higan:
        dstpath = higandir + "/track-" + str(dst) + ".pcm"
    else:
        dstpath = f"{rompath}-{dst}.pcm"

    for match in re.finditer(r'\d+', os.path.basename(srcpath)):
        pass
    srctrack = int(match.group(0))

    if srctrack != dst:
        srctitle = titles[srctrack-1]
        shorttitle = srctitle[4:]
        if not live:
            logger.info(titles[dst-1] + ': (' + shorttitle.strip() + ') ' + srcpath)
    else:
        if not live:
            logger.info(titles[dst-1] + ': ' + srcpath)

    if not dry_run:
        try:
            # Use a temporary file and os.replace to get around the fact that
            # python doesn't have an atomic copy/hardlink with overwrite.
            tmpname = os.path.join(tmpdir, f"tmp{os.path.basename(dstpath)}")
            
            if (forcerealcopy):
                shutil.copy(srcpath, tmpname)
            else:
                os.link(srcpath, tmpname)

            os.replace(tmpname, dstpath)
            return True
        except PermissionError:
            if not live:
                logger.info(f"Failed to copy {srcpath} to {dstpath} during non-live update")
            return False

# Build a dictionary mapping each possible track number to all matching tracks
# in the search directory; do this once, to avoid excess searching later.
#
# In default mode (non-basic/non-full), since we want non-extended MSU packs to
# still have their dungeon/boss music represented in the shuffled pack, match
# the generic backups for each of the extended MSU tracks.
#
# Index format:
# index[2] = ['../msu1/track-2.pcm', '../msu2/track-2.pcm']
def build_index(args):
    global trackindex

    if os.path.exists('trackindex.pkl') and not args.reindex:
        with open('trackindex.pkl', 'rb') as f:
            try:
                trackindex = pickle.load(f)
            except Exception as e:
                print("Failed to load track index")

        if trackindex:
            print("Reusing track index, run with --reindex to pick up any new packs.")
            return

    print("Building index, this should take a few seconds.")
    buildstarttime = datetime.datetime.now()

    if (args.singleshuffle):
        searchdir = args.singleshuffle
    elif args.collection:
        searchdir = args.collection
    else:
        searchdir = '../'

    #For all packs in the target directory, make a list of found track numbers.
    allpacks = list()
    for path in Path(searchdir).rglob('*.pcm'):
        pack = os.path.dirname(str(path))
        if 'disabled' not in pack.lower():
            name = os.path.basename(str(path))[:8]
            if pack not in allpacks and name != "shuffled":
                allpacks.append(pack)

    if not allpacks:
        print("ERROR: Couldn't find any MSU packs in " + os.path.abspath(str(searchdir)))
        return

    for pack in allpacks:
        for track in list(range(1, 62)):
            foundtracks = list()
            for path in Path(pack).rglob(f"*-{track}.pcm"):
                trackname = os.path.basename(str(path))
                if 'disabled' not in trackname.lower():
                    foundtracks.append(str(path))

            #For extended MSU packs, use the backups
            if not args.basicshuffle and not args.fullshuffle:
                if not foundtracks and track in extendedmsutracks:
                    backuptrack = extendedbackupdict[track]
                    for path in Path(pack).rglob(f"*-{backuptrack}.pcm"):
                        trackname = os.path.basename(str(path))
                        if 'disabled' not in trackname.lower():
                            foundtracks.append(str(path))

            trackindex.setdefault(track, []).extend(foundtracks)

    #Uncomment to print index for debugging
    #pp = pprint.PrettyPrinter()
    #pp.pprint(trackindex)

    buildtime = datetime.datetime.now() - buildstarttime
    print(f"Index build took {buildtime.seconds}.{buildtime.microseconds} seconds")

    with open('trackindex.pkl', 'wb') as f:
        # Saving track index as plaintext instead of HIGHEST_PROTOCOL since
        # this is only loaded once, and plaintext may be useful for debugging.
        pickle.dump(trackindex, f, 0)

def shuffle_all_tracks(rompath, fullshuffle, singleshuffle, dry_run, higan, forcerealcopy, live, nowplaying, cooldown, prevtrack):
    logger = logging.getLogger('')
    #For all found non-looping tracks, pick a random track with a matching
    #track number from a random pack in the target directory.
    shufflestarttime = datetime.datetime.now()

    if not live:
        logger.info("Non-looping tracks:")

    if cooldown == 0:
        with TemporaryDirectory(dir='.') as tmpdir:
            oldwinnerdict = {}
            if os.path.exists('winnerdict.pkl'):
                with open('winnerdict.pkl', 'rb') as f:
                    try:
                        oldwinnerdict = pickle.load(f)
                    except Exception as e:
                        print("Failed to load tracklist")
            winnerdict = {}
            for i in nonloopingfoundtracks:
                winner = random.choice(trackindex[i])
                winnerdict[i] = winner
                copy_track(logger, winner, i, rompath, dry_run, higan, forcerealcopy, live, tmpdir)

            #For all found looping tracks, pick a random track from a random pack
            #in the target directory, with a matching track number by default, or
            #a shuffled different looping track number if fullshuffle or
            #singleshuffle are enabled.
            if not live:
                logger.info("Looping tracks:")
            for i in loopingfoundtracks:
                if (args.fullshuffle or args.singleshuffle):
                    dst = i
                    src = shuffledloopingfoundtracks[loopingfoundtracks.index(i)]
                else:
                    dst = i
                    src = i
                winner = random.choice(trackindex[src])
                copied = copy_track(logger, winner, dst, rompath, dry_run, higan, forcerealcopy, live, tmpdir)
                # if copy failed, use OLD winner...
                if copied:
                    winnerdict[i] = winner
                elif i in oldwinnerdict:
                    winnerdict[i] = oldwinnerdict[i]

            with open('winnerdict.pkl', 'wb') as f:
                pickle.dump(winnerdict, f, pickle.HIGHEST_PROTOCOL)
        if live:
            cooldown = int(live)
            if not nowplaying:
                shuffletime = datetime.datetime.now() - shufflestarttime
                print("Reshuffling MSU pack every%s second%s, press ctrl+c or close the window to stop reshuffling. (shuffled in %d.%ds)" %(" " + str(int(live)) if int(live) != 1 else "", "s" if int(live) != 1 else "", shuffletime.seconds, shuffletime.microseconds))

    if live:
        if nowplaying:
            newtrack = read_track(prevtrack)
            prevtrack = newtrack
        s.enter(1, 1, shuffle_all_tracks, argument=(rompath, fullshuffle, singleshuffle, dry_run, higan, forcerealcopy, live, nowplaying, cooldown - 1, prevtrack))

async def recv_loop(ws, recv_queue):
    try:
        async for msg in ws:
            recv_queue.put_nowait(msg)
    finally:
        await ws.close()

# Print the track that's currently playing, and print its pack to
# nowplaying.txt which can be used as a streaming text file source.
def print_pack(path):
    print("Now playing: " + path)
    path_parts = list()
    while True:
        parts = os.path.split(path)
        if parts[0] == path:
            path_parts.insert(0, parts[0])
            break
        elif parts[1] == path:
            path_parts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            path_parts.insert(0, parts[1])
    with open('nowplaying.txt', 'w') as f:
        f.truncate(0)
        print("MSU pack now playing:", file=f)
        print(path_parts[1], file=f)

async def query(prevtrack):
    addr = "ws://localhost:8080"
    try:
        ws = await websockets.connect(addr, ping_timeout=None, ping_interval=None)
    except Exception as e:
        print("Failed to connect to qusb2snes")
        return 0

    devlist = {
        "Opcode": "DeviceList",
        "Space": "SNES"
    }
    await ws.send(json.dumps(devlist))
    reply = json.loads(await ws.recv())
    devices = reply['Results'] if 'Results' in reply and len(reply['Results']) > 0 else None
    if not devices:
        print("Failed to connect to SNES through qusb2snes")
        await ws.close()
        return 0

    device = devices[0]
    attachreq = {
        "Opcode": "Attach",
        "Space": "SNES",
        "Operands": [device]
    }
    await ws.send(json.dumps(attachreq))

    recv_queue = asyncio.Queue()
    recv_task = asyncio.create_task(recv_loop(ws, recv_queue))
    WRAM_START = 0xF50000

    # Current MSU is $010B, per https://github.com/KatDevsGames/z3randomizer/blob/master/msu.asm#L126
    REG_CURRENT_MSU_TRACK = 0x010B

    address = WRAM_START + REG_CURRENT_MSU_TRACK
    size = 1
    readreq = {
        "Opcode": "GetAddress",
        "Space": "SNES",
        "Operands": [hex(address)[2:], hex(size)[2:]]
    }
    await ws.send(json.dumps(readreq))
    data = bytes()
    while len(data) < 1:
        try:
            data += await asyncio.wait_for(recv_queue.get(), 1)
        except asyncio.TimeoutError:
            break

    track = 0
    if len(data) != 1:
        print("Failed to query REG_CURRENT_MSU_TRACK")
    else:
        track = int(data[0])

    if track != 0 and track != prevtrack:
        if os.path.exists('winnerdict.pkl'):
            winnerdict = {}
            with open('winnerdict.pkl', 'rb') as f:
                try:
                    winnerdict = pickle.load(f)
                    print_pack(str(winnerdict[track]))
                except Exception as e:
                    print("Failed to load tracklist")

    await ws.close()
    return track

# Read the currently playing track over qusb2snes.
# TODO: This currently opens up a new qusb2snes connection every second.
# Eventually this should be smarter by keeping one connection alive instead.
def read_track(prevtrack):
    track = asyncio.get_event_loop().run_until_complete(query(prevtrack))
    return track

def generate_shuffled_msu(args, rompath):
    logger = logging.getLogger('')

    if (not os.path.exists(f'{rompath}.msu')):
        logger.info(f"'{rompath}.msu' doesn't exist, creating it.")
        if (not args.dry_run):
            with open(f'{rompath}.msu', 'w'):
                pass

    global nonloopingfoundtracks
    global loopingfoundtracks
    global shuffledloopingfoundtracks

    foundtracks = list()
    for key in trackindex:
        if trackindex[key]:
            foundtracks.append(key)
    foundtracks = sorted(foundtracks)

    #Separate this list into looping tracks and non-looping tracks, and make a
    #shuffled list of the found looping tracks.
    loopingfoundtracks = [i for i in foundtracks if i not in nonloopingtracks]

    shuffledloopingfoundtracks = loopingfoundtracks.copy()
    random.shuffle(shuffledloopingfoundtracks)
    nonloopingfoundtracks = [i for i in foundtracks if i in nonloopingtracks]

    if args.live:
        s.enter(1, 1, shuffle_all_tracks, argument=(rompath, args.fullshuffle, args.singleshuffle, args.dry_run, args.higan, args.forcerealcopy, args.live, args.nowplaying, int(args.live), 0))
        s.run()
    else:
        shuffle_all_tracks(rompath, args.fullshuffle, args.singleshuffle, args.dry_run, args.higan, args.forcerealcopy, args.live, args.nowplaying, 0, 0)
        logger.info('Done.')

def main(args):
    print("ALttPMSUShuffler version " + __version__)

    if args.version:
        return

    build_index(args)

    for rom in args.roms:
        args.forcerealcopy = args.realcopy
        try:
            # determine if the supplied rom is ON the same drive as the script. If not, realcopy is mandatory.
            os.path.commonpath([os.path.abspath(rom), os.path.abspath(__file__)])
        except:
            print(f"Failed to find common path between {os.path.abspath(rom)} and {os.path.abspath(__file__)}, forcing real copies.")
            args.forcerealcopy = True

        if args.live and args.forcerealcopy:
            print("WARNING: live updates with real copies will cause a LOT of disk usage.")

        delete_old_msu(args, rom)
        generate_shuffled_msu(args, rom)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--loglevel', default='info', const='info', nargs='?', choices=['error', 'info', 'warning', 'debug'], help='Select level of logging for output.')
    parser.add_argument('--fullshuffle', help="Choose each looping track randomly from all looping tracks from all packs, rather than the default behavior of only mixing track numbers for dungeon/boss-specific tracks.  Good if you like shop music in Ganon's Tower.", action='store_true', default=False)
    parser.add_argument('--basicshuffle', help='Choose each track with the same track from a random pack.  If you have any extended packs, the dungeon/boss themes from non-extended packs will never be chosen in this mode.  If you only have non-extended packs, this preserves the ability to tell crystal/pendant dungeons by music.', action='store_true', default=False)
    parser.add_argument('--singleshuffle', help='Choose each looping track randomly from all looping tracks from a single MSU pack.  Enter the path to a subfolder in the parent directory containing a single MSU pack.')
    parser.add_argument('--higan', help='Creates files in higan-friendly directory structure.', action='store_true', default=False)
    parser.add_argument('--realcopy', help='Creates real copies of the source tracks instead of hardlinks', action='store_true', default=False)
    parser.add_argument('--dry-run', help='Makes script print all filesystem commands that would be executed instead of actually executing them.', action='store_true', default=False)
    parser.add_argument('--live', help='The interval at which to re-shuffle the entire pack, in seconds; will skip tracks currently in use.')
    parser.add_argument('--nowplaying', help='EXPERIMENTAL: During live reshuffling, connect to qusb2snes to print the currently playing MSU pack to console and nowplaying.txt', action='store_true', default=False)
    parser.add_argument('--reindex', help='Rebuild the index of MSU packs, this must be run to pick up any new packs or moved/deleted files in existing packs!', action='store_true', default=False)
    parser.add_argument('--collection', help='Point script at another directory to find root of MSU packs. Only useful if used with --reindex.')
    parser.add_argument('--version', help='Print version number and exit.', action='store_true', default=False)

    romlist = list()
    args, roms = parser.parse_known_args()
    for rom in roms:
        if not os.path.exists(rom):
            print(f"ERROR: Unknown argument {rom}")
            parser.print_help()
            sys.exit()

        romlist.append(os.path.splitext(rom)[0])

    if not romlist:
        romlist.append('./shuffled')

    args.roms = romlist

    if ((args.fullshuffle and args.basicshuffle)) or (args.singleshuffle and (args.fullshuffle or args.basicshuffle)):
        parser.print_help()
        sys.exit()

    if args.live and int(args.live) < 1:
        print("WARNING, can't choose live updates shorter than 1 second, defaulting to 1 second")
        args.live = 1

    # When shuffling a single pack, don't auto-extend non-extended packs.
    if (args.singleshuffle):
        args.basicshuffle = True

    # set up logger
    loglevel = {'error': logging.ERROR, 'info': logging.INFO, 'warning': logging.WARNING, 'debug': logging.DEBUG}[args.loglevel]
    logging.basicConfig(format='%(message)s', level=loglevel)

    main(args)

