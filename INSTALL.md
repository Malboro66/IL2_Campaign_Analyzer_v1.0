# Instruções de Instalação - IL-2 Campaign Analyzer

## Requisitos do Sistema

- **Sistema Operacional**: Windows 10/11, Linux (Ubuntu 18.04+), macOS 10.14+
- **Python**: Versão 3.8 ou superior
- **Espaço em Disco**: Mínimo 100 MB livres
- **Memória RAM**: Mínimo 2 GB

## Instalação Rápida

### Opção 1: Instalação via Código Fonte (Recomendada)

1. **Baixe e extraia o arquivo**
   ```
   IL2_Campaign_Analyzer_v1.0.zip
   ```

2. **Abra o terminal/prompt de comando** na pasta extraída

3. **Crie um ambiente virtual** (recomendado):
   ```bash
   python -m venv venv
   ```

4. **Ative o ambiente virtual**:
   - **Windows**:
     ```cmd
     venv\Scripts\activate
     ```
   - **Linux/macOS**:
     ```bash
     source venv/bin/activate
     ```

5. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

6. **Execute a aplicação**:
   ```bash
   python main_app.py
   ```

### Opção 2: Instalação Manual das Dependências

Se a instalação automática falhar, instale manualmente:

```bash
pip install PyQt5==5.15.11
pip install reportlab==4.4.3
pip install pyinstaller==6.15.0
```

## Configuração Inicial

### 1. Primeira Execução

1. Execute `python main_app.py`
2. Clique em "Selecionar Pasta PWCGFC"
3. Navegue até a pasta onde está instalado o IL-2 Sturmovik
4. Selecione a pasta `PWCGFC` (geralmente em `IL-2 Sturmovik Battle of Stalingrad\PWCGFC`)

### 2. Estrutura de Pastas Esperada

A aplicação espera encontrar a seguinte estrutura:

```
PWCGFC/
├── User/
│   └── Campaigns/
│       └── [Nome_da_Campanha]/
│           ├── Campaign.json
│           ├── CampaignAces.json
│           ├── CampaignLog.json
│           ├── CombatReports/
│           └── MissionData/
└── ...
```

## Solução de Problemas

### Erro: "No module named 'PyQt5'"

**Solução**:
```bash
pip install PyQt5
```

### Erro: "Qt platform plugin could not be initialized" (Linux)

**Solução**:
```bash
sudo apt-get install python3-pyqt5
sudo apt-get install python3-pyqt5-dev
```

### Erro: "Permission denied" (Linux/macOS)

**Solução**:
```bash
chmod +x main_app.py
```

### Aplicação não encontra a pasta PWCGFC

**Verificações**:
1. Certifique-se de que o IL-2 Sturmovik está instalado
2. Verifique se a pasta `PWCGFC` existe no diretório do jogo
3. Confirme que há campanhas na pasta `User/Campaigns/`

### Dados não carregam

**Verificações**:
1. Verifique se os arquivos JSON existem na pasta da campanha
2. Confirme que os arquivos não estão corrompidos
3. Verifique as permissões de leitura dos arquivos

## Criando um Executável (Opcional)

Para criar um executável standalone:

1. **Ative o ambiente virtual**
2. **Execute o PyInstaller**:
   ```bash
   pyinstaller --onefile --windowed --name "IL2_Campaign_Analyzer" main_app.py
   ```
3. **O executável será criado em**: `dist/IL2_Campaign_Analyzer.exe` (Windows) ou `dist/IL2_Campaign_Analyzer` (Linux/macOS)

## Desinstalação

Para remover a aplicação:

1. **Desative o ambiente virtual**:
   ```bash
   deactivate
   ```

2. **Remova a pasta do projeto**

3. **Remova o ambiente virtual** (se criado):
   - Simplesmente delete a pasta `venv`

## Suporte Técnico

### Logs de Erro

Se encontrar problemas, execute a aplicação via terminal para ver mensagens de erro:

```bash
python main_app.py
```

### Informações do Sistema

Para reportar problemas, inclua:
- Sistema operacional e versão
- Versão do Python (`python --version`)
- Mensagem de erro completa
- Passos para reproduzir o problema

### Contato

Para suporte adicional:
- Abra uma issue no repositório do projeto
- Inclua logs de erro e informações do sistema
- Descreva detalhadamente o problema encontrado

## Atualizações

Para atualizar para uma nova versão:

1. **Baixe a nova versão**
2. **Substitua os arquivos** (mantenha `pilot_info.json` se existir)
3. **Atualize as dependências**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

## Notas Importantes

- **Backup**: Faça backup de suas campanhas antes de usar a aplicação
- **Compatibilidade**: Testado com PWCG versões 4.0+
- **Performance**: Para campanhas muito grandes, o carregamento pode demorar alguns segundos
- **Privacidade**: A aplicação não envia dados para servidores externos

