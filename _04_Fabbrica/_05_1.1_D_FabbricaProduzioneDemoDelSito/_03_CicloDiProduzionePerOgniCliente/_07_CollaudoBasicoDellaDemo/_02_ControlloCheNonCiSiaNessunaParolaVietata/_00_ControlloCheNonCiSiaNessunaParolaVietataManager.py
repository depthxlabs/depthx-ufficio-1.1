"""Manager del passo 7.2: nessuna parola vietata nelle frasi visibili del sito."""

from ._03_ParoleVietateNeiTestiDelSito import paroleVietateNeiTestiDelSito


def controlloCheNonCiSiaNessunaParolaVietataManager(sito, recensioni=()):
    return paroleVietateNeiTestiDelSito(sito, recensioni)
