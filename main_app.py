# ===================================================================
#  IL2 Campaign Analyzer - main_app.py (improved & fixes)
# ===================================================================
import sys
import os
import json
import re
import random
import threading
import logging
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QTabWidget, QTextEdit,
    QFormLayout, QGroupBox, QComboBox, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QProgressBar, QStatusBar, QSplitter, QScrollArea
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal, QLockFile
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# ===================================================================
#  LOGGING SETUP (robust, single logger, file + stdout)
# ===================================================================
import logging.handlers

def _setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger_name = "IL2CampaignAnalyzer"
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(level)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    try:
        base_dir = Path(__file__).parent if '__file__' in globals() else Path.cwd()
        logs_dir = base_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_filename = logs_dir / f"il2_analyzer_{datetime.now():%Y%m%d}.log"
        fh = logging.handlers.RotatingFileHandler(
            filename=str(log_filename),
            maxBytes=5 * 1024 * 1024,
            backupCount=7,
            encoding='utf-8'
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception:
        logger.warning("Não foi possível inicializar o handler de arquivo de log.")

    logger.propagate = False

    def _excepthook(exc_type, exc_value, exc_traceback):
        if logger:
            logger.exception("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = _excepthook

    try:
        def _threading_excepthook(args):
            logger.exception("Uncaught threading exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
        threading.excepthook = _threading_excepthook  # type: ignore
    except Exception:
        pass

    return logger

logger = _setup_logging(logging.INFO)

# ===================================================================
#  DATA PARSING & PROCESSING
# ===================================================================
class IL2DataParser:
    """Lê e extrai dados brutos dos arquivos da campanha PWCGFC."""
    def __init__(self, pwcgfc_path):
        # aceitar None/'' e Path/str; fallback para cwd para evitar exceções
        if isinstance(pwcgfc_path, Path):
            self.pwcgfc_path = pwcgfc_path
        else:
            try:
                self.pwcgfc_path = Path(pwcgfc_path) if pwcgfc_path else Path.cwd()
            except Exception:
                self.pwcgfc_path = Path.cwd()

        self.campaigns_path = self.pwcgfc_path / 'User' / 'Campaigns'
        self._json_cache: Dict[str, Any] = {}

    def get_json_data(self, file_path: Path) -> Any:
        """Carrega JSON de arquivo, com cache, diferentes encodings e fallback tolerante."""
        try:
            file_path = Path(file_path)
            key = str(file_path.resolve())
        except Exception:
            key = str(file_path)

        if key in self._json_cache:
            return self._json_cache[key]

        if not file_path.exists():
            logger.warning(f"Arquivo não encontrado: {file_path}")
            return None

        # Tentativas em ordem: utf-8, latin-1, leitura com errors='replace' + json.loads
        try:
            with file_path.open('r', encoding='utf-8') as f:
                data = json.load(f)
                self._json_cache[key] = data
                return data
        except json.JSONDecodeError:
            logger.debug(f"JSONDecodeError ao ler {file_path} como utf-8; tentando latin-1.")
            try:
                with file_path.open('r', encoding='latin-1') as f:
                    data = json.load(f)
                    self._json_cache[key] = data
                    return data
            except json.JSONDecodeError:
                logger.debug(f"latin-1 também falhou para {file_path}; tentando leitura tolerante.")
                try:
                    text = file_path.read_text(encoding='utf-8', errors='replace')
                    data = json.loads(text)
                    self._json_cache[key] = data
                    return data
                except Exception as e:
                    logger.error(f"Erro ao decodificar JSON (fallback) {file_path}: {e}")
                    return None
            except Exception as e:
                logger.error(f"Erro ao ler arquivo {file_path} com latin-1: {e}")
                return None
        except IOError as e:
            logger.error(f"Erro ao ler o arquivo JSON {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao carregar JSON {file_path}: {e}")
            return None

    def get_campaigns(self) -> List[str]:
        if not self.campaigns_path.exists():
            logger.warning(f"Pasta de campanhas não encontrada: {self.campaigns_path}")
            return []
        try:
            campaigns = [p.name for p in self.campaigns_path.iterdir() if p.is_dir()]
            return sorted(campaigns)
        except Exception as e:
            logger.error(f"Erro ao listar campanhas em {self.campaigns_path}: {e}")
            return []

    def get_campaign_info(self, campaign_name: str) -> Dict:
        path = self.campaigns_path / campaign_name / 'Campaign.json'
        return self.get_json_data(path) or {}

    def get_campaign_aces(self, campaign_name: str) -> List[Dict]:
        aces_path = self.campaigns_path / campaign_name / 'CampaignAces.json'
        data = self.get_json_data(aces_path)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get('aces', []) if data.get('aces') else []
        return []

    def get_squadron_personnel(self, campaign_name: str, squadron_id: int) -> Dict:
        personnel_path = self.campaigns_path / campaign_name / 'Personnel' / f'{squadron_id}.json'
        return self.get_json_data(personnel_path) or {}

    def get_combat_reports(self, campaign_name: str, player_serial: str) -> List[Dict]:
        reports_path = self.campaigns_path / campaign_name / 'CombatReports' / player_serial
        if not reports_path.exists() or not reports_path.is_dir():
            logger.warning(f"Pasta de relatórios não encontrada para serial {player_serial}: {reports_path}")
            return []

        files = []
        for report_file in reports_path.glob('*.json'):
            try:
                mtime = report_file.stat().st_mtime
            except Exception:
                mtime = 0
            files.append((mtime, report_file))

        files.sort(key=lambda x: x[0], reverse=True)

        reports = []
        for _, report_file in files:
            report_data = self.get_json_data(report_file)
            if isinstance(report_data, dict):
                reports.append(report_data)
            else:
                logger.warning(f"Dados de relatório inválidos encontrados em {report_file}: {type(report_data)}")
        return reports

    def get_mission_data(self, campaign_name: str, report: Dict) -> Dict:
        mission_data_dir = self.campaigns_path / campaign_name / 'MissionData'
        if not mission_data_dir.exists() or not mission_data_dir.is_dir():
            logger.warning(f"Diretório de dados da missão não encontrado: {mission_data_dir}")
            return {}

        pilot_name = (report.get("reportPilotName") or "") or ""
        pilot_name_clean = re.sub(
            r'^(?:Lieutenant|Ltn|Fw|Obltn|Cne|S/Lt|Sergt|Lt|Capt|Major|Maj)\.?\s*',
            '',
            pilot_name,
            flags=re.IGNORECASE
        ).strip()
        pilot_name_clean = re.sub(r'\s+', ' ', pilot_name_clean).strip()

        date_str_yyyymmdd = report.get("date", "") or ""
        if not date_str_yyyymmdd or len(date_str_yyyymmdd) != 8 or not date_str_yyyymmdd.isdigit():
            logger.warning(f"Data da missão ausente ou inválida no relatório: {date_str_yyyymmdd}")
            return {}

        try:
            date_obj = datetime.strptime(date_str_yyyymmdd, '%Y%m%d')
            date_str_dashed = date_obj.strftime('%Y-%m-%d')
        except ValueError:
            logger.error(f"Formato de data inválido no relatório: {date_str_yyyymmdd}")
            return {}

        candidates = []
        try:
            # coletar candidatos mais seletivamente para evitar leitura desnecessária
            candidates += list(mission_data_dir.glob('*MissionData.json'))
            candidates += list(mission_data_dir.glob('*.MissionData.json'))
            candidates += list(mission_data_dir.glob('*.json'))
            # remove duplicatas
            seen = set()
            unique = []
            for p in candidates:
                try:
                    rp = str(p.resolve())
                except Exception:
                    rp = str(p)
                if rp not in seen:
                    seen.add(rp)
                    unique.append(p)
            candidates = unique
        except Exception as e:
            logger.warning(f"Erro ao listar arquivos de MissionData: {e}")
            return {}

        lower_pilot = pilot_name_clean.lower()
        lower_date = date_str_dashed.lower()

        match_candidates = []
        for f in candidates:
            name_lower = f.name.lower()
            if lower_date in name_lower and (not lower_pilot or lower_pilot in name_lower):
                match_candidates.append(f)

        if not match_candidates and lower_pilot:
            for f in candidates:
                if lower_pilot in f.name.lower():
                    match_candidates.append(f)

        if not match_candidates:
            for f in candidates:
                if lower_date in f.name.lower():
                    match_candidates.append(f)

        if not match_candidates:
            date_regex = re.compile(r'\d{4}-\d{2}-\d{2}')
            nearest = []
            for f in candidates:
                m = date_regex.search(f.name)
                if m and m.group(0) == date_str_dashed:
                    nearest.append(f)
            if nearest:
                match_candidates = nearest

        if match_candidates:
            try:
                match_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
            except Exception:
                pass
            for candidate in match_candidates:
                data = self.get_json_data(candidate)
                if isinstance(data, dict):
                    logger.info(f"Arquivo de missão correspondente encontrado: {candidate.name}")
                    return data
                else:
                    logger.debug(f"Arquivo candidato inválido: {candidate} -> {type(data)}")

        logger.warning(f"Nenhum arquivo de dados da missão encontrado para piloto '{pilot_name_clean}' na data '{date_str_dashed}' em {mission_data_dir}")
        return {}

class IL2DataProcessor:
    """Processa os dados brutos, organizando e enriquecendo as informações."""
    def __init__(self, pwcgfc_path):
        self.parser = IL2DataParser(pwcgfc_path)

    def process_campaign(self, campaign_name: str) -> Dict:
        campaign_info = self.parser.get_campaign_info(campaign_name)
        if not campaign_info:
            return {}

        player_serial = str(campaign_info.get('referencePlayerSerialNumber', ''))
        combat_reports = self.parser.get_combat_reports(campaign_name, player_serial)

        missions_data, player_squadron_id = self._process_missions_data(campaign_name, combat_reports, player_serial)

        pilot_data = self._process_pilot_data(campaign_info, combat_reports)

        if player_squadron_id:
            squadron_personnel = self.parser.get_squadron_personnel(campaign_name, player_squadron_id)
            squadron_data = self._process_squadron_data(squadron_personnel)
        else:
            squadron_data = []
            logger.debug("Não foi possível determinar o squadronId do jogador.")

        aces_data = self._process_aces_data(self.parser.get_campaign_aces(campaign_name))

        return {
            'pilot': pilot_data,
            'missions': missions_data,
            'squadron': squadron_data,
            'aces': aces_data
        }

    def _process_missions_data(self, campaign_name, combat_reports, player_serial):
        missions_with_key = []
        player_squadron_id = None

        for report in combat_reports:
            if not isinstance(report, dict):
                logger.debug(f"Relatório inválido encontrado: {report}. Pulando.")
                continue

            raw_date = report.get('date', '') or ''
            try:
                mission_details = self.parser.get_mission_data(campaign_name, report) or {}
            except Exception as e:
                logger.warning(f"Falha ao obter MissionData para relatório: {e}")
                mission_details = {}

            mission_time = report.get("time", "N/A")

            pilots_in_mission = []
            ha_report = report.get('haReport') or ""
            if ha_report:
                pilot_lines = re.findall(r'^(?:Ltn|Lieutenant|Fw|Obltn|Cne|S/Lt|Sergt|Lt|Capt|Maj)\.?\s+.*$', ha_report, re.MULTILINE | re.IGNORECASE)
                for line in pilot_lines:
                    name = re.sub(r'^(?:Ltn|Lieutenant|Fw|Obltn|Cne|S/Lt|Sergt|Lt|Capt|Maj)\.?\s*', '', line, flags=re.IGNORECASE).strip()
                    if name:
                        pilots_in_mission.append(name)
            seen = set()
            pilots_in_mission = [p for p in pilots_in_mission if not (p in seen or seen.add(p))]

            weather_text = "Não disponível"
            description_text = "Descrição da missão não encontrada."
            try:
                if mission_details:
                    description_text = mission_details.get('missionDescription', description_text) or description_text
                    time_match = re.search(r'Time\s+([0-9]{2}:[0-9]{2}:[0-9]{2})', description_text)
                    if time_match:
                        mission_time = time_match.group(1)
                    match = re.search(r'Weather Report\s*\n(.*?)(?:\n\n|$)', description_text, re.DOTALL | re.IGNORECASE)
                    if match:
                        weather_text = match.group(1).strip()
                    if not player_squadron_id:
                        mission_planes = mission_details.get('missionPlanes', {}) or {}
                        for k, v in mission_planes.items():
                            try:
                                if str(k) == str(player_serial):
                                    player_squadron_id = v.get('squadronId') if isinstance(v, dict) else None
                                    break
                            except Exception:
                                continue
            except Exception as e:
                logger.debug(f"Erro ao processar mission_details: {e}")

            mission_entry = {
                'date': self._format_date(raw_date) if raw_date else report.get('date', 'N/A'),
                'time': mission_time,
                'aircraft': report.get('type', 'N/A'),
                'duty': report.get('duty', 'N/A'),
                'locality': report.get('locality', 'N/A'),
                'airfield': (mission_details.get('missionHeader', {}) if isinstance(mission_details.get('missionHeader', {}), dict) else {}).get('airfield', 'N/A'),
                'pilots': pilots_in_mission,
                'weather': weather_text,
                'description': description_text,
            }
            missions_with_key.append((raw_date or "99999999", mission_entry))

        try:
            missions_with_key.sort(key=lambda t: (t[0] == "99999999", t[0]))
        except Exception:
            logger.debug("Falha ao ordenar missões por data; mantendo ordem original.")

        missions = [m for _, m in missions_with_key]
        return missions, player_squadron_id

    def _process_squadron_data(self, squadron_personnel):
        squad_members = []
        if not squadron_personnel:
            logger.debug("Arquivo de pessoal do esquadrão não encontrado ou vazio.")
            return squad_members

        squad_collection = squadron_personnel.get('squadronMemberCollection', {}) or {}
        for pilot_info in squad_collection.values():
            try:
                victories = pilot_info.get('victories', [])
                if isinstance(victories, (list, tuple, dict)):
                    victories_count = len(victories)
                else:
                    victories_count = int(victories) if str(victories).isdigit() else 0
            except Exception:
                victories_count = 0

            try:
                missions_flown = pilot_info.get('missionFlown', 0)
                if not isinstance(missions_flown, int):
                    missions_flown = int(missions_flown) if str(missions_flown).isdigit() else 0
            except Exception:
                missions_flown = 0

            squad_members.append({
                'name': pilot_info.get('name', 'N/A'),
                'rank': pilot_info.get('rank', 'N/A'),
                'victories': victories_count,
                'missions_flown': missions_flown,
                'status': self._get_pilot_status(pilot_info.get('pilotActiveStatus', -1))
            })

        squad_members.sort(key=lambda x: (x['missions_flown'], x['victories']), reverse=True)
        return squad_members

    def _get_pilot_status(self, status_code):
        return {
            0: "Ativo",
            1: "Ativo",
            2: "Morto em Combate (KIA)",
            3: "Gravemente Ferido (WIA)",
            4: "Capturado (POW)",
            5: "Desaparecido em Combate (MIA)"
        }.get(status_code, "Desconhecido")

    def _process_aces_data(self, aces_raw_data: List[Dict]) -> List[Dict]:
        aces = []
        if not aces_raw_data:
            return aces
        for ace in aces_raw_data:
            try:
                victories = ace.get('victories', 0)
                victories = int(victories) if (isinstance(victories, (int, str)) and str(victories).isdigit()) else (victories if isinstance(victories, int) else 0)
            except Exception:
                victories = 0
            aces.append({
                'name': ace.get('name', 'N/A'),
                'victories': victories
            })
        aces.sort(key=lambda x: x['victories'], reverse=True)
        return aces

    def _format_date(self, date_str):
        if not date_str or len(date_str) != 8 or not date_str.isdigit():
            return date_str
        try:
            return datetime.strptime(date_str, '%Y%m%d').strftime('%d/%m/%Y')
        except ValueError:
            return date_str

    def _process_pilot_data(self, campaign_info, combat_reports):
        pilot = {}
        try:
            # Nome vem sempre do Campaign.json
            pilot['name'] = campaign_info.get('referencePlayerName') or campaign_info.get('playerName') \
                            or campaign_info.get('name') or "N/A"

            # Esquadrão vem do Campaign.json se existir, caso contrário, do primeiro CombatReport válido
            squadron_name = campaign_info.get('referencePlayerSquadronName') or campaign_info.get('playerSquadron')
            if not squadron_name and combat_reports:
                for report in combat_reports:
                    if isinstance(report, dict) and report.get("squadron"):
                        squadron_name = report.get("squadron")
                        break

            pilot['squadron'] = squadron_name or "N/A"

            # Total de missões voadas é o número de relatórios válidos
            pilot["total_missions"] = len([r for r in combat_reports if isinstance(r, dict)])

            logger.debug(
                f"Nome do piloto processado: {pilot.get('name')}, Esquadrão processado: {pilot.get('squadron')}"
            )
        except Exception as e:
            logger.debug(f"Erro ao processar dados do piloto: {e}")
            pilot['name'] = pilot.get('name', 'N/A')
            pilot['squadron'] = pilot.get('squadron', 'N/A')
            pilot['total_missions'] = pilot.get('total_missions', 0)
        return pilot

# ===================================================================
#  REPORT GENERATION
# ===================================================================
class IL2ReportGenerator:
    """Gera relatórios em PDF, texto e imagens de mapa (robusto e com cleanup)."""
    def __init__(self):
        self.styles = getSampleStyleSheet()
        if 'Title' in self.styles:
            self.styles['Title'].fontSize = 20
            self.styles['Title'].alignment = TA_CENTER
            self.styles['Title'].spaceAfter = 20
            self.styles['Title'].textColor = colors.darkblue
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles.get('Heading2', self.styles['Normal']),
            fontSize=16, alignment=TA_LEFT, spaceAfter=12, spaceBefore=12,
            textColor=colors.darkslateblue
        ))
        self.map_coordinates = self._load_map_coordinates()

    def _load_map_coordinates(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            coords_path = os.path.join(script_dir, "coordenadas_mapa_final_calibrado.json")
            if not os.path.exists(coords_path):
                # fallback: cwd
                coords_path = os.path.join(os.getcwd(), "coordenadas_mapa_final_calibrado.json")
            with open(coords_path, 'r', encoding='utf-8') as f:
                return json.load(f) or {}
        except FileNotFoundError:
            logger.error("Arquivo 'coordenadas_mapa_final_calibrado.json' não encontrado!")
            return {}
        except Exception as e:
            logger.error(f"Erro ao carregar coordenadas do mapa: {e}")
            return {}

    def gerar_mapa_de_carreira(self, missoes: list, output_path: str, highlight_mission_index: int = -1):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        mapa_base_path = os.path.join(script_dir, "mapa_base.jpg")
        if not os.path.exists(mapa_base_path):
            mapa_base_path = os.path.join(os.getcwd(), "mapa_base.jpg")

        if not os.path.exists(mapa_base_path):
            logger.warning("mapa_base.jpg ausente.")
            return False
        if not self.map_coordinates:
            logger.warning("Coordenadas do mapa vazias.")
            return False

        try:
            img = Image.open(mapa_base_path).convert("RGB")
            draw = ImageDraw.Draw(img)

            try:
                base_font_size = max(12, img.width // 50)
                font = ImageFont.truetype("arial.ttf", base_font_size)
            except Exception:
                font = ImageFont.load_default()

            if not isinstance(missoes, list):
                missoes = list(missoes or [])

            def _to_point(value):
                try:
                    x, y = value
                    return (int(round(float(x))), int(round(float(y))))
                except Exception:
                    return None

            if highlight_mission_index != -1 and 0 <= highlight_mission_index < len(missoes):
                missao = missoes[highlight_mission_index]
                localidade = missao.get('locality')
                if localidade in self.map_coordinates:
                    ponto = _to_point(self.map_coordinates[localidade])
                    if ponto:
                        raio = max(10, img.width // 80)
                        draw.ellipse((ponto[0] - raio, ponto[1] - raio, ponto[0] + raio, ponto[1] + raio), outline="yellow", width=5)
                        draw.ellipse((ponto[0] - raio*2, ponto[1] - raio*2, ponto[0] + raio*2, ponto[1] + raio*2), outline="yellow", width=2)
                        try:
                            draw.text((ponto[0] + raio + 5, ponto[1] - raio // 2), f"{localidade}", font=font, fill="yellow")
                        except Exception:
                            pass
                    else:
                        logger.debug(f"Coordenadas inválidas para '{localidade}': {self.map_coordinates.get(localidade)}")
                else:
                    logger.debug(f"Localidade '{localidade}' não encontrada nas coordenadas.")
            else:
                ponto_anterior = None
                for i, missao in enumerate(missoes):
                    localidade = missao.get('locality')
                    if not localidade:
                        continue
                    coord = self.map_coordinates.get(localidade)
                    ponto_atual = _to_point(coord) if coord else None
                    if not ponto_atual:
                        logger.debug(f"Localidade '{localidade}' não encontrada ou coordenada inválida; pulando.")
                        continue
                    if ponto_anterior:
                        try:
                            draw.line([ponto_anterior, ponto_atual], fill="yellow", width=max(2, img.width // 200))
                        except Exception:
                            pass
                    raio = max(6, img.width // 160)
                    try:
                        draw.ellipse((ponto_atual[0] - raio, ponto_atual[1] - raio, ponto_atual[0] + raio, ponto_atual[1] + raio), fill="#FF0000", outline="black", width=2)
                    except Exception:
                        pass
                    try:
                        draw.text((ponto_atual[0] + raio + 3, ponto_atual[1] - raio - 3), str(i + 1), font=font, fill="white")
                    except Exception:
                        pass
                    ponto_anterior = ponto_atual

            # ensure folder exists
            out_dir = os.path.dirname(output_path) or "."
            try:
                os.makedirs(out_dir, exist_ok=True)
            except Exception:
                pass

            img.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Falha ao gerar imagem do mapa: {e}")
            return False

    def generate_mission_report_pdf(self, mission_data, all_missions, mission_index, output_path):
        import tempfile
        from reportlab.platypus import Image as ReportLabImage
        from reportlab.lib.utils import ImageReader

        mini_map_path = None
        tmp_file = None
        try:
            tmp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            mini_map_path = tmp_file.name
            tmp_file.close()
        except Exception:
            mini_map_path = os.path.join(tempfile.gettempdir(), "mini_mapa_temp.png")

        map_success = False
        try:
            map_success = self.gerar_mapa_de_carreira(
                missoes=all_missions or [],
                output_path=mini_map_path,
                highlight_mission_index=mission_index
            )
        except Exception as e:
            logger.warning(f"Falha ao gerar mini-mapa: {e}")
            map_success = False

        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []
            story.append(Paragraph(f"Relatório de Missão - {mission_data.get('date', 'N/A')}", self.styles.get('Title', self.styles['Normal'])))
            story.append(Spacer(1, 0.2 * inch))
            info_data = [
                ['Data:', mission_data.get('date', 'N/A')],
                ['Hora:', mission_data.get('time', 'N/A')],
                ['Aeronave:', mission_data.get('aircraft', 'N/A')],
                ['Tipo de Missão:', mission_data.get('duty', 'N/A')],
                ['Aeródromo de Partida:', mission_data.get('airfield', 'N/A')]
            ]
            info_table = Table(info_data, colWidths=[1.5 * inch, 4.5 * inch])
            info_table.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            story.append(info_table)
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph("Condições Meteorológicas", self.styles['CustomHeading']))
            story.append(Paragraph((mission_data.get('weather', 'Não disponível.') or '').replace('\n', '<br/>'), self.styles['Normal']))
            story.append(Spacer(1, 0.3 * inch))
            story.append(Paragraph("Pilotos na Missão", self.styles['CustomHeading']))

            pilots = mission_data.get('pilots', []) or []
            if pilots:
                list_style = ParagraphStyle(name='list', parent=self.styles['Normal'], leftIndent=15)
                pilot_list = [Paragraph(f"• {name}", list_style) for name in pilots]
                story.extend(pilot_list)
            else:
                story.append(Paragraph("Lista de pilotos não disponível no relatório.", self.styles['Normal']))

            if map_success and mini_map_path and os.path.exists(mini_map_path):
                story.append(Spacer(1, 0.3 * inch))
                story.append(Paragraph("Localização da Missão", self.styles['CustomHeading']))
                try:
                    img_reader = ImageReader(mini_map_path)
                    img_width, img_height = img_reader.getSize()
                    aspect = img_height / float(img_width) if img_width else 1.0
                    display_width = 6 * inch
                    story.append(ReportLabImage(mini_map_path, width=display_width, height=(display_width * aspect)))
                except Exception as e:
                    logger.warning(f"Falha ao anexar mini-mapa no PDF: {e}")

            doc.build(story)
            return True
        except Exception as e:
            logger.error(f"Erro ao gerar PDF da missão: {e}")
            return False
        finally:
            try:
                if mini_map_path and os.path.exists(mini_map_path):
                    os.remove(mini_map_path)
            except Exception:
                pass

    def _gerar_entrada_diario(self, missao: dict, piloto_nome: str) -> str:
        data_raw = missao.get('date', '') or ''
        data_formatada = data_raw or "Data desconhecida"
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%Y%m%d'):
            try:
                data_obj = datetime.strptime(data_raw, fmt)
                data_formatada = data_obj.strftime('%d de %B de %Y')
                break
            except Exception:
                continue

        narrativa_parts = [f"{data_formatada}\n"]
        frases_clima = [
            f"O dia começou com o tempo {missao.get('weather', 'indefinido').lower()}. Partimos de {missao.get('airfield', 'base desconhecida')} por volta das {missao.get('time', 'hora incerta')}.",
            f"As condições hoje eram de {missao.get('weather', 'tempo incerto')}. Decolamos de {missao.get('airfield', 'nossa base')} às {missao.get('time', 'hora incerta')}."
        ]
        narrativa_parts.append(random.choice(frases_clima))

        narrativa_parts.append(f" Minha tarefa era uma missão de '{missao.get('duty', 'tipo desconhecido')}' no meu {missao.get('aircraft', 'aeronave')}.")
        if missao.get('pilots'):
            piloto_lower = (piloto_nome or "").lower()
            companheiros = []
            for p in missao.get('pilots', [])[:10]:
                try:
                    if piloto_lower and piloto_lower in p.lower():
                        continue
                    sobrenome = p.split()[-1]
                    if sobrenome:
                        companheiros.append(sobrenome)
                except Exception:
                    continue
            if companheiros:
                narrativa_parts.append(f" Voaram comigo hoje os camaradas {', '.join(companheiros[:3])}.")

        narrativa_parts.append(" A patrulha ocorreu sem grandes incidentes e retornamos em segurança.")
        narrativa_parts.append("\n" + ("-" * 80) + "\n")
        return "".join(narrativa_parts)

    def generate_campaign_diary_txt(self, campaign_data: dict) -> str:
        piloto = campaign_data.get('pilot', {}) or {}
        piloto_nome = piloto.get('name', 'N/A')
        missoes_raw = campaign_data.get('missions', []) or []

        def _parse_date_for_sort(m):
            d = m.get('date', '') or ''
            if not d:
                return datetime.max
            for fmt in ('%d/%m/%Y', '%Y%m%d', '%Y-%m-%d'):
                try:
                    return datetime.strptime(d, fmt)
                except Exception:
                    continue
            return datetime.max

        try:
            missoes = sorted(missoes_raw, key=_parse_date_for_sort)
        except Exception:
            missoes = list(missoes_raw)

        diario_lines = []
        diario_lines.append("=" * 80)
        diario_lines.append("                   DIÁRIO DE BORDO DE CAMPANHA")
        diario_lines.append("=" * 80)
        diario_lines.append("")
        diario_lines.append(f"Piloto: {piloto_nome}")
        diario_lines.append(f"Esquadrão: {piloto.get('squadron', 'N/A')}")
        if missoes:
            primeiro = missoes[0].get('date', '')
            ultimo = missoes[-1].get('date', '')
            diario_lines.append(f"Período da Campanha: {primeiro} a {ultimo}")
        diario_lines.append("")
        diario_lines.append("=" * 80)
        diario_lines.append("")

        for missao in missoes:
            diario_lines.append(self._gerar_entrada_diario(missao, piloto_nome))

        return "\n".join(diario_lines)

# ===================================================================
#  APPLICATION CLASSES
# ===================================================================
class DataSyncThread(QThread):
    data_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    progress = pyqtSignal(int)
    started_sync = pyqtSignal()

    def __init__(self, pwcgfc_path, campaign_name, parent=None):
        super().__init__(parent)
        self.pwcgfc_path = pwcgfc_path
        self.campaign_name = campaign_name

    def run(self):
        try:
            self.started_sync.emit()
            self.progress.emit(5)
            processor = IL2DataProcessor(self.pwcgfc_path)
            self.progress.emit(20)
            processed_data = processor.process_campaign(self.campaign_name)
            self.progress.emit(90)
            if processed_data is None:
                logger.error("Processamento retornou None para a campanha %s", self.campaign_name)
                self.error_occurred.emit("Não foi possível carregar os dados da campanha (retorno inválido).")
                self.progress.emit(0)
                return
            self.data_loaded.emit(processed_data)
            self.progress.emit(100)
        except Exception:
            logger.exception("Erro na thread de sincronização")
            self.error_occurred.emit("Erro ao sincronizar dados. Verifique os logs para detalhes.")
            try:
                self.progress.emit(0)
            except Exception:
                pass

class MapViewer(QScrollArea):
    """Widget que exibe uma imagem com suporte a zoom e fit-to-view."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.zoom_factor = 1.0
        self._pixmap = QPixmap()
        self._fit_factor = 1.0
        self._is_fit = True
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.setWidget(self.image_label)
        self.setWidgetResizable(True)
        self._min_zoom = 0.1
        self._max_zoom = 10.0

    def set_pixmap(self, pixmap):
        """Define o pixmap original; aceita QPixmap, caminho (str/Path)."""
        if isinstance(pixmap, QPixmap):
            self._pixmap = pixmap
        else:
            try:
                p = str(pixmap)
                if not os.path.exists(p):
                    self.image_label.setText("Imagem não encontrada.")
                    self._pixmap = QPixmap()
                    return
                self._pixmap = QPixmap(p)
            except Exception:
                self._pixmap = QPixmap()

        if self._pixmap.isNull():
            self.image_label.clear()
            return

        self.fit_to_view()

    def fit_to_view(self):
        if self._pixmap.isNull():
            return

        view_size = self.viewport().size()
        pixmap_size = self._pixmap.size()

        if pixmap_size.width() == 0 or pixmap_size.height() == 0:
            return

        width_ratio = view_size.width() / pixmap_size.width()
        height_ratio = view_size.height() / pixmap_size.height()
        self._fit_factor = max(0.0001, min(width_ratio, height_ratio))
        self.zoom_factor = self._fit_factor
        self._is_fit = True

        self.setWidgetResizable(True)
        scaled = self._pixmap.scaled(view_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled)
        self.image_label.resize(scaled.size())

        h = self.horizontalScrollBar()
        v = self.verticalScrollBar()
        h.setValue((h.maximum() + h.minimum()) // 2)
        v.setValue((v.maximum() + v.minimum()) // 2)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not self._pixmap.isNull() and self._is_fit:
            self.fit_to_view()

    def wheelEvent(self, event):
        if self._pixmap.isNull():
            return

        viewport = self.viewport().size()
        label_w = max(1, self.image_label.width())
        label_h = max(1, self.image_label.height())
        hsb = self.horizontalScrollBar()
        vsb = self.verticalScrollBar()
        center_ratio_x = (hsb.value() + viewport.width() / 2) / label_w
        center_ratio_y = (vsb.value() + viewport.height() / 2) / label_h

        delta = event.angleDelta().y()
        factor = 1.25 if delta > 0 else (1 / 1.25)

        self.zoom_factor = max(self._min_zoom, min(self._max_zoom, self.zoom_factor * factor))
        self._is_fit = False
        self.update_zoom()

        new_label_w = max(1, self.image_label.width())
        new_label_h = max(1, self.image_label.height())
        new_h_value = int(center_ratio_x * new_label_w - viewport.width() / 2)
        new_v_value = int(center_ratio_y * new_label_h - viewport.height() / 2)
        hsb.setValue(max(hsb.minimum(), min(hsb.maximum(), new_h_value)))
        vsb.setValue(max(vsb.minimum(), min(vsb.maximum(), new_v_value)))

    def update_zoom(self):
        if self._pixmap.isNull():
            return

        self.setWidgetResizable(False)
        orig = self._pixmap
        new_w = max(1, int(orig.width() * self.zoom_factor))
        new_h = max(1, int(orig.height() * self.zoom_factor))
        scaled_pixmap = orig.scaled(new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_label.setPixmap(scaled_pixmap)
        self.image_label.resize(scaled_pixmap.size())

    def mouseDoubleClickEvent(self, event):
        if self._pixmap.isNull():
            return
        if self._is_fit:
            self.zoom_factor = max(self._min_zoom, min(self._max_zoom, 1.0))
            self._is_fit = False
            self.update_zoom()
        else:
            self.fit_to_view()

class IL2CampaignAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('IL2CampaignAnalyzer', 'Settings')
        self.pwcgfc_path = ""
        self.current_data = {}
        self.selected_mission_index = -1
        self.report_generator = IL2ReportGenerator()
        self.sync_thread = None
        self.setup_ui()
        self.load_saved_settings()

    def setup_ui(self):
        self.setWindowTitle('IL-2 Campaign Analyzer v0.4')
        self.setGeometry(100, 100, 1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.path_label = QLabel('Nenhum caminho selecionado')
        main_layout.addWidget(self.path_label)

        select_path_button = QPushButton('Selecionar Pasta PWCGFC')
        select_path_button.clicked.connect(self.select_pwcgfc_folder)
        main_layout.addWidget(select_path_button)

        campaign_layout = QHBoxLayout()
        campaign_layout.addWidget(QLabel("Campanha:"))
        self.campaign_combo = QComboBox()
        campaign_layout.addWidget(self.campaign_combo)
        main_layout.addLayout(campaign_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.tabs = QTabWidget()
        self.create_tabs()
        main_layout.addWidget(self.tabs)

        buttons_layout = QHBoxLayout()
        sync_button = QPushButton('Sincronizar Dados')
        sync_button.clicked.connect(self.sync_data)
        buttons_layout.addWidget(sync_button)

        self.diary_button = QPushButton('Gerar Diário de Bordo (.txt)')
        self.diary_button.clicked.connect(self.export_diary)
        self.diary_button.setEnabled(False)
        buttons_layout.addWidget(self.diary_button)

        self.export_pdf_button = QPushButton('Exportar Missão para PDF')
        self.export_pdf_button.clicked.connect(self.export_mission_pdf)
        self.export_pdf_button.setEnabled(False)
        buttons_layout.addWidget(self.export_pdf_button)

        main_layout.addLayout(buttons_layout)
        self.setStatusBar(QStatusBar())

    def create_tabs(self):
        self.tab_pilot_profile = QWidget()
        profile_layout = QFormLayout(self.tab_pilot_profile)
        self.pilot_name_label = QLabel("N/A")
        self.squadron_name_label = QLabel("N/A")
        self.total_missions_label = QLabel("N/A")
        profile_layout.addRow("Nome:", self.pilot_name_label)
        profile_layout.addRow("Esquadrão:", self.squadron_name_label)
        profile_layout.addRow("Missões Voadas:", self.total_missions_label)
        self.tabs.addTab(self.tab_pilot_profile, 'Perfil do Piloto')

        self.tab_squadron = QWidget()
        squadron_layout = QVBoxLayout(self.tab_squadron)
        self.squadron_table = QTableWidget()
        self.squadron_table.setColumnCount(5)
        self.squadron_table.setHorizontalHeaderLabels(["Nome", "Patente", "Abates", "Missões Voadas", "Status"])
        self.squadron_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.squadron_table.setSelectionBehavior(QTableWidget.SelectRows)
        squadron_layout.addWidget(self.squadron_table)
        self.tabs.addTab(self.tab_squadron, 'Esquadrão')

        self.tab_missions = QWidget()
        missions_layout = QVBoxLayout(self.tab_missions)
        splitter = QSplitter(Qt.Vertical)
        self.missions_table = QTableWidget()
        self.missions_table.setColumnCount(4)
        self.missions_table.setHorizontalHeaderLabels(["Data", "Hora", "Aeronave", "Tipo de Missão"])
        self.missions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.missions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.missions_table.setSelectionMode(QTableWidget.SingleSelection)
        self.missions_table.itemSelectionChanged.connect(self.on_mission_selected)
        details_group = QGroupBox("Detalhes da Missão Selecionada")
        details_layout = QVBoxLayout()
        self.mission_details_text = QTextEdit()
        self.mission_details_text.setReadOnly(True)
        details_layout.addWidget(self.mission_details_text)
        details_group.setLayout(details_layout)
        splitter.addWidget(self.missions_table)
        splitter.addWidget(details_group)
        splitter.setSizes([400, 200])
        missions_layout.addWidget(splitter)
        self.tabs.addTab(self.tab_missions, 'Missões')

        self.tab_map = QWidget()
        map_layout = QVBoxLayout(self.tab_map)
        self.map_viewer = MapViewer()
        map_layout.addWidget(self.map_viewer)
        self.tabs.addTab(self.tab_map, "Mapa da Carreira")

        self.tab_aces = QWidget()
        aces_layout = QVBoxLayout(self.tab_aces)
        self.aces_table = QTableWidget()
        self.aces_table.setColumnCount(2)
        self.aces_table.setHorizontalHeaderLabels(["Nome do Ás", "Vitórias"])
        self.aces_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        aces_layout.addWidget(self.aces_table)
        self.tabs.addTab(self.tab_aces, "Ases da Campanha")

    def select_pwcgfc_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, 'Selecionar Pasta PWCGFC')
        if folder_path:
            self.pwcgfc_path = folder_path
            self.path_label.setText(f'Caminho: {folder_path}')
            self.settings.setValue('pwcgfc_path', self.pwcgfc_path)
            self.load_campaigns()

    def load_campaigns(self):
        if not self.pwcgfc_path:
            return
        parser = IL2DataParser(self.pwcgfc_path)
        campaigns = parser.get_campaigns()
        self.campaign_combo.clear()
        self.campaign_combo.addItems(campaigns)

    def sync_data(self):
        current_campaign = self.campaign_combo.currentText()
        if not self.pwcgfc_path or not current_campaign:
            QMessageBox.warning(self, "Aviso", "Selecione a pasta e uma campanha primeiro!")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.sync_thread = DataSyncThread(self.pwcgfc_path, current_campaign)
        self.sync_thread.data_loaded.connect(self.on_data_loaded)
        self.sync_thread.error_occurred.connect(self.on_sync_error)
        self.sync_thread.progress.connect(self.progress_bar.setValue)
        self.sync_thread.started_sync.connect(lambda: self.progress_bar.setVisible(True))
        self.sync_thread.start()

    def on_data_loaded(self, data):
        self.current_data = data
        self.update_ui_with_data()
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Dados carregados com sucesso!", 5000)
        QApplication.processEvents()

        try:
            map_output_path = os.path.join(tempfile.gettempdir(), "Mapa_de_Carreira_Gerado.png")
            success = self.report_generator.gerar_mapa_de_carreira(
                missoes=self.current_data.get('missions', []),
                output_path=map_output_path,
                highlight_mission_index=-1
            )
            if success and os.path.exists(map_output_path):
                self.map_viewer.set_pixmap(map_output_path)
            else:
                self.map_viewer.image_label.setText("Não foi possível gerar o mapa de carreira.")
        except Exception as e:
            logger.exception(f"Erro ao gerar/exibir mapa: {e}")
            self.map_viewer.image_label.setText("Erro ao gerar o mapa.")

    def on_sync_error(self, error_message):
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Erro de Sincronização", error_message)
        self.statusBar().showMessage("Falha ao carregar dados.", 5000)

    def update_ui_with_data(self):
        self.export_pdf_button.setEnabled(False)
        self.diary_button.setEnabled(False)

        self.selected_mission_index = -1
        self.mission_details_text.clear()

        pilot_data = self.current_data.get('pilot', {})
        self.pilot_name_label.setText(pilot_data.get('name', 'N/A'))
        self.squadron_name_label.setText(pilot_data.get("squadron", "N/A"))
        self.total_missions_label.setText(str(pilot_data.get('total_missions', '0')))

        squadron_data = self.current_data.get('squadron', [])
        self.squadron_table.setRowCount(len(squadron_data))
        for row, member in enumerate(squadron_data):
            name_item = QTableWidgetItem(member.get('name'))
            rank_item = QTableWidgetItem(member.get('rank'))
            victories_item = QTableWidgetItem(str(member.get('victories')))
            missions_item = QTableWidgetItem(str(member.get('missions_flown')))
            status_item = QTableWidgetItem(member.get('status'))

            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            rank_item.setFlags(rank_item.flags() & ~Qt.ItemIsEditable)
            victories_item.setFlags(victories_item.flags() & ~Qt.ItemIsEditable)
            missions_item.setFlags(missions_item.flags() & ~Qt.ItemIsEditable)
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)

            self.squadron_table.setItem(row, 0, name_item)
            self.squadron_table.setItem(row, 1, rank_item)
            self.squadron_table.setItem(row, 2, victories_item)
            self.squadron_table.setItem(row, 3, missions_item)
            self.squadron_table.setItem(row, 4, status_item)

        missions_data = self.current_data.get('missions', [])
        self.missions_table.setRowCount(len(missions_data))
        for row, mission in enumerate(missions_data):
            date_item = QTableWidgetItem(mission.get('date', ''))
            time_item = QTableWidgetItem(mission.get('time', ''))
            aircraft_item = QTableWidgetItem(mission.get('aircraft', ''))
            duty_item = QTableWidgetItem(mission.get('duty', ''))

            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            time_item.setFlags(time_item.flags() & ~Qt.ItemIsEditable)
            aircraft_item.setFlags(aircraft_item.flags() & ~Qt.ItemIsEditable)
            duty_item.setFlags(duty_item.flags() & ~Qt.ItemIsEditable)

            self.missions_table.setItem(row, 0, date_item)
            self.missions_table.setItem(row, 1, time_item)
            self.missions_table.setItem(row, 2, aircraft_item)
            self.missions_table.setItem(row, 3, duty_item)

        if self.current_data:
            self.diary_button.setEnabled(True)

        aces_data = self.current_data.get("aces", [])
        self.aces_table.setRowCount(len(aces_data))
        for row, ace in enumerate(aces_data):
            name_item = QTableWidgetItem(ace.get("name", "N/A"))
            victories_item = QTableWidgetItem(str(ace.get("victories", 0)))

            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            victories_item.setFlags(victories_item.flags() & ~Qt.ItemIsEditable)

            self.aces_table.setItem(row, 0, name_item)
            self.aces_table.setItem(row, 1, victories_item)

    def on_mission_selected(self):
        selected_items = self.missions_table.selectedItems()
        if selected_items:
            self.selected_mission_index = selected_items[0].row()
            self.export_pdf_button.setEnabled(True)
            mission_data = self.current_data['missions'][self.selected_mission_index]
            self.mission_details_text.setText(mission_data.get('description', ''))
        else:
            self.selected_mission_index = -1
            self.export_pdf_button.setEnabled(False)
            self.mission_details_text.clear()

    def export_diary(self):
        if not self.current_data:
            QMessageBox.warning(self, "Aviso", "Sincronize os dados de uma campanha primeiro!")
            return

        diary_content = self.report_generator.generate_campaign_diary_txt(self.current_data)

        pilot_name = self.current_data.get('pilot', {}).get('name', 'Piloto').replace(' ', '_')
        default_filename = f"Diario_de_Bordo_{pilot_name}.txt"
        file_path, _ = QFileDialog.getSaveFileName(self, 'Salvar Diário de Bordo', default_filename, 'Text Files (*.txt);;All Files (*)')

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(diary_content)
                QMessageBox.information(self, "Sucesso", f"Diário de bordo salvo em: {file_path}")
            except IOError as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível salvar o arquivo do diário: {e}")

    def export_mission_pdf(self):
        if self.selected_mission_index == -1:
            QMessageBox.warning(self, "Aviso", "Selecione uma missão na tabela para exportar.")
            return

        mission_to_export = self.current_data['missions'][self.selected_mission_index]
        default_filename = f"Missao_{mission_to_export.get('date','').replace('/', '-')}.pdf"
        file_path, _ = QFileDialog.getSaveFileName(self, 'Salvar Relatório da Missão', default_filename, 'PDF (*.pdf)')

        if file_path:
            success = self.report_generator.generate_mission_report_pdf(
                mission_data=mission_to_export,
                all_missions=self.current_data.get('missions', []),
                mission_index=self.selected_mission_index,
                output_path=file_path
            )
            if success:
                QMessageBox.information(self, "Sucesso", f"Relatório da missão salvo em: {file_path}")
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível gerar o PDF da missão.")

    def load_saved_settings(self):
        saved_path = self.settings.value('pwcgfc_path', '')
        if saved_path and os.path.exists(saved_path):
            self.pwcgfc_path = saved_path
            self.path_label.setText(f'Caminho: {saved_path}')
            self.load_campaigns()

    def closeEvent(self, event):
        self.settings.setValue('pwcgfc_path', self.pwcgfc_path)
        event.accept()

# ===================================================================
#  APPLICATION ENTRYPOINT
# ===================================================================
if __name__ == '__main__':
    try:
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("IL2 Campaign Analyzer")
    app.setOrganizationName("IL2CampaignAnalyzer")

    logger.info("Iniciando IL-2 Campaign Analyzer")

    lock = None
    try:
        lockfile_path = str(Path(tempfile.gettempdir()) / "il2_campaign_analyzer.lock")
        lock = QLockFile(lockfile_path)
        lock.setStaleLockTime(0)
        if not lock.tryLock(100):
            try:
                QMessageBox.warning(None, "Instância em execução", "Outra instância do programa já está em execução.")
            except Exception:
                pass
            logger.warning("Outra instância detectada. Saindo.")
            sys.exit(0)
    except Exception:
        lock = None

    try:
        window = IL2CampaignAnalyzer()
        window.show()
    except Exception:
        logger.exception("Falha ao inicializar a janela principal")
        try:
            QMessageBox.critical(None, "Erro", "Falha ao iniciar a interface. Veja os logs para detalhes.")
        except Exception:
            pass
        sys.exit(1)

    try:
        exit_code = app.exec_()
    except Exception:
        logger.exception("Exceção não tratada no loop principal do Qt")
        exit_code = 1
    finally:
        try:
            if lock and lock.isLocked():
                lock.unlock()
        except Exception:
            pass

    logger.info("Encerrando IL-2 Campaign Analyzer")
    sys.exit(exit_code)
