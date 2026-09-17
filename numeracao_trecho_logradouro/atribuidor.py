"""Atribuição do número sequencial por segmento.

Percorre a ordem final; para cada par consecutivo, incrementa o número se os
dois não compartilham nó (salto) ou o nó compartilhado é um cruzamento; caso
contrário (nó de passagem) o trecho herda o número do anterior. Começa em 1 e
grava o inteiro cru (``1``, ``2``, ...).
"""


def atribuir(ordem, grafo):
    """
    ``ordem``: lista de ids de trecho na ordem espacial.
    ``grafo``: ``GrafoLogradouro`` já com ``definir_alvo`` chamado para este código.
    Devolve ``dict`` ``{id_trecho: numero_sequencial_inteiro}``.
    """
    numeros = {}
    n = 0
    for i, id_trecho in enumerate(ordem):
        if i == 0:
            n = 1
        else:
            no = grafo.no_compartilhado(ordem[i - 1], id_trecho)
            if no < 0 or no in grafo.cruzamentos:
                n += 1
        numeros[id_trecho] = n
    return numeros
