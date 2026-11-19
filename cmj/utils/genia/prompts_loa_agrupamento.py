"""
Prompts da consolidação de finalidades em ementa de emenda coletiva (LOA).

Campo de formatação: {ementas}, uma finalidade por linha, prefixada com "- ".
O prompt em uso é o indicado em IAEmentaEmendaColetiva.prompt_template; o
outro fica como histórico.
"""

# Moldado para o contexto legislativo/orçamentário.
PROMPT_V0 = """
Você receberá anotações brutas de emendas parlamentares com redundâncias, ruídos de sistema e repetições.

SUA MISSÃO:
Consolidar a destinação/objeto dessas emendas em EXATAMENTE UM ÚNICO PARÁGRAFO contínuo, sem quebras de linha.

REGRAS OBRIGATÓRIAS:
1. ESTRUTURA INICIAL: Comece sempre com minúsculo da seguinte forma "destinado ... ").
2. CONSOLIDAÇÃO DOS OBJETOS: Identifique o objetivo central de cada item dos dados brutos e liste todas as finalidades/especificações apenas uma única vez, ou seja, desconsidere repetições, mesmo que com pequenas variações incluindo sinônimos, unindo-as e separando cada especificação por " // " (duas barras).
3. ELIMINAÇÃO DE REDUNDÂNCIAS: Elimine Razão Social seguida de CNES ou CNPJ, além de trechos de código entre colchetes ou chaves.
4. PRESERVAÇÃO DE DETALHES: Não resuma genericamente como apenas, por exemplo, "construção"; inclua os detalhes específicos citados (ex: melhorias estruturais, manutenção predial, materiais, custeio).
5. PRESERVAÇÃO DE VALORES MONETÁRIOS: Mantenha todos os valores monetários ligado aos objetos identificados nas emendas, sem arredondamentos ou omissões. Coloque os valores próximos aos objetos correspondentes. Caso haja valores descrevendo apenas a totalização dos objetos, descarte-os.
6. FORMATO: Texto corrido, único parágrafo, terminando sem ponto final.
7. CONSOLIDAÇÃO DAS LOCALIDADES: Consolide e adicione apenas se houver informações claras de bairros, cidades e estados, evitando repetições e redundâncias, mantendo todos os detalhes relevantes, concluíndo com "(Localidade beneficiada: ...)".

DADOS BRUTOS:
{ementas}
"""

# Prompt isolado e novo: busca consolidar melhor os dados sem perder
# isolamento, eliminando duplicidades semânticas.
PROMPT_V1 = """
Consolide as seguintes ementas em um único parágrafo contínuo, seguindo as regras estabelecidas:

REGRAS OBRIGATÓRIAS:
1. ESTRUTURA: Comece sempre com minúsculo da seguinte forma "destinado ... ". Termine o parágrafo sem ponto final.
2. Consolide as ementas em um único parágrafo contínuo, eliminando redundâncias, repetições e ruídos de sistema, preservando todos os detalhes relevantes de cada emenda, incluindo valores monetários e localidades beneficiadas. No entanto, mantenha nomes de pessoas, mas remova CNPJs, CNES, Razão Social e quaisquer códigos ou identificadores irrelevantes que não contribuam para a compreensão do conteúdo.
3. Mantenha a ordem cronológica das ementas, respeitando a sequência original de apresentação.
4. Utilize conectivos adequados para garantir a coesão e a fluidez do texto consolidado.
5. Evite iniciar frases com números ou símbolos isolados, reestruturando quando necessário.
6. Certifique-se de que todas as localidades beneficiadas estejam claramente indicadas, sem omissões.
7. Evite duplicidades semânticas, garantindo que informações equivalentes não sejam repetidas de forma redundante. Principalmente as mascasras {{entidade}} e {{bairro}}, assegurando que cada bairro/localidade seja mencionada apenas uma vez, mesmo que apareça em diferentes ementas.
8. Mantenha a consistência na formatação de valores monetários, utilizando sempre o mesmo padrão de moeda e separadores decimais.
9. Garanta que todas as informações relevantes das ementas estejam preservadas, sem omitir detalhes importantes, mesmo que haja pequenas variações de redação entre elas.
10. Ao consolidar as ementas, assegure que a redação final seja clara, coesa e de fácil compreensão, evitando ambiguidades e mantendo a precisão técnica.


EMENTAS:
{ementas}
"""
