class NumeracaoError(Exception):
    """
    Falha ao numerar um logradouro: topologia impossível (beco sem saída no
    percurso) ou vão entre trechos disjuntos acima da tolerância de gap. Um
    logradouro que dispara isso é pulado; a numeração dos demais segue.
    """
