"""Classe de plugin: só registra e remove o provider do Processing."""

from qgis.core import QgsApplication

from .provider import ProviderPrefeituraBetim


class PluginPrefeituraBetim:
    def __init__(self, iface):
        self.iface = iface
        self.provider = None

    def initProcessing(self):
        self.provider = ProviderPrefeituraBetim()
        QgsApplication.processingRegistry().addProvider(self.provider)

    def initGui(self):
        self.initProcessing()

    def unload(self):
        if self.provider is not None:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None
