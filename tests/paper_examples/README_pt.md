# Exemplos verbatim dos artigos (suíte de fidelidade)

*English guide: [README.md](README.md) — os cabeçalhos dos stubs estão em inglês.*

Cada arquivo `<metodo>.py` desta pasta transcreve o **running example do artigo
original do método**: o grafo da figura, as consultas que o texto destaca e,
quando o artigo os imprime, os rótulos do índice. O runner (`test_runner.py`)
valida que a implementação da biblioteca reproduz tudo isso, em três camadas:

| Camada | O que é conferido | Obrigatória? |
|---|---|---|
| 1 — Respostas | `query(u, v)` para **todos** os pares do grafo transcrito | sempre |
| 2 — Consultas destacadas | os pares específicos que o texto do artigo discute | se houver `queries` |
| 3 — Rótulos impressos | o índice construído bate com a figura de rótulos | se houver `labels` |

O exemplo de referência preenchido é o [`hl.py`](hl.py) — leia-o uma vez antes
de preencher seu primeiro stub.

## Início rápido

```bash
# roda a suíte inteira (stubs não preenchidos dão SKIP, nunca falham)
pytest tests/paper_examples/ -v

# roda o exemplo de um único método
pytest tests/paper_examples/test_runner.py -k treecover -v
```

Um stub **não preenchido** reporta (saída real):

```
SKIPPED [1] tests/paper_examples/test_runner.py:44: stub 'treecover' not
filled yet (edges empty) — see README.md in this folder
```

Um stub **preenchido e passando** reporta:

```
tests/paper_examples/test_runner.py::test_paper_example[hl] PASSED
```

## Anatomia de um stub

```python
from _schema import PaperExample, LabelCheck   # LabelCheck só se usar a Camada 3

EXAMPLE = PaperExample(
    method="treecover",          # a chave no catálogo — catalog.methods() lista todas
    source="Agrawal, Borgida, Jagadish, SIGMOD 1989 — ...",   # citação legível
    figure="Figure 3.3, p. 3",   # exatamente qual figura você transcreveu
    doi="10.1145/67544.66950",
    num_nodes=5,                 # maior id de vértice + 1
    edges=[(0, 1), (0, 2)],      # as arestas da figura, verbatim, como (u, v) = u -> v
    queries=[(0, 2, True)],      # pares (u, v, esperado) que o TEXTO destaca
    labels=None,                 # ou um LabelCheck — ver "Camada 3" abaixo
)
```

`reach` (opcional) permite escrever a verdade completa à mão; sem ele, o runner
deriva a alcançabilidade das `edges` por BFS — que é o caso normal.

## Preenchendo um stub, passo a passo

Suponha que a figura do artigo mostre este DAG de 5 vértices, rotulados
`a..e`, com setas `a→b, a→c, b→d, c→d, d→e`:

**1. Mapeie letras para inteiros** (ordem alfabética) e anote o mapeamento:

```python
    # mapeamento de vértices: a=0, b=1, c=2, d=3, e=4
```

**2. Transcreva as arestas** — uma tupla por seta, `(cauda, cabeça)`. Confira
duas vezes a *direção* de cada seta; aresta invertida é o erro mais comum:

```python
    num_nodes=5,
    edges=[(0, 1), (0, 2), (1, 3), (2, 3), (3, 4)],
```

**3. Copie as consultas destacadas.** Se o texto diz *"note que a alcança e,
mas e não alcança a"*, isso vira:

```python
    queries=[(0, 4, True), (4, 0, False)],
```

**4. Rode:**

```bash
pytest tests/paper_examples/test_runner.py -k <metodo> -v
```

Só a Camada 1 já confere os 25 pares deste grafo contra a biblioteca.

## Camada 3: transcrevendo os rótulos do artigo

Só adicione `labels` quando o artigo *imprime* o índice construído na figura
**e** o método tem introspecção implementada (hoje: `hl`, `kind="two_hop"`,
via `HL.two_hop_labels()`). Suponha que a figura imprima esta tabela de
rótulos para o DAG acima:

| v | Lin | Lout |
|---|-----|------|
| a | a   | a, b, c, d |
| e | d, e | e |

Isso vira (aplicando o mapeamento de letras):

```python
    labels=LabelCheck(
        kind="two_hop",
        mode="invariant",        # exact vs invariant: ver abaixo
        expected={
            0: {"Lin": {0}, "Lout": {0, 1, 2, 3}},
            4: {"Lin": {3, 4}, "Lout": {4}},
        },
    ),
```

Observações:

- **Tabela parcial é normal.** Se a figura imprime só alguns vértices (ou tem
  linha `...`), transcreva só esses — a comparação se restringe automaticamente
  aos vértices transcritos.
- **`mode="exact"` vs `mode="invariant"`.** `exact` exige que os rótulos
  construídos sejam iguais aos impressos, conjunto a conjunto — só possível
  quando o artigo fixa a ordem de construção por completo. `invariant` exige
  que os rótulos construídos *induzam a mesma alcançabilidade* dos impressos
  (a escolha certa quando o algoritmo tem liberdade de desempate, como o
  backbone FastCover do HL). Na dúvida, comece com `exact`; se falhar com o
  cross-check passando, mude para `invariant` e explique num comentário.

### Como rótulos decidem alcançabilidade (a regra 2-hop)

`u` alcança `v` **se e somente se** `Lout(u) ∩ Lin(v) ≠ ∅`. Na mini-tabela
acima: `Lout(a) = {a,b,c,d}` e `Lin(e) = {d,e}` se intersectam em `{d}`, logo
`a` alcança `e` — batendo com o grafo (`a→b→d→e`). É essa regra que o
cross-check e o modo `invariant` calculam.

## Interpretando falhas

**"transcription error"** — o grafo e os rótulos que você digitou discordam
entre si. Mensagem real de um stub quebrado de propósito:

```
AssertionError: [hl] Fig. X: transcription error (graph or labels mis-copied
from the paper). Reachability from the transcribed edges and from the
transcribed labels disagree on: [(0, 2)]
```

Os pares listados dizem onde olhar: aqui, as arestas dizem que `0` alcança `2`
mas os rótulos transcritos dizem que não (ou vice-versa). Reabra a figura e
corrija o que foi mal copiado. A biblioteca não participa dessa checagem —
ela compara suas duas transcrições uma contra a outra.

**Falha nas Camadas 1/2** (`query(u,v) = X, paper graph says Y`) — as
transcrições são consistentes, mas a *implementação* discorda do exemplo do
artigo. Primeiro reconfira a figura mais uma vez; se a transcrição estiver
certa, você pode ter encontrado um **bug de fidelidade** — abra uma issue com
o stub.

**Camada 3 `exact` falhando com cross-check passando** — em geral não é bug:
a construção fez escolhas de desempate diferentes (mas válidas) das da rodada
do artigo. Mude para `mode="invariant"` e anote o porquê.

## Criando um stub para um método que ainda não tem

Métodos ainda sem stub: GRAIL, PLL, TOL, TFLabel, BFL, ChainCover, TreeSSPI e
as linhas de base (TC, BFSDFS — métodos de livro-texto, sem figura de exemplo).
Para adicionar um:

1. Consiga o PDF do artigo e localize a figura de running example (em geral
   "Figure 1/2 … example").
2. Copie qualquer stub não preenchido (ex.: `treecover.py`) e renomeie para
   `<chave-do-catalogo>.py` — o runner descobre qualquer `*.py` novo
   automaticamente (nomes começando com `_`, `test_` ou `conftest` são
   excluídos).
3. Atualize `method`, `source`, `figure`, `doi` e o cabeçalho de instruções.
4. Preencha seguindo os passos acima; sem preencher ele só dá SKIP, então
   commitar um stub só com proveniência é ok.

Checklist antes de commitar um stub preenchido:

- [ ] direção de todas as setas conferida duas vezes;
- [ ] mapeamento letra→inteiro (se houver) anotado em comentário;
- [ ] `pytest ... -k <metodo> -v` passando;
- [ ] arestas de leitura difícil sinalizadas em comentário para revisão humana
      (veja o bloco `CAUTION` no `hl.py` como modelo).

## Adicionando um novo kind de rótulo (comparadores)

Se um artigo imprime um índice que não cabe em nenhum `kind` existente
(intervalos, coordenadas 2D, cadeias, ...): adicione uma função comparadora em
`_comparators.py`, registre-a em `COMPARATORS`, e exponha a introspecção
correspondente na implementação (veja `HL.two_hop_labels()` como modelo —
método read-only, espaço de vértices originais, só DAGs). Todo comparador deve
rodar o cross-check de transcrição antes de tocar na implementação. As saídas,
em ordem: novo kind → `mode="invariant"` → omitir `labels` (as Camadas 1–2
seguem validando o método).

## Notas de proveniência

- `docs/paper_166.pdf` é o paper do FELINE (EDBT 2014); `docs/reneveloso.pdf`
  é a tese (144 pp.) — use o paper.
- `docs/scarab.pdf` (SCARAB, SIGMOD 2012) é referência de apoio do HL
  (backbone FastCover), não tem stub próprio.
- No `docs/ferrari.pdf` as legendas das figuras são extraídas na p. 10 desta
  versão do PDF; as figuras em si aparecem antes.
- Dica para figuras densas: renderize em alta resolução e leia por quadrantes,
  ex.: `pdftoppm -f 5 -l 5 -r 600 -png docs/DL.pdf /tmp/fig`.
