# Exemplos verbatim dos artigos (suíte de fidelidade)

*English guide: [README.md](README.md) — os cabeçalhos dos stubs estão em inglês.*

Cada arquivo `<metodo>.py` desta pasta transcreve o *running example* do artigo
original do método: o grafo da figura, as consultas que o texto destaca e, quando
o artigo os imprime, os rótulos do índice. O runner (`test_runner.py`) valida que
a implementação da biblioteca reproduz tudo isso, em três camadas:

1. **Respostas** — todo par `(u, v)` do grafo transcrito;
2. **Consultas destacadas** — os pares que o texto do artigo discute;
3. **Rótulos impressos** — o índice construído bate com a figura (quando houver).

## Como preencher um stub

1. Abra o PDF e a figura indicados no cabeçalho do arquivo.
2. Siga os passos numerados do cabeçalho (arestas → num_nodes → consultas → rótulos).
3. Rode `pytest tests/paper_examples/test_runner.py -k <metodo> -v`.
4. Interprete a falha:
   - **"transcription error"** = grafo/rótulos mal copiados — reconfira a figura;
   - **qualquer outra falha** = possível bug de fidelidade na biblioteca (reporte!).

Dica: quando a figura rotula vértices por letras, mapeie letras → inteiros
(ordem alfabética) e anote o mapeamento em comentário no próprio stub.

## Como criar um stub para um método ainda sem arquivo

Copie `hl.py` (o exemplo de referência, já preenchido), ajuste `method` (a chave
no `catalog`), a proveniência (`source`, `figure`, `doi`) e o cabeçalho de
instruções. Stubs não preenchidos (`edges` vazio) aparecem como SKIP — nunca
quebram a CI. Métodos ainda sem stub: GRAIL, PLL, TOL, TFLabel, BFL, ChainCover,
TreeSSPI e as linhas de base (TC, BFSDFS — livros-texto, sem figura de exemplo).

## Rótulos (Camada 3)

Só métodos com introspecção implementada suportam `labels` (hoje: `hl`, com
`kind="two_hop"` via `HL.two_hop_labels()`). Se o índice do seu método não
couber em nenhum `kind` existente, as saídas são (nesta ordem):

1. novo `kind` + comparador em `_comparators.py`;
2. `mode="invariant"` (os rótulos construídos precisam apenas induzir a mesma
   alcançabilidade que os do artigo);
3. omitir `labels` — as Camadas 1–2 já validam o método.

Todo comparador roda antes o **cross-check de transcrição**: a alcançabilidade
implicada pelos rótulos copiados do artigo deve bater com a derivada das
arestas copiadas. Divergência = erro de digitação na transcrição, e a mensagem
de erro aponta exatamente os pares em conflito.

## Notas de proveniência

- `docs/paper_166.pdf` é o paper do FELINE (EDBT 2014); `docs/reneveloso.pdf`
  é a tese (144 pp.) — use o paper.
- `docs/scarab.pdf` (SCARAB, SIGMOD 2012) é referência de apoio do HL
  (backbone FastCover), não tem stub próprio.
- No `docs/ferrari.pdf` as legendas das figuras são extraídas na p. 10 desta
  versão do PDF; as figuras em si aparecem antes.
