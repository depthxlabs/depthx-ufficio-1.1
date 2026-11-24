"""Manager del passo 7.9: nelle recensioni nessun nome di chi le ha scritte."""

from ._01_NomiDegliOspitiNelSito import nomiDegliOspitiNelSito


def controlloCheLeRecensioniNonAbbianoIlNomeDiChiLeHaScritteManager(sito, recensioni):
    return nomiDegliOspitiNelSito(sito, recensioni)
