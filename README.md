<<<<<<< HEAD
# IL-2 Sturmovik Campaign Analyzer

Uma aplicação Python com interface gráfica para analisar dados de campanhas do IL-2 Sturmovik, exibir informações do piloto e esquadrão, listar ases, detalhar missões e permitir a exportação para PDF.

## Funcionalidades

- **Seleção de Pasta PWCGFC**: Interface para selecionar e salvar o caminho da pasta PWCGFC
- **Análise de Campanhas**: Carregamento e análise de múltiplas campanhas
- **Perfil do Piloto**: Exibição de informações detalhadas do piloto com campos complementares
- **Informações do Esquadrão**: Dados do esquadrão e atividades recentes
- **Lista de Ases**: Ranking dos pilotos com maior número de abates
- **Histórico de Missões**: Detalhamento completo das missões realizadas
- **Exportação PDF**: Geração de relatórios completos em formato PDF

## Estrutura de Arquivos Analisados

A aplicação analisa os seguintes arquivos da pasta PWCGFC:

### Pasta Principal: `PWCGFC/User/Campaigns/[Nome_da_Campanha]/`

1. **Campaign.json**
   - `name`: Nome do piloto
   - `date`: Data atual da campanha
   - `referencePlayerSerialNumber`: Número de referência do piloto

2. **CampaignAces.json**
   - Lista dos pilotos com maior número de abates

3. **CampaignLog.json**
   - `date`: Data das informações
   - `log`: Informação do ocorrido
   - `squadronId`: ID do esquadrão

4. **CombatReports/[referencePlayerSerialNumber]/**
   - Arquivos .json para cada missão com informações detalhadas

5. **MissionData/**
   - Arquivos .json com dados específicos das missões

### Pasta de Missões: `IL-2 Sturmovik Battle of Stalingrad/data/Missions/PWCG/`

- Arquivos .mission com dados meteorológicos e condições de voo

## Instalação

### Pré-requisitos

- Python 3.11 ou superior
- Sistema operacional Windows, Linux ou macOS

### Instalação das Dependências

1. Clone ou baixe o projeto
2. Navegue até a pasta do projeto
3. Crie um ambiente virtual:
   ```bash
   python -m venv venv
   ```
4. Ative o ambiente virtual:
   - Windows: `venv\Scripts\activate`
   - Linux/macOS: `source venv/bin/activate`
5. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

### Executando a Aplicação

```bash
python main_app.py
```

### Passos para Usar

1. **Selecionar Pasta PWCGFC**
   - Clique em "Selecionar Pasta PWCGFC"
   - Navegue até a pasta onde está instalado o PWCGFC
   - Selecione a pasta principal do PWCGFC

2. **Escolher Campanha**
   - No dropdown "Campanha", selecione a campanha que deseja analisar
   - As campanhas disponíveis são carregadas automaticamente

3. **Sincronizar Dados**
   - Clique em "Sincronizar Dados" para carregar e processar os dados da campanha
   - Aguarde o processamento (indicado pela barra de progresso)

4. **Navegar pelas Abas**
   - **Pilot Profile**: Informações do piloto e campos para dados complementares
   - **Squad**: Informações do esquadrão e atividades recentes
   - **Aces**: Lista dos ases ordenada por número de vitórias
   - **Missions**: Histórico detalhado das missões

5. **Adicionar Informações Complementares**
   - Na aba "Pilot Profile", preencha data de nascimento, local de nascimento
   - Anexe uma foto do piloto (opcional)
   - Clique em "Salvar Informações Complementares"

6. **Exportar Relatório**
   - Clique em "Exportar para PDF" para gerar um relatório completo
   - Escolha o local e nome do arquivo PDF

## Estrutura do Projeto

```
il2_campaign_analyzer/
├── main_app.py          # Aplicação principal com interface gráfica
├── data_parser.py       # Módulo para parsing dos arquivos JSON e .mission
├── data_processor.py    # Módulo para processamento e filtragem dos dados
├── pdf_generator.py     # Módulo para geração de relatórios PDF
├── test_app.py         # Testes da aplicação
├── requirements.txt    # Dependências do projeto
├── README.md          # Documentação
└── pilot_info.json    # Arquivo gerado para salvar informações complementares
```

## Testes

Para executar os testes da aplicação:

```bash
python test_app.py
```

## Geração de Executável

Para criar um executável standalone:

```bash
pyinstaller --onefile --windowed main_app.py
```

O executável será gerado na pasta `dist/`.

## Limitações Conhecidas

- A aplicação assume estruturas específicas dos arquivos JSON do PWCGFC
- Arquivos .mission são procurados por nome do piloto e podem não ser encontrados se a nomenclatura for diferente
- A interface gráfica requer um ambiente com suporte a PyQt5

## Solução de Problemas

### Erro "Qt platform plugin"
Se encontrar erros relacionados ao Qt no Linux:
```bash
sudo apt-get install python3-pyqt5
```

### Pasta PWCGFC não encontrada
Certifique-se de que está selecionando a pasta raiz do PWCGFC, que deve conter a subpasta `User/Campaigns/`.

### Dados não carregam
Verifique se:
- A campanha selecionada possui os arquivos necessários
- Os arquivos JSON não estão corrompidos
- As permissões de leitura estão adequadas

## Contribuição

Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Implemente as mudanças
4. Execute os testes
5. Submeta um pull request

## Licença

Este projeto é distribuído sob licença MIT. Veja o arquivo LICENSE para mais detalhes.

## Suporte

Para suporte ou dúvidas, abra uma issue no repositório do projeto.
=======
