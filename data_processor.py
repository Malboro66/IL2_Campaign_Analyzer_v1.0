import os
import json
from datetime import datetime, timedelta
from data_parser import IL2DataParser

class IL2DataProcessor:
    def __init__(self, pwcgfc_path):
        self.parser = IL2DataParser(pwcgfc_path)
        self.pilot_info_file = os.path.join(os.path.dirname(__file__), 'pilot_info.json')

    def process_campaign_data(self, campaign_name):
        """Processa todos os dados de uma campanha"""
        all_data = self.parser.get_all_campaign_data(campaign_name)
        if not all_data:
            return None

        # Filtrar dados do piloto do usuário
        pilot_data = self.filter_pilot_data(all_data)
        
        # Processar dados dos ases
        aces_data = self.process_aces_data(all_data['aces'])
        
        # Processar dados do esquadrão
        squad_data = self.process_squad_data(all_data, pilot_data)
        
        # Processar dados das missões
        missions_data = self.process_missions_data(all_data['combat_reports'], pilot_data)

        return {
            'pilot': pilot_data,
            'aces': aces_data,
            'squad': squad_data,
            'missions': missions_data,
            'raw_data': all_data
        }

    def filter_pilot_data(self, all_data):
        """Filtra dados específicos do piloto do usuário"""
        campaign_data = all_data['campaign']
        
        pilot_data = {
            'name': campaign_data.get('name', 'N/A'),
            'serial_number': campaign_data.get('referencePlayerSerialNumber', 'N/A'),
            'campaign_date': campaign_data.get('date', 'N/A'),
            'squadron': 'N/A',  # Será preenchido com base nos relatórios de combate
            'total_missions': 0,
            'total_flight_time': 0,
            'aircraft_types': set(),
            'last_mission_date': None
        }

        # Extrair informações dos relatórios de combate
        combat_reports = all_data.get('combat_reports', [])
        if combat_reports:
            pilot_data['total_missions'] = len(combat_reports)
            
            # Pegar o esquadrão do primeiro relatório
            if combat_reports[0].get('squadron'):
                pilot_data['squadron'] = combat_reports[0]['squadron']
            
            # Coletar tipos de aeronaves
            for report in combat_reports:
                if report.get('type'):
                    pilot_data['aircraft_types'].add(report['type'])
            
            # Encontrar a data da última missão
            dates = []
            for report in combat_reports:
                if report.get('date'):
                    try:
                        # Assumindo formato YYYYMMDD
                        date_str = report['date']
                        if len(date_str) == 8:
                            date_obj = datetime.strptime(date_str, '%Y%m%d')
                            dates.append(date_obj)
                    except:
                        pass
            
            if dates:
                pilot_data['last_mission_date'] = max(dates)

        pilot_data['aircraft_types'] = list(pilot_data['aircraft_types'])
        
        # Carregar informações complementares salvas
        complement_info = self.load_pilot_complement_info()
        if complement_info:
            pilot_data.update(complement_info)
            
            # Calcular idade se tiver data de nascimento e última missão
            if pilot_data.get('birth_date') and pilot_data.get('last_mission_date'):
                try:
                    birth_date = datetime.strptime(pilot_data['birth_date'], '%d/%m/%Y')
                    age = pilot_data['last_mission_date'].year - birth_date.year
                    if pilot_data['last_mission_date'].month < birth_date.month or \
                       (pilot_data['last_mission_date'].month == birth_date.month and 
                        pilot_data['last_mission_date'].day < birth_date.day):
                        age -= 1
                    pilot_data['age'] = age
                except:
                    pilot_data['age'] = 'N/A'

        return pilot_data

    def process_aces_data(self, aces_raw_data):
        """Processa dados dos ases"""
        aces = []
        
        for ace in aces_raw_data:
            aces.append({
                'name': ace.get('name', 'N/A'),
                'squadron': ace.get('squadron', 'N/A'),
                'victories': ace.get('victories', 0)
            })
        
        # Ordenar por número de vitórias (decrescente)
        aces.sort(key=lambda x: x['victories'], reverse=True)
        
        return aces

    def process_squad_data(self, all_data, pilot_data):
        """Processa dados do esquadrão"""
        pilot_squadron = pilot_data.get('squadron', '')
        
        squad_info = {
            'name': pilot_squadron,
            'members': [],
            'total_missions': 0,
            'total_victories': 0,
            'recent_activities': []
        }

        # Filtrar logs do esquadrão
        logs = all_data.get('logs', [])
        for log in logs:
            if log.get('squadronId') == pilot_squadron or \
               pilot_squadron in log.get('log', ''):
                squad_info['recent_activities'].append({
                    'date': log.get('date', 'N/A'),
                    'activity': log.get('log', 'N/A')
                })

        # Filtrar ases do mesmo esquadrão
        aces = all_data.get('aces', [])
        for ace in aces:
            if ace.get('squadron') == pilot_squadron:
                squad_info['members'].append({
                    'name': ace.get('name', 'N/A'),
                    'victories': ace.get('victories', 0)
                })
                squad_info['total_victories'] += ace.get('victories', 0)

        return squad_info

    def process_missions_data(self, combat_reports, pilot_data):
        """Processa dados das missões"""
        missions = []
        
        for report in combat_reports:
            mission = {
                'date': self.format_date(report.get('date', 'N/A')),
                'time': report.get('time', 'N/A'),
                'aircraft': report.get('type', 'N/A'),
                'duty': report.get('duty', 'N/A'),
                'locality': report.get('locality', 'N/A'),
                'altitude': report.get('altitude', 'N/A'),
                'squadron': report.get('squadron', 'N/A'),
                'report': report.get('haReport', 'N/A'),
                'narrative': report.get('narrative', 'N/A'),
                'flight_pilots': report.get('flightPilots', [])
            }
            
            # Tentar obter dados meteorológicos da missão
            mission_weather = self.parser.parse_mission_file(
                pilot_data.get('name', ''), 
                report.get('date', '')
            )
            if mission_weather:
                mission['weather'] = mission_weather
            
            missions.append(mission)
        
        # Ordenar por data (mais recente primeiro)
        missions.sort(key=lambda x: x['date'], reverse=True)
        
        return missions

    def format_date(self, date_str):
        """Formata data do formato YYYYMMDD para DD/MM/YYYY"""
        if not date_str or date_str == 'N/A' or len(date_str) != 8:
            return date_str
        
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_obj.strftime('%d/%m/%Y')
        except:
            return date_str

    def save_pilot_complement_info(self, birth_date, birth_place, photo_path=None):
        """Salva informações complementares do piloto"""
        complement_info = {
            'birth_date': birth_date,
            'birth_place': birth_place
        }
        
        if photo_path:
            complement_info['photo_path'] = photo_path
        
        try:
            with open(self.pilot_info_file, 'w', encoding='utf-8') as f:
                json.dump(complement_info, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Erro ao salvar informações complementares: {e}")
            return False

    def load_pilot_complement_info(self):
        """Carrega informações complementares do piloto"""
        if not os.path.exists(self.pilot_info_file):
            return None
        
        try:
            with open(self.pilot_info_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar informações complementares: {e}")
            return None

    def calculate_pilot_statistics(self, missions_data):
        """Calcula estatísticas do piloto"""
        stats = {
            'total_missions': len(missions_data),
            'aircraft_types': set(),
            'duty_types': {},
            'localities': set(),
            'average_altitude': 0
        }

        total_altitude = 0
        altitude_count = 0

        for mission in missions_data:
            # Tipos de aeronaves
            if mission['aircraft'] != 'N/A':
                stats['aircraft_types'].add(mission['aircraft'])
            
            # Tipos de missão
            duty = mission['duty']
            if duty != 'N/A':
                stats['duty_types'][duty] = stats['duty_types'].get(duty, 0) + 1
            
            # Localidades
            if mission['locality'] != 'N/A':
                stats['localities'].add(mission['locality'])
            
            # Altitude média
            altitude_str = mission['altitude']
            if altitude_str != 'N/A' and 'meters' in altitude_str:
                try:
                    altitude_value = float(altitude_str.replace('meters', '').strip())
                    total_altitude += altitude_value
                    altitude_count += 1
                except:
                    pass

        if altitude_count > 0:
            stats['average_altitude'] = round(total_altitude / altitude_count, 2)

        stats['aircraft_types'] = list(stats['aircraft_types'])
        stats['localities'] = list(stats['localities'])

        return stats

