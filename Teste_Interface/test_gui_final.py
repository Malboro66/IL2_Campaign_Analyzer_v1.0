#!/usr/bin/env python3
"""
Script de teste para IL-2 Campaign Analyzer v3.0
Testa todas as funcionalidades implementadas
"""

import os
import sys
import json
from pathlib import Path
from dataclasses import asdict

# Adiciona o diretório atual ao path para importar o módulo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Testa importação dos módulos"""
    try:
        from gui_final import (
            PilotInfo, MissionData, AceData, DecorationData,
            IL2CampaignAnalyzer, PathConfigDialog
        )
        print("✓ Importação dos módulos bem-sucedida")
        return True
    except ImportError as e:
        print(f"✗ Erro na importação: {e}")
        return False

def test_data_classes():
    """Testa as classes de dados"""
    try:
        from gui_final import PilotInfo, MissionData, AceData, DecorationData
        
        # Testa PilotInfo com novos campos
        pilot = PilotInfo(
            name="Teste Piloto",
            rank="Capitão",
            rank_type="Capitão",
            hat_type="Boné de Voo",
            uniform_type="Uniforme de Voo",
            personal_weapon="Colt .45"
        )
        print(f"✓ PilotInfo criado: {pilot.name}, {pilot.rank}")
        print(f"  - Arma pessoal: {pilot.personal_weapon}")
        print(f"  - Chapéu: {pilot.hat_type}")
        print(f"  - Uniforme: {pilot.uniform_type}")
        
        # Testa DecorationData
        decoration = DecorationData(
            name="Medalha de Teste",
            description="Medalha de teste para validação",
            date_awarded="2024-01-01"
        )
        print(f"✓ DecorationData criado: {decoration.name}")
        
        # Testa MissionData
        mission = MissionData(
            date="2024-01-01",
            time="14:30",
            aircraft="P-51",
            mission_type="Patrulha",
            location="França",
            altitude="5000m"
        )
        print(f"✓ MissionData criado: {mission.aircraft}")
        
        # Testa AceData
        ace = AceData(
            name="Ace Teste",
            squadron="352nd FG",
            victories=15
        )
        print(f"✓ AceData criado: {ace.name}")
        
        return True
    except Exception as e:
        print(f"✗ Erro ao testar classes de dados: {e}")
        return False

def create_test_data():
    """Cria dados de teste"""
    try:
        test_dir = Path("/home/ubuntu/test_campaign")
        test_dir.mkdir(exist_ok=True)
        
        # Dados do piloto
        pilot_data = {
            "name": "John Doe",
            "serial": "12345",
            "squadron": "352nd Fighter Group",
            "rank": "Captain",
            "birth_date": "1920-05-15",
            "birth_place": "New York, USA",
            "age": 24,
            "rank_type": "Capitão",
            "hat_type": "Boné de Voo",
            "uniform_type": "Uniforme de Voo",
            "personal_weapon": "Colt .45",
            "missions_flown": 25,
            "victories": 8,
            "losses": 2
        }
        
        with open(test_dir / "pilot_extra.json", "w", encoding="utf-8") as f:
            json.dump(pilot_data, f, indent=2, ensure_ascii=False)
        
        # Dados de condecorações
        decorations_data = [
            {
                "name": "Distinguished Flying Cross",
                "description": "Por bravura excepcional em combate aéreo",
                "date_awarded": "1944-06-15"
            },
            {
                "name": "Air Medal",
                "description": "Por mérito em operações de voo",
                "date_awarded": "1944-08-20"
            }
        ]
        
        with open(test_dir / "decorations.json", "w", encoding="utf-8") as f:
            json.dump(decorations_data, f, indent=2, ensure_ascii=False)
        
        # Dados de missões
        missions_data = [
            {
                "date": "1944-06-06",
                "time": "06:30",
                "aircraft": "P-51D Mustang",
                "mission_type": "Escort",
                "location": "Normandy",
                "altitude": "25000ft",
                "duration": "3h 15m",
                "result": "Success"
            },
            {
                "date": "1944-06-10",
                "time": "14:00",
                "aircraft": "P-51D Mustang",
                "mission_type": "Fighter Sweep",
                "location": "France",
                "altitude": "20000ft",
                "duration": "2h 45m",
                "result": "Success"
            }
        ]
        
        with open(test_dir / "missions.json", "w", encoding="utf-8") as f:
            json.dump(missions_data, f, indent=2, ensure_ascii=False)
        
        # Dados de ases
        aces_data = [
            {
                "name": "Chuck Yeager",
                "squadron": "357th FG",
                "victories": 11,
                "status": "Active"
            },
            {
                "name": "George Preddy",
                "squadron": "352nd FG",
                "victories": 26,
                "status": "KIA"
            }
        ]
        
        with open(test_dir / "aces.json", "w", encoding="utf-8") as f:
            json.dump(aces_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Dados de teste criados em: {test_dir}")
        return True
        
    except Exception as e:
        print(f"✗ Erro ao criar dados de teste: {e}")
        return False

def check_assets():
    """Verifica se os assets existem"""
    try:
        assets_dir = Path("/home/ubuntu/assets")
        
        # Verifica chapéus
        hats_dir = assets_dir / "hats"
        hat_files = list(hats_dir.glob("*.png")) if hats_dir.exists() else []
        print(f"✓ {len(hat_files)} imagens de chapéu encontradas")
        
        # Verifica uniformes
        uniforms_dir = assets_dir / "uniforms"
        uniform_files = list(uniforms_dir.glob("*.png")) if uniforms_dir.exists() else []
        print(f"✓ {len(uniform_files)} imagens de uniforme encontradas")
        
        # Verifica armas
        weapons_dir = assets_dir / "weapons"
        weapon_files = list(weapons_dir.glob("*.png")) if weapons_dir.exists() else []
        print(f"✓ {len(weapon_files)} imagens de arma encontradas")
        
        # Verifica patentes
        ranks_dir = assets_dir / "ranks"
        rank_files = list(ranks_dir.glob("*.png")) if ranks_dir.exists() else []
        print(f"✓ {len(rank_files)} imagens de patente encontradas")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao verificar assets: {e}")
        return False

def test_application_init():
    """Testa inicialização da aplicação"""
    try:
        from PyQt5.QtWidgets import QApplication
        from gui_final import IL2CampaignAnalyzer
        
        # Cria aplicação Qt (necessário para widgets)
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Testa criação da janela principal
        analyzer = IL2CampaignAnalyzer()
        
        # Verifica se as opções de armas foram carregadas
        weapon_options = analyzer.weapon_options
        print(f"✓ {len(weapon_options)} opções de arma carregadas:")
        for weapon in weapon_options.keys():
            print(f"  - {weapon}")
        
        # Verifica se as opções de patente foram carregadas
        rank_options = analyzer.rank_options
        print(f"✓ {len(rank_options)} opções de patente carregadas:")
        for rank in rank_options.keys():
            print(f"  - {rank}")
        
        # Testa dialog de configuração
        config_dialog = analyzer.PathConfigDialog(None, "/test/path")
        print("✓ PathConfigDialog criado com sucesso")
        
        return True
        
    except Exception as e:
        print(f"✗ Erro ao testar inicialização da aplicação: {e}")
        return False

def main():
    """Função principal de teste"""
    print("=== TESTE DA APLICAÇÃO IL-2 CAMPAIGN ANALYZER v3.0 ===")
    
    tests = [
        ("Importação dos módulos", test_imports),
        ("Classes de dados", test_data_classes),
        ("Criação de dados de teste", create_test_data),
        ("Verificação de assets", check_assets),
        ("Inicialização da aplicação", test_application_init)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n=== {test_name} ===")
        try:
            if test_func():
                passed += 1
            else:
                print(f"✗ Teste '{test_name}' falhou")
        except Exception as e:
            print(f"✗ Erro no teste '{test_name}': {e}")
    
    print(f"\n=== RESULTADO FINAL ===")
    print(f"Testes aprovados: {passed}/{total}")
    
    if passed == total:
        print("✓ Todos os testes passaram! A aplicação está pronta.")
        return 0
    else:
        print("✗ Alguns testes falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

