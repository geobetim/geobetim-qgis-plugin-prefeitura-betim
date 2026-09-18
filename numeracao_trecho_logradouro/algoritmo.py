"""Algoritmo do Processing: numera os trechos de cada logradouro.

Percorre os ``COD_LOGRADOURO`` em escopo e, para cada um, ordena seus trechos
pela ordem espacial e grava o número sequencial inteiro por segmento num
atributo da própria camada (na edição).
"""

from qgis.core import (
    NULL,
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterField,
    QgsProcessingParameterNumber,
    QgsProcessingParameterVectorLayer,
    QgsRectangle,
)
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from ..shared.camada import (
    avisar_sem_codigo,
    avisar_trechos_degenerados,
    exigir_crs_metrico,
    ler_camada,
)
from ..shared.edicao import edicao_sem_commit, exigir
from . import (
    GrafoLogradouro,
    NumeracaoError,
    SequenciadorAutomatico,
    atribuir,
    parse_geometria,
)

_TIPOS_INTEIROS = (
    QVariant.Int,
    QVariant.LongLong,
    QVariant.UInt,
    QVariant.ULongLong,
    QVariant.Double,
)


class NumeracaoPorLogradouroAlgorithm(QgsProcessingAlgorithm):
    INPUT = "INPUT"
    APENAS_SELECIONADAS = "APENAS_SELECIONADAS"
    SOBRESCREVER = "SOBRESCREVER"
    CAMPO_CODIGO = "CAMPO_CODIGO"
    CAMPO_SEQUENCIAL = "CAMPO_SEQUENCIAL"
    TOL_VERTICE = "TOL_VERTICE"
    TOL_GAP = "TOL_GAP"

    # -- identidade --------------------------------------------------------

    def name(self):
        return "numerar_por_logradouro"

    def displayName(self):
        return self.tr("Numeração de trechologradouro por logradouro")

    def group(self):
        return self.tr("Trecho logradouro")

    def groupId(self):
        return "trechologradouro"

    def shortHelpString(self):
        return self.tr(
            "Numera os trechos de cada logradouro seguindo a ordem espacial e "
            "grava o número sequencial inteiro por segmento no atributo "
            "escolhido. O número começa em 1 em cada logradouro, avança a cada "
            "cruzamento e se repete entre trechos contíguos do mesmo segmento. "
            "Trechos desconectados do mesmo logradouro são encadeados pela ponta "
            "mais próxima, dentro da tolerância de gap.\n\n"
            "Por padrão ('apenas selecionadas' marcado) processa os "
            "COD_LOGRADOURO das feições selecionadas (cada um por inteiro); "
            "desmarque a opção para processar todos os COD_LOGRADOURO "
            "distintos da camada.\n\n"
            "Um COD_LOGRADOURO que já tenha o atributo do número sequencial "
            "preenchido em pelo menos um trecho é ignorado — a menos que "
            "'Sobrescrever numeração' esteja marcado, quando todo COD_LOGRADOURO "
            "em escopo é renumerado e os valores existentes são substituídos. "
            "Use isso para reconciliar a numeração de logradouros que tiveram a "
            "geometria dos trechos alterada.\n\n"
            "Os valores são aplicados na edição da camada — ficam visíveis no "
            "mapa mas só são gravados em definitivo quando você clicar em "
            "'Salvar edições da camada'. Antes disso dá para inspecionar e "
            "reverter tudo de uma vez.\n\n"
            "Trechos com o código do logradouro nulo são desconsiderados.\n\n"
            "A camada precisa estar em CRS projetado (unidade em metros) e o "
            "atributo do número sequencial precisa ser numérico (inteiro ou "
            "real — o valor gravado é sempre o inteiro)."
        )

    def createInstance(self):
        return NumeracaoPorLogradouroAlgorithm()

    def flags(self):
        # Grava direto na camada do projeto — não roda fora da thread principal.
        return super().flags() | QgsProcessingAlgorithm.FlagNoThreading

    def tr(self, texto):
        return QCoreApplication.translate("NumeracaoPorLogradouroAlgorithm", texto)

    # -- parâmetros ------------------------------------------------------

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.INPUT,
                self.tr("Camada de trechos-logradouros"),
                [QgsProcessing.TypeVectorLine],
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.APENAS_SELECIONADAS,
                self.tr(
                    "Numerar apenas os logradouros das feições selecionadas "
                    "(desmarque para processar a camada inteira)"
                ),
                defaultValue=True,
            )
        )
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SOBRESCREVER,
                self.tr(
                    "Sobrescrever numeração (renumera mesmo com o número "
                    "sequencial já preenchido)"
                ),
                defaultValue=False,
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.CAMPO_CODIGO,
                self.tr("Atributo do código do logradouro"),
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.Any,
            )
        )
        self.addParameter(
            QgsProcessingParameterField(
                self.CAMPO_SEQUENCIAL,
                self.tr("Atributo do número sequencial do trecho (inteiro)"),
                parentLayerParameterName=self.INPUT,
                type=QgsProcessingParameterField.Numeric,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOL_VERTICE,
                self.tr("Tolerância para interseção de vértices (m)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=0.05,
                minValue=0.0,
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                self.TOL_GAP,
                self.tr("Tolerância para gap entre trechos do mesmo logradouro (m)"),
                type=QgsProcessingParameterNumber.Double,
                defaultValue=30.0,
                minValue=0.0,
            )
        )

    # -- execução ------------------------------------------------------

    def processAlgorithm(self, parameters, context, feedback):
        camada = self.parameterAsVectorLayer(parameters, self.INPUT, context)
        if camada is None:
            raise QgsProcessingException(
                self.tr(
                    "A entrada precisa ser uma camada vetorial do projeto — o "
                    "resultado é gravado nela."
                )
            )
        apenas_selecionadas = self.parameterAsBool(
            parameters, self.APENAS_SELECIONADAS, context
        )
        sobrescrever = self.parameterAsBool(parameters, self.SOBRESCREVER, context)

        exigir_crs_metrico(camada)

        nome_codigo = self.parameterAsString(parameters, self.CAMPO_CODIGO, context)
        nome_sequencial = self.parameterAsString(
            parameters, self.CAMPO_SEQUENCIAL, context
        )
        tol_vertice = self.parameterAsDouble(parameters, self.TOL_VERTICE, context)
        tol_gap = self.parameterAsDouble(parameters, self.TOL_GAP, context)

        campos = camada.fields()
        idx_codigo = campos.indexFromName(nome_codigo)
        idx_sequencial = campos.indexFromName(nome_sequencial)
        if idx_codigo < 0 or idx_sequencial < 0:
            raise QgsProcessingException(
                self.tr("Atributo de código ou de número sequencial não encontrado.")
            )
        if campos.at(idx_sequencial).type() not in _TIPOS_INTEIROS:
            raise QgsProcessingException(
                self.tr(
                    "O atributo do número sequencial precisa ser numérico "
                    "(inteiro ou real); o valor gravado é sempre o inteiro."
                )
            )

        # -- lê a camada inteira (a operação pressupõe ela carregada) --------
        feedback.pushInfo(self.tr("Lendo a camada..."))
        leitura = ler_camada(
            camada, nome_codigo, campos_extra=(nome_sequencial,), feedback=feedback
        )
        if feedback.isCanceled():
            return {}
        avisar_sem_codigo(leitura, feedback)
        geom_por_id = leitura.geom_por_id
        cod_por_id = leitura.cod_por_id
        por_codigo = leitura.por_codigo
        idx_feicoes = leitura.indice_espacial
        seq_preenchido = {
            fid: (valor is not None and valor != NULL)
            for fid, valor in leitura.valor_extra[nome_sequencial].items()
        }

        # -- escopo: COD_LOGRADOURO da camada inteira ou da seleção --------
        if apenas_selecionadas:
            fids_sel = camada.selectedFeatureIds()
            if not fids_sel:
                raise QgsProcessingException(
                    self.tr(
                        "Nenhuma feição selecionada na camada — marque as feições "
                        "ou desligue a opção 'apenas selecionadas'."
                    )
                )
            codigos_escopo = {
                cod_por_id[fid] for fid in fids_sel if fid in cod_por_id
            }
        else:
            codigos_escopo = set(por_codigo.keys())

        # -- descarta os já numerados (a menos que "sobrescrever") ----------
        a_numerar = []
        cods_ignorados = []
        for cod in codigos_escopo:
            ids = por_codigo.get(cod, [])
            if not ids:
                continue
            if not sobrescrever and any(seq_preenchido[i] for i in ids):
                cods_ignorados.append(cod)
            else:
                a_numerar.append(cod)
        ignorados = len(cods_ignorados)

        feedback.pushInfo(
            self.tr(
                "{0} logradouro(s) em escopo · {1} já numerado(s) (ignorados) · "
                "{2} a numerar."
            ).format(len(codigos_escopo), ignorados, len(a_numerar))
        )
        # Descarte por "já numerado" tem que ser visível: é a causa mais comum
        # de "rodou, não deu erro e não gravou nada".
        if cods_ignorados and apenas_selecionadas:
            feedback.pushWarning(
                self.tr(
                    "Logradouro(s) selecionado(s) já numerado(s) e ignorado(s): "
                    "{0}. Ligue 'Sobrescrever numeração' para renumerar."
                ).format(", ".join(str(c) for c in sorted(cods_ignorados, key=str)))
            )
        if not a_numerar:
            feedback.pushWarning(
                self.tr(
                    "Nada foi gravado: todo logradouro em escopo já tem o número "
                    "sequencial preenchido. Ligue 'Sobrescrever numeração' para "
                    "renumerar."
                )
            )
            return {}

        # -- grafo compartilhado da vizinhança dos códigos a numerar --------
        bbox = QgsRectangle()
        for cod in a_numerar:
            for fid in por_codigo[cod]:
                bbox.combineExtentWith(geom_por_id[fid].boundingBox())
        bbox.grow(tol_vertice)
        ids_vizinhanca = idx_feicoes.intersects(bbox)

        feedback.pushInfo(
            self.tr("Montando o grafo ({0} trechos na vizinhança)...").format(
                len(ids_vizinhanca)
            )
        )
        parseados = {}
        for fid in ids_vizinhanca:
            try:
                parseados[fid] = parse_geometria(
                    fid, cod_por_id[fid], geom_por_id[fid]
                )
            except NumeracaoError as ex:
                feedback.pushWarning(str(ex))
        grafo = GrafoLogradouro(parseados.values(), tol_vertice)

        # -- numera cada logradouro ------------------------------------
        resultado = {}
        numerados = 0
        falhados = 0
        total = len(a_numerar)
        for i, cod in enumerate(a_numerar):
            if feedback.isCanceled():
                break
            feedback.setProgress(int(100 * i / total))

            ids = por_codigo[cod]
            if any(fid not in parseados for fid in ids):
                feedback.pushWarning(
                    self.tr(
                        "COD_LOGRADOURO {0}: algum trecho ficou fora do grafo; pulado."
                    ).format(cod)
                )
                falhados += 1
                continue

            alvo = [parseados[fid] for fid in ids]
            try:
                grafo.definir_alvo(alvo)
                ordem = SequenciadorAutomatico(cod, alvo, grafo, tol_gap).run()
                numeros = atribuir(ordem, grafo)
            except NumeracaoError as ex:
                feedback.pushWarning("COD_LOGRADOURO {0}: {1}".format(cod, ex))
                falhados += 1
                continue

            avisar_trechos_degenerados(feedback, cod, grafo.degenerados)

            resultado.update(numeros)
            numerados += 1

        # -- aplica na EDIÇÃO da camada (sem gravar definitivamente) --------
        # Os valores vão para o buffer de edição do QGIS: ficam visíveis no
        # mapa (label, tabela de atributos) mas só são persistidos quando o
        # usuário clicar em "Salvar edições da camada". Assim ele inspeciona
        # antes, e pode reverter tudo de uma vez (é um único passo de desfazer).
        if resultado:
            with edicao_sem_commit(
                camada, self.tr("Numeração de trechos-logradouros")
            ):
                for fid, n in resultado.items():
                    exigir(
                        camada.changeAttributeValue(fid, idx_sequencial, int(n)),
                        "changeAttributeValue, feição {0}".format(fid),
                    )

        feedback.pushInfo(
            self.tr(
                "Concluído: {0} numerado(s) · {1} ignorado(s) por já numerados · "
                "{2} com falha."
            ).format(numerados, ignorados, falhados)
        )
        if resultado:
            feedback.pushInfo(
                self.tr(
                    "{0} trecho(s) atualizado(s) na EDIÇÃO da camada. Revise no "
                    "mapa e use 'Salvar edições da camada' para gravar em "
                    "definitivo, ou 'Reverter' para desfazer."
                ).format(len(resultado))
            )
        return {}
