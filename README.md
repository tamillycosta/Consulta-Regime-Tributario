# 🏢 Consulta-Regime-Tributario

Uma aplicação web desenvolvida para automatizar a consulta de informações cadastrais de empresas a partir de uma planilha.

A ferramenta foi criada para facilitar o trabalho de escritórios que precisam consultar diversos CNPJs, substituindo consultas individuais por um processo automatizado e organizado.

## O que a aplicação faz?

-  Consulta em lote de várias empresas a partir de uma única planilha
- Identificação automática das colunas de CNPJ e nome da empresa
-  Tratamento e normalização dos CNPJs, incluindo correção de zeros à esquerda
-  Consulta através da BrasilAPI, com fallback automático para a MinhaReceita
- Cache local dos resultados por 30 dias
- Geração automática de um relatório Excel

## Classificação no relatório

O arquivo gerado utiliza cores para facilitar a visualização dos resultados:

| Cor | Situação |
| --- | --- |
| 🟢 | Optante pelo Simples Nacional |
| 🔵 | Optante pelo MEI |
| 🟠 | Excluída do Simples Nacional |
| 🔴 | Inativa ou Baixada |
| ⚪ | Lucro Presumido, Lucro Real ou Não Optante |

## 📄 Como usar

1. Acesse a aplicação pelo link.
2. Envie a planilha contendo os dados das empresas.
3. Aguarde o processamento das consultas.
4. Baixe o relatório Excel gerado.

A planilha não precisa seguir um modelo rígido. A aplicação identifica automaticamente as colunas referentes ao CNPJ e ao nome da empresa.

## Projeto
link :

