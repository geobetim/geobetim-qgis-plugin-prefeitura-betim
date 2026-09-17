"""Aplicação de mudanças no buffer de edição da camada, sem gravar em definitivo.

Todos os algoritmos do conjunto seguem o mesmo contrato: põem a camada em edição,
abrem **um** comando de edição, aplicam as mudanças e fecham o comando. Nunca
fazem ``commitChanges()`` — os valores ficam no buffer de edição do QGIS
(visíveis no mapa e na tabela de atributos) e só são persistidos quando o
operador clica em "Salvar edições da camada". "Reverter" desfaz tudo num passo.
"""

from contextlib import contextmanager

from qgis.core import QgsProcessingException


@contextmanager
def edicao_sem_commit(camada, rotulo):
    """Contexto que abre/fecha um comando de edição na camada.

    Uso::

        with edicao_sem_commit(camada, "Remover trechos de passagem"):
            camada.changeGeometry(fid, nova_geom)
            camada.addFeature(nova_feicao)
            camada.deleteFeature(fid_removido)

    Uma exceção dentro do bloco desfaz o comando de edição e propaga. Use
    ``exigir`` em cada escrita: os métodos de edição do QGIS devolvem ``bool`` e
    uma recusa silenciosa deixaria o resumo mentindo ("atualizado" sem gravar).
    """
    if not camada.isEditable() and not camada.startEditing():
        raise QgsProcessingException("Não foi possível colocar a camada em edição.")
    camada.beginEditCommand(rotulo)
    try:
        yield
    except Exception:
        camada.destroyEditCommand()
        raise
    camada.endEditCommand()
    camada.triggerRepaint()


def exigir(ok, mensagem):
    """Levanta ``QgsProcessingException`` se uma escrita na camada foi recusada.

    Dentro de ``edicao_sem_commit`` isso destrói o comando de edição — nada
    fica gravado pela metade.
    """
    if not ok:
        raise QgsProcessingException(
            "O QGIS recusou uma escrita na camada ({0}); nada foi gravado. "
            "Verifique se o atributo é um campo real da camada (não de junção "
            "ou expressão) e se o provider permite edição.".format(mensagem)
        )
