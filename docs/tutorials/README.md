# Tutoriais do PortalCMJ

Esta pasta reúne os tutoriais do projeto: textos que explicam como uma parte do sistema funciona e
por que ela é assim. Cada um tem o próprio público e a própria profundidade.

## Tutoriais

| Tutorial | Para quem | O que cobre |
| --- | --- | --- |
| [Frontend v8](./frontend/v8/README.md) | Quem está começando em Django e Vue | Passo a passo: constrói uma tela pequena no v8, da primeira página aos testes |
| [Chat RAG](./rag/README.md) | Quem vai manter ou evoluir o chat com I.A. | Texto denso e técnico: arquitetura, ingestão, recuperação híbrida, WebSocket e LLM, modelos, operação, diagnóstico e avaliação |

## O que um tutorial é, e o que não é

O projeto tem três tipos de documento, e cada um responde a uma pergunta:

| Tipo | Onde fica | Pergunta |
| --- | --- | --- |
| Spec | `docs/specs/` | O que o sistema deve fazer? São as regras, ligadas aos testes |
| Guia | `docs/backend/`, `docs/frontend/`, `docs/commands/`, `docs/testing/` | Como se usa? É a referência rápida para quem já conhece o assunto |
| Tutorial | `docs/tutorials/` | Como funciona, e por quê? Explica, com o contexto que os outros dois dispensam |

Um tutorial não define regra. Quando ele e uma spec disserem coisas diferentes, vale a spec, e o
tutorial é que está desatualizado.

## Como estão organizados

Cada tutorial fica numa pasta própria, com um `README.md` que serve de índice e arquivos numerados
na ordem de leitura. Os de frontend ficam em `frontend/<versão>/`.
