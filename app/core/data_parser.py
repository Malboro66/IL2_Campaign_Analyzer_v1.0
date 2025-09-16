# app/core/data_parser.py
import os
import json
import xml.etree.ElementTree as ET


class IL2DataParser:
    """
    Responsável por localizar e extrair informações brutas das campanhas
    armazenadas na pasta PWCGFC.
    """

    def __init__(self, pwcgfc_path: str):
        self.pwcgfc_path = pwcgfc_path

    # ----------------------------
    # Localiza campanhas disponíveis
    # ----------------------------
    def get_campaigns(self):
        """
        Retorna uma lista de campanhas encontradas no diretório PWCGFC.
        Cada campanha geralmente é uma subpasta.
        """
        if not self.pwcgfc_path or not os.path.isdir(self.pwcgfc_path):
            return []

        try:
            campaigns = [
                name for name in os.listdir(self.pwcgfc_path)
                if os.path.isdir(os.path.join(self.pwcgfc_path, name))
            ]
            return campaigns
        except Exception:
            return []

    # ----------------------------
    # Lê um arquivo JSON de campanha
    # ----------------------------
    def parse_campaign_json(self, campaign_path: str):
        """
        Lê e retorna dados de campanha a partir de um JSON.
        """
        file_path = os.path.join(self.pwcgfc_path, campaign_path, "campaign.json")
        if not os.path.exists(file_path):
            return {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERRO] Falha ao ler {file_path}: {e}")
            return {}

    # ----------------------------
    # Lê um arquivo XML de campanha
    # ----------------------------
    def parse_campaign_xml(self, campaign_path: str):
        """
        Lê e retorna dados de campanha a partir de um XML.
        """
        file_path = os.path.join(self.pwcgfc_path, campaign_path, "campaign.xml")
        if not os.path.exists(file_path):
            return {}

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return self._xml_to_dict(root)
        except Exception as e:
            print(f"[ERRO] Falha ao ler {file_path}: {e}")
            return {}

    # ----------------------------
    # Converte XML em dicionário
    # ----------------------------
    def _xml_to_dict(self, element):
        """
        Converte recursivamente um elemento XML em dicionário.
        """
        data = {}
        # Atributos
        if element.attrib:
            data.update(element.attrib)
        # Filhos
        for child in element:
            data[child.tag] = self._xml_to_dict(child)
        # Texto
        if element.text and element.text.strip():
            data["text"] = element.text.strip()
        return data
