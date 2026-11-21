---
name: spec-nova
description: Conduz uma funcionalidade nova da spec ao código. Escreve em docs/specs as regras desejadas e os requisitos de segurança modelados antes do código, resolve as dúvidas com o responsável, implementa com a regra de negócio concentrada numa classe de serviço e testes ligados às regras, e revisa a segurança do código escrito. Use ao criar uma funcionalidade ou capacidade que ainda não existe. Para documentar comportamento existente, use spec-legado.
---

# Funcionalidade nova: da spec ao código

A spec vem antes do código. Ela nasce com regras `[desejado]`, passa a `[acordado]` com decisão
humana e termina `[implementado]`, com teste para cada regra.

Antes de começar, leia `docs/specs/README.md`: cabeçalho, marcadores, IDs, ligação com testes,
varredura de segurança, severidade e publicação valem aqui.

## Limites

- Não leia `.env` nem credenciais, e não use dados de produção.
- Não implemente antes de as dúvidas que afetam a implementação estarem resolvidas.
- Não reformate arquivos fora do escopo.
- Siga o `CLAUDE.md`: migrations só por `makemigrations`, task Celery com `queue=`, frontend novo no
  v6 (o v8 só quando o pedido citar o v8), model em CRUD com entrada em `layouts.yaml`, grupos em
  `map_rules.py`.

## Onde fica cada regra

Concentre ao máximo a regra de negócio numa classe de serviço. As demais camadas fazem só o
essencial do seu propósito.

O serviço fica em `<app>/services/s_<assunto>.py` no app mais adequado ao que está sendo
implementado. Crie a pasta `services/` se ela não existir. O padrão de referência é
`cmj/loa/services/`. A escolha do app entra na spec, no Escopo ou como dúvida.

| Camada | Faz | Não faz |
| --- | --- | --- |
| Serviço | Regras de negócio, decisões por estado ou fase, cálculos, orquestração das escritas, permissão por objeto (quem pode fazer isto com este registro) | Ler `request`, montar resposta HTTP, renderizar |
| Model | Campos, relações, integridade do próprio registro em `clean()` | Regra que envolve outros registros ou o usuário |
| View, ViewSet, `@action` | Autenticação e permissão de acesso à rota, validação da entrada por form ou serializer, chamada ao serviço, resposta | Decidir regra ou repetir a que está no serviço |
| Form, serializer | Formato e validação de campo | Regra entre registros |
| Task Celery, command, consumer | Receber ids e chamar o mesmo serviço, que revalida permissão e estado | Ter caminho próprio de regra |
| Signal | Efeito técnico: cache, índice | Regra de negócio |
| Frontend | Apresentação e UX, como esconder o botão que o backend recusaria | Ser a única barreira ou calcular regra que o backend não confere |

Consequências:

- Todo ponto de entrada chama o **mesmo** método do serviço, para que a regra e a permissão por
  objeto valham em todos. Isso resolve boa parte do item 1 da varredura (acesso e IDOR) por
  construção.
- As evidências das regras na spec apontam para o serviço. O ponto de entrada aparece nos
  requisitos de acesso.
- As regras de negócio são testadas direto no serviço, sem HTTP. Por ponto de entrada, bastam os
  testes de acesso e o de que ele delega ao serviço.
- O serviço recebe o usuário como parâmetro explícito quando a regra depende dele, nunca o
  `request`.

## Processo

### 1. Recorte e leitura

1. Delimite a capacidade. Se o pedido for amplo, proponha o recorte antes de seguir.
2. Leia a documentação da área: `docs/backend/convencoes.md`, `docs/frontend/v6.md` (ou
   `docs/frontend/v8.md`, se o pedido for no v8) e as specs do domínio em `docs/specs/`.
3. Localize o que será reaproveitado: `Crud`, `MasterDetailCrud`, mixins de `cmj/mixins.py`,
   `@customize` da API, stores do v6, serviços existentes.
4. Liste o legado que a funcionalidade toca. Comportamento legado sem spec que será alterado: rode a
   `spec-legado` só desse trecho, ou registre-o como dúvida.

### 2. Spec `[desejado]`

Escreva `docs/specs/<dominio>/<capacidade>.md` com `Status: desejado`, no formato abaixo.

Modele as ameaças antes do código. Para cada ponto de entrada planejado, responda os 7 itens da
varredura de `docs/specs/README.md` e transforme cada resposta em regra testável, por exemplo:

- anônimo recebe 403 no endpoint X; autor só altera os próprios registros;
- a API não serializa `cpf` nem `owner`; o filtro Y não enumera dados pessoais;
- o PDF embute apenas arquivos de mídia permitidos; upload aceita só os tipos Z;
- a task revalida permissão e estado pelo serviço;
- a geração por IA exige autenticação e consome cota.

Esses requisitos são regras comuns, com o prefixo do domínio e sem `-SEG-`: o código ainda não
existe, logo não são falha publicada.

### 3. Dúvidas

Apresente as dúvidas uma por vez, cada uma com a opção recomendada. Registre a decisão na spec e só
mude uma regra para `[acordado]` com confirmação explícita do responsável. Pare antes de implementar
enquanto houver dúvida que afete a implementação.

### 4. Implementação

1. Escreva primeiro os testes dos requisitos de segurança: anônimo, autenticado sem vínculo, outro
   autor e operador, para cada ponto de entrada.
2. Escreva os testes das regras de negócio contra o serviço.
3. Implemente o serviço, depois os pontos de entrada finos.
4. Ligue cada teste à regra com `@pytest.mark.spec("<ID>")`.
5. Rode só os testes do que mudou (`--create-db` se mudou model) e `python manage.py check`.
6. Formate com black e isort só os arquivos alterados.

### 5. Revisão de segurança do código escrito

Reaplique a varredura ao diff, não ao plano. Procure pontos de escrita ou leitura que surgiram na
implementação, campos expostos pelo `drfautoapi`, `@action` sem permissão própria e regra que ficou
fora do serviço.

- Falha no código novo: corrija antes do commit e cubra com teste.
- Regra fora do serviço: mova-a para o serviço antes do commit.
- Falha no legado alcançado: registre-a como risco `-SEG-` e siga a seção `Publicação` de
  `docs/specs/README.md`. Risco Crítico confirmado é avisado ao usuário imediatamente.

### 6. Fechamento

1. Regras com teste passam a `[implementado]`. Atualize `Status`, `Última verificação`,
   `Código principal` e `Testes`.
2. Confira se todo `arquivo:linha` citado continua correto.
3. Domínio novo em `docs/specs/`: acrescente a spec à seção Documentação do `CLAUDE.md`.
4. Não rode `npm run build` nem faça push.

## Formato

```markdown
# <Domínio>: <capacidade>

Status: desejado
Última verificação: AAAA-MM-DD (commit `<hash>`)
Código principal: `<caminhos>` ou a criar
Testes: `<caminhos>` ou a criar

## Escopo
App que recebe o serviço, pontos de entrada planejados, legado tocado.
## Regras
- PREFIXO-001 [desejado] Regra em uma frase. Evidência: a criar, ou `arquivo:linha` do serviço.
## Requisitos de segurança
- PREFIXO-020 [desejado] Quem pode o quê, por qual ponto de entrada. Item da varredura: 1.
## Riscos de segurança
Só para falhas encontradas no legado alcançado, no formato de `docs/specs/README.md`.
## Dúvidas
- D1. Contexto, opções e recomendação. Decisão: pendente.
## Fora do escopo
```

## Ao terminar

Informe, nesta ordem: riscos encontrados no legado, requisitos de segurança e o teste que cobre cada
um, regras sem teste e dúvidas ainda abertas.
