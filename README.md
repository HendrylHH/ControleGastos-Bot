# Bot de Controle Financeiro no Telegram

Este projeto é um **bot do Telegram** para **controle de gastos pessoais**, permitindo que o usuário registre despesas, defina um saldo mensal, gere relatórios e visualize gráficos de gastos.

## Funcionalidades Principais
- **Adicionar gasto**: Registrar um gasto informando valor e categoria.
- **Definir saldo mensal**: Configurar o saldo disponível para o mês atual.
- **Consultar saldo disponível**: Verificar o saldo restante após os gastos.
- **Gerar relatório mensal**: Criar um arquivo CSV e um resumo de gastos do mês.
- **Editar e excluir gastos**: Modificar ou remover registros previamente cadastrados.
- **Gerar gráficos**: Criar gráficos de despesas por categoria.
- **Backup de registros**: Exportar todos os gastos registrados.
- **Listar gastos**: Exibir todos os gastos registrados com seus respectivos IDs.
- **Automação**: 
  - Geração automática de relatório no início do mês.
  - Envio de resumo diário dos gastos do dia.

## Tecnologias Utilizadas
- **Python** (Automação e manipulação de dados)
- **Python Telegram Bot API** (Interação com o Telegram)
- **Pandas** (Manipulação e análise de dados)
- **Matplotlib** (Geração de gráficos)

## Como Configurar e Executar

### Pré-requisitos
1. Ter o **Python 3.8+** instalado.
2. Criar um bot no Telegram via [BotFather](https://core.telegram.org/bots/tutorial).
3. Obter o **token** do bot e substituir no código (`TOKEN_DO_BOT`).
4. Obter seu **User ID** via [@userinfobot](https://t.me/userinfobot) e substituir no código (`USER_ID`).

### Instalação
```sh
# Clone o repositório
git clone https://github.com/HendrylHH/ControleGastos-Bot.git
cd controlegastos-bot

### Comandos Disponíveis
| Comando | Descrição |
|---------|-----------|
| `/g valor categoria` | Adiciona um gasto |
| `/e valor` | Define saldo mensal |
| `/csd` | Consulta saldo disponível |
| `/rm` | Gera relatório mensal |
| `/editar id novo_valor [nova_categoria]` | Edita um registro |
| `/excluir id` | Exclui um registro |
| `/grafico` | Envia gráfico de gastos |
| `/backup` | Gera um backup dos registros |
| `/lista` | Lista todos os gastos registrados |


