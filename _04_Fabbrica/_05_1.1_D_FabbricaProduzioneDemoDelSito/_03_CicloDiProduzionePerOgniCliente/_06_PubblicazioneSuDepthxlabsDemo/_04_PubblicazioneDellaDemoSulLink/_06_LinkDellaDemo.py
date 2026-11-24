"""Il link pubblico della demo del cliente."""

LINK_DELLE_DEMO = "https://www.depthxlabs.com/demo/{}/"


def linkDellaDemo(nome):
    return LINK_DELLE_DEMO.format(nome)
