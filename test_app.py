#!/usr/bin/env python3
"""
Script de teste para a aplicação IL-2 Campaign Analyzer
"""

import os
import sys
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_parser import IL2DataParser
from data_processor import IL2DataProcessor
from pdf_generator import IL2PDFGenerator

class TestIL2DataParser(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.parser = IL2DataParser(self.test_dir)

    def test_get_campaigns_empty(self):
        """Testa obtenção de campanhas quando não há pasta"""
        campaigns = self.parser.get_campaigns()
        self.assertEqual(campaigns, [])

    def test_parse_campaign_json_not_found(self):
        """Testa parsing quando arquivo não existe"""
        result = self.parser.parse_campaign_json("test_campaign")
        self.assertIsNone(result)

class TestIL2DataProcessor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.processor = IL2DataProcessor(self.test_dir)

    def test_format_date(self):
        """Testa formatação de datas"""
        # Teste com data válida
        result = self.processor.format_date("20160101")
        self.assertEqual(result, "01/01/2016")
        
        # Teste com data inválida
        result = self.processor.format_date("invalid")
        self.assertEqual(result, "invalid")
        
        # Teste com N/A
        result = self.processor.format_date("N/A")
        self.assertEqual(result, "N/A")

class TestIL2PDFGenerator(unittest.TestCase):
    def setUp(self):
        self.pdf_generator = IL2PDFGenerator()

    def test_pdf_generator_initialization(self):
        """Testa inicialização do gerador de PDF"""
        self.assertIsNotNone(self.pdf_generator.styles)

def create_sample_data():
    """Cria dados de exemplo para teste"""
    return {
        'pilot': {
            'name': 'Test Pilot',
            'serial_number': '123456',
            'squadron': 'Test Squadron',
            'campaign_date': '01/01/2016',
            'total_missions': 5,
            'aircraft_types': ['Albatros D.III', 'Fokker E.III'],
            'age': 25
        },
        'aces': [
            {'name': 'Ace 1', 'squadron': 'Squadron 1', 'victories': 10},
            {'name': 'Ace 2', 'squadron': 'Squadron 2', 'victories': 8}
        ],
        'squad': {
            'name': 'Test Squadron',
            'members': [{'name': 'Member 1', 'victories': 5}],
            'total_victories': 15,
            'recent_activities': [
                {'date': '01/01/2016', 'activity': 'Test activity'}
            ]
        },
        'missions': [
            {
                'date': '01/01/2016',
                'time': '10:00',
                'aircraft': 'Albatros D.III',
                'duty': 'CAP',
                'locality': 'Test Location',
                'altitude': '1000 meters',
                'squadron': 'Test Squadron',
                'report': 'Test mission report',
                'narrative': 'Test narrative'
            }
        ]
    }

def test_pdf_generation():
    """Testa geração de PDF com dados de exemplo"""
    try:
        pdf_generator = IL2PDFGenerator()
        sample_data = create_sample_data()
        
        output_path = os.path.join(tempfile.gettempdir(), 'test_report.pdf')
        result = pdf_generator.generate_pilot_report(sample_data, output_path)
        
        if result and os.path.exists(output_path):
            print("✓ Geração de PDF: SUCESSO")
            os.remove(output_path)
            return True
        else:
            print("✗ Geração de PDF: FALHOU")
            return False
    except Exception as e:
        print(f"✗ Geração de PDF: ERRO - {e}")
        return False

def test_data_processing():
    """Testa processamento de dados"""
    try:
        # Criar estrutura de teste
        test_dir = tempfile.mkdtemp()
        campaigns_dir = os.path.join(test_dir, 'User', 'Campaigns', 'TestCampaign')
        os.makedirs(campaigns_dir, exist_ok=True)
        
        # Criar arquivo Campaign.json de teste
        campaign_data = {
            'name': 'Test Pilot',
            'date': '20160101',
            'referencePlayerSerialNumber': 123456
        }
        
        with open(os.path.join(campaigns_dir, 'Campaign.json'), 'w') as f:
            json.dump(campaign_data, f)
        
        # Testar parser
        parser = IL2DataParser(test_dir)
        result = parser.parse_campaign_json('TestCampaign')
        
        if result and result['name'] == 'Test Pilot':
            print("✓ Parsing de dados: SUCESSO")
            return True
        else:
            print("✗ Parsing de dados: FALHOU")
            return False
            
    except Exception as e:
        print(f"✗ Parsing de dados: ERRO - {e}")
        return False

def run_basic_tests():
    """Executa testes básicos da aplicação"""
    print("=== Executando Testes Básicos ===\n")
    
    tests_passed = 0
    total_tests = 3
    
    # Teste 1: Importação de módulos
    try:
        from data_parser import IL2DataParser
        from data_processor import IL2DataProcessor
        from pdf_generator import IL2PDFGenerator
        print("✓ Importação de módulos: SUCESSO")
        tests_passed += 1
    except Exception as e:
        print(f"✗ Importação de módulos: ERRO - {e}")
    
    # Teste 2: Processamento de dados
    if test_data_processing():
        tests_passed += 1
    
    # Teste 3: Geração de PDF
    if test_pdf_generation():
        tests_passed += 1
    
    print(f"\n=== Resultado dos Testes ===")
    print(f"Testes aprovados: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✓ Todos os testes básicos passaram!")
        return True
    else:
        print("✗ Alguns testes falharam.")
        return False

if __name__ == '__main__':
    # Executar testes básicos
    success = run_basic_tests()
    
    # Executar testes unitários se os básicos passaram
    if success:
        print("\n=== Executando Testes Unitários ===")
        unittest.main(argv=[''], exit=False, verbosity=2)
    
    sys.exit(0 if success else 1)

