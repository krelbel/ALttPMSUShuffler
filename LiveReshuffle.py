import os

# Helper script for reshuffling a MSU-1 pack every few seconds; works well
# when using MSU packs with emulators, allowing you to experience different
# music whenever the track is next loaded after being reshuffled.
#
# See Main.py for full documentation.

# Number of seconds to wait between reshuffles of the MSU pack
INTERVAL = 10

os.system(f"python Main.py --live {INTERVAL}")

