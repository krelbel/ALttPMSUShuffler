import logging
import argparse
import os
import random
from pathlib import Path
import shutil

__version__ = '0.1-dev'

# Finds all PCM files in all subdirectories of the parent directory of this
# script, and creates a new shuffled full MSU-1 pack for ALttP Randomizer;
# for each of the 61 tracks, it finds all matching *-$N.pcm tracks from all
# MSU packs in all subdirectories of the parent directory and picks one at
# random to copy to this directory as shuffled-$N.pcm.
#
# Usage:
# 1) Copy this script to a new subdirectory in the directory containing all
#    of your current MSU packs
# 2) python Main.py in terminal to execute the script to delete any old pack
#    in this directory and generate a new one
# 3) (first time only) Create a new empty file named "shuffled.msu" in this
#    directory
# 4) Copy the ALttP Randomizer ROM (with background music enabled) to this
#    directory and rename it to "shuffled.sfc".  Load it in an MSU-compatible
#    emulator (works well with Snes9x 1.60)

def delete_old_msu(args):
    for path in Path('./').rglob('*.pcm'):
        os.remove(str(path))

def generate_shuffled_msu(args):
    logger = logging.getLogger('')
    for i in range(61):
        istr = str(i + 1)
        match = "*-" + istr + ".pcm"
        dstname = "./shuffled-" + istr + ".pcm"

        l = list()
        for path in Path('../').rglob(match):
            l.append(path)

        winner = random.choice(l)
        logger.info('Picked: ' + str(winner))
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

