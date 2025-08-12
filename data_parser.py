import os
import json
import re
from datetime import datetime

class IL2DataParser:
    def __init__(self, pwcgfc_path):
        self.pwcgfc_path = pwcgfc_path
        self.campaigns_path = os.path.join(pwcgfc_path, 'User', 'Campaigns')
        self.missions_path = os.path.join(pwcgfc_path, '..', 'data', 'Missions', 'PWCG')

    def get_campaigns(self):
        """Retorna lista de campanhas disponíveis"""
        if not os.path.exists(self.campaigns_path):
            return []
        
        campaigns = []
        for item in os.listdir(self.campaigns_path):
            item_path = os.path.join(self.campaigns_path, item)
            if os.path.isdir(item_path):
                campaigns.append(item)
        return campaigns

    def parse_campaign_json(self, campaign_name):
        """Parse do arquivo Campaign.json"""
        campaign_path = os.path.join(self.campaigns_path, campaign_name, 'Campaign.json')
        
        if not os.path.exists(campaign_path):
            return None
            
        try:
            with open(campaign_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            return {
                'name': data.get('name', 'N/A'),
                'date': data.get('date', 'N/A'),
                'referencePlayerSerialNumber': data.get('referencePlayerSerialNumber', 'N/A')
            }
        except Exception as e:
            print(f"Erro ao ler Campaign.json: {e}")
            return None

    def parse_campaign_aces_json(self, campaign_name):
        """Parse do arquivo CampaignAces.json"""
        aces_path = os.path.join(self.campaigns_path, campaign_name, 'CampaignAces.json')
        
        if not os.path.exists(aces_path):
            return []
            
        try:
            with open(aces_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            aces = []
            # Assumindo que o arquivo contém uma lista de ases
            if isinstance(data, list):
                for ace in data:
                    aces.append({
                        'name': ace.get('name', 'N/A'),
                        'squadron': ace.get('squadron', 'N/A'),
                        'victories': ace.get('victories', 0)
                    })
            elif isinstance(data, dict):
                # Se for um dicionário, pode ter uma estrutura diferente
                for key, value in data.items():
                    if isinstance(value, dict):
                        aces.append({
                            'name': value.get('name', key),
                            'squadron': value.get('squadron', 'N/A'),
                            'victories': value.get('victories', 0)
                        })
            
            return aces
        except Exception as e:
            print(f"Erro ao ler CampaignAces.json: {e}")
            return []

    def parse_campaign_log_json(self, campaign_name):
        """Parse do arquivo CampaignLog.json"""
        log_path = os.path.join(self.campaigns_path, campaign_name, 'CampaignLog.json')
        
        if not os.path.exists(log_path):
            return []
            
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logs = []
            if isinstance(data, list):
                for log_entry in data:
                    logs.append({
                        'date': log_entry.get('date', 'N/A'),
                        'log': log_entry.get('log', 'N/A'),
                        'squadronId': log_entry.get('squadronId', 'N/A')
                    })
            
            return logs
        except Exception as e:
            print(f"Erro ao ler CampaignLog.json: {e}")
            return []

    def parse_combat_reports(self, campaign_name, player_serial_number):
        """Parse dos arquivos de relatórios de combate"""
        combat_reports_path = os.path.join(self.campaigns_path, campaign_name, 'CombatReports', str(player_serial_number))
        
        if not os.path.exists(combat_reports_path):
            return []
        
        reports = []
        try:
            for filename in os.listdir(combat_reports_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(combat_reports_path, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    reports.append({
                        'flightPilots': data.get('flightPilots', []),
                        'pilotSerialNumber': data.get('pilotSerialNumber', 'N/A'),
                        'reportPilotName': data.get('reportPilotName', 'N/A'),
                        'squadron': data.get('squadron', 'N/A'),
                        'date': data.get('date', 'N/A'),
                        'time': data.get('time', 'N/A'),
                        'type': data.get('type', 'N/A'),
                        'locality': data.get('locality', 'N/A'),
                        'duty': data.get('duty', 'N/A'),
                        'haReport': data.get('haReport', 'N/A'),
                        'narrative': data.get('narrative', 'N/A'),
                        'altitude': data.get('altitude', 'N/A')
                    })
        except Exception as e:
            print(f"Erro ao ler relatórios de combate: {e}")
        
        return reports

    def parse_mission_file(self, pilot_name, mission_date):
        """Parse do arquivo .mission correspondente"""
        if not os.path.exists(self.missions_path):
            return None
        
        # Procurar pelo arquivo .mission correspondente
        mission_filename = f"{pilot_name}_{mission_date}.mission"
        mission_file_path = os.path.join(self.missions_path, mission_filename)
        
        if not os.path.exists(mission_file_path):
            # Tentar encontrar arquivos similares
            for filename in os.listdir(self.missions_path):
                if filename.endswith('.mission') and pilot_name.lower() in filename.lower():
                    mission_file_path = os.path.join(self.missions_path, filename)
                    break
            else:
                return None
        
        try:
            with open(mission_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse das informações específicas do arquivo .mission
            mission_data = {}
            
            # Extrair informações usando regex
            patterns = {
                'Time': r'Time\s*=\s*([^;]+)',
                'Date': r'Date\s*=\s*([^;]+)',
                'CloudLevel': r'CloudLevel\s*=\s*([^;]+)',
                'CloudHeight': r'CloudHeight\s*=\s*([^;]+)',
                'Temperature': r'Temperature\s*=\s*([^;]+)',
                'Pressure': r'Pressure\s*=\s*([^;]+)',
                'Haze': r'Haze\s*=\s*([^;]+)',
                'WindLayers': r'WindLayers\s*=\s*([^;]+)',
                'LayerFog': r'LayerFog\s*=\s*([^;]+)'
            }
            
            for key, pattern in patterns.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    mission_data[key] = match.group(1).strip()
                else:
                    mission_data[key] = 'N/A'
            
            return mission_data
        except Exception as e:
            print(f"Erro ao ler arquivo .mission: {e}")
            return None

    def parse_mission_data_json(self, campaign_name, pilot_name, mission_date):
        """Parse do arquivo JSON de dados da missão"""
        mission_data_path = os.path.join(self.campaigns_path, campaign_name, 'MissionData')
        
        if not os.path.exists(mission_data_path):
            return None
        
        # Procurar pelo arquivo JSON correspondente
        mission_filename = f"{pilot_name}_{mission_date}.json"
        mission_file_path = os.path.join(mission_data_path, mission_filename)
        
        if not os.path.exists(mission_file_path):
            # Tentar encontrar arquivos similares
            for filename in os.listdir(mission_data_path):
                if filename.endswith('.json') and pilot_name.lower() in filename.lower():
                    mission_file_path = os.path.join(mission_data_path, filename)
                    break
            else:
                return None
        
        try:
            with open(mission_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Erro ao ler dados da missão: {e}")
            return None

    def get_all_campaign_data(self, campaign_name):
        """Coleta todos os dados de uma campanha"""
        campaign_data = self.parse_campaign_json(campaign_name)
        if not campaign_data:
            return None
        
        aces_data = self.parse_campaign_aces_json(campaign_name)
        log_data = self.parse_campaign_log_json(campaign_name)
        
        player_serial = campaign_data.get('referencePlayerSerialNumber')
        combat_reports = self.parse_combat_reports(campaign_name, player_serial)
        
        return {
            'campaign': campaign_data,
            'aces': aces_data,
            'logs': log_data,
            'combat_reports': combat_reports
        }

