"""Avvia yt-dlp dall'ambiente Python del motore, con i percorsi brevi di Windows."""

import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "_01_StrumentiDelMotore", "_04_CoordinatoreDelMotore"))

import _02_PercorsiChiaviEFunzioniComuni  # percorsi brevi per le librerie compilate

import yt_dlp

sys.exit(yt_dlp.main(sys.argv[1:]))
