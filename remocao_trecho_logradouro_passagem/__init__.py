"""Algoritmo do Processing: remoção de trechos de passagem.

Colapsa cada segmento de passagem de um logradouro (trechos ligados só por nós de
passagem) num trecho só: mantém o maior, estende sua geometria pelos vértices dos
demais e apaga o resto. Opcionalmente divide os trechos colapsados nas
interseções com camadas auxiliares, gerando registros novos. Aplica tudo no
buffer de edição da camada, sem gravar em definitivo.
"""
