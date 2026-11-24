"""Manager del passo 9.2: il resoconto della demo su Drive, nella cartella del cliente: link, collaudo, approvazione e fotografie."""

from ._01_CaricaIlResocontoDellaDemoSuDrive import caricaIlResocontoDellaDemoSuDrive


def caricaIlResocontoDellaDemoSuDriveManager(idDrive, pubblicazione, collaudo, approvazione, prove):
    return caricaIlResocontoDellaDemoSuDrive(idDrive, pubblicazione, collaudo, approvazione, prove)
