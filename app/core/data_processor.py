from __future__ import annotations

from typing import Dict, Any, List, Optional, Iterable
from pathlib import Path

# Import relativo para modo pacote
from .data_parser import IL2DataParser


def _safe_int(v: Any) -> int:
    try:
        return int(v)
    except Exception:
        try:
            s = str(v).strip()
            return int(s) if s.isdigit() else 0
        except Exception:
            return 0


class IL2DataProcessor:
    """
    Processa dados do PWCG/IL-2 e entrega um schema consumido pela UI.
    Prioridades de origem para membros do esquadrão:
      1) Personnel/<squadronId>.json (catálogo)
      2) missionPlanes da missão correspondente
      3) fallback pelos nomes do debrief
    """

    def __init__(self, pwcg_root: str) -> None:
        self.parser = IL2DataParser(pwcg_root)
        self.pwcg_root = Path(pwcg_root)

    # API
    def get_campaigns(self) -> List[str]:
        return self.parser.get_campaigns()

    def process_campaign(self, campaign_name: str) -> Dict[str, Any]:
        raw = self.parser.parse_campaign_json(campaign_name)
        if not raw:
            return {}

        campaign = raw.get("campaign", {}) or {}
        pilot_serial = campaign.get("referencePlayerSerialNumber")
        pilot_name = campaign.get("name") or campaign.get("pilotName") or "Desconhecido"
        product = campaign.get("product")

        missions = self._build_missions(raw, pilot_serial)

        # Descobrir squadronId: Campaign.json -> MissionData header -> missionPlanes do jogador
        squadron_id = campaign.get("squadronId") or campaign.get("referencePlayerSquadronId")
        if not squadron_id:
            squadron_id = self._extract_squadron_id_from_raw(raw)
        if not squadron_id and pilot_serial is not None:
            squadron_id = self._extract_squadron_id_from_planes(raw, pilot_serial)

        # Derivações básicas
        squadron_name = self._first_non_empty([m.get("squadron") for m in missions]) or "N/A"
        aircraft_type = self._first_non_empty([m.get("aircraft") for m in missions]) or "N/A"

        pilot = {
            "name": pilot_name,
            "serial": pilot_serial,
            "rank": "NA",
            "squadron": squadron_name,
            "aircraft": aircraft_type,
            "kills": 0,
            "total_missions": len(missions),
            "product": product or "IL-2",
        }

        squadron = {
            "name": squadron_name,
            "aircraft": aircraft_type,
            "total_missions": len(missions),
            "total_kills": 0,
            "id": squadron_id,
        }

        aces = self._build_aces(raw)
        logs = self._build_logs(raw)

        # Enriquecer missões com combat reports
        self._enrich_missions_with_reports(missions, raw)

        # Construir membros
        squadron_members = self._build_squadron_members(
            raw=raw,
            campaign_name=campaign_name,
            squadron_id=squadron_id,
            missions=missions,
            pilot_name=pilot_name,
            pilot_serial=pilot_serial,
            pilot_total_missions=pilot["total_missions"],
        )

        return {
            "pilot": pilot,
            "missions": missions,
            "squadron": squadron,
            "aces": aces,
            "logs": logs,
            "squadron_members": squadron_members,
            "raw": raw,
        }

    # Builders
    def _build_missions(self, raw: Dict[str, Any], player_serial: Optional[int]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for m in raw.get("missions", []) or []:
            header = m.get("missionHeader", {}) or {}
            description = m.get("missionDescription") or ""
            date = header.get("date") or m.get("date") or ""
            time = header.get("time") or m.get("time") or ""
            squadron = header.get("squadron") or ""
            aircraft = header.get("aircraftType") or header.get("aircraft") or ""
            duty = header.get("duty") or m.get("missionType") or ""
            airfield = header.get("airfield") or ""
            altitude = header.get("altitude")

            mission_planes = m.get("missionPlanes") or {}
            squadmates = []
            if isinstance(mission_planes, dict):
                for _, pdata in mission_planes.items():
                    pdata = pdata or {}
                    name = pdata.get("pilotName")
                    serial = pdata.get("pilotSerialNumber")
                    if name and (player_serial is None or serial != player_serial):
                        squadmates.append(name)

            out.append({
                "date": date,
                "time": time,
                "type": duty,
                "aircraft": aircraft,
                "squadron": squadron,
                "airfield": airfield,
                "altitude_m": altitude if isinstance(altitude, int) else None,
                "description": description,
                "squadmates": sorted(set(squadmates)),
                "report": {"narrative": "", "haReport": ""},
            })
        return out

    def _build_aces(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        aces_root = raw.get("aces") or {}
        aces_map = aces_root.get("acesInCampaign") or aces_root.get("aces") or {}
        out: List[Dict[str, Any]] = []
        iterable: Iterable = []
        if isinstance(aces_map, dict):
            iterable = aces_map.values()
        elif isinstance(aces_map, list):
            iterable = aces_map
        for ace in iterable:
            victories = ace.get("victories") or []
            out.append({
                "name": ace.get("name", "N/A"),
                "rank": ace.get("rank", "N/A"),
                "country": ace.get("country", "N/A"),
                "missionFlown": ace.get("missionFlown", 0),
                "victories": len(victories) if isinstance(victories, list) else 0,
            })
        return out

    def _build_logs(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        by_date = (raw.get("log") or {}).get("campaignLogsByDate") or {}
        out: List[Dict[str, Any]] = []
        for dkey in sorted(by_date.keys()):
            entry = by_date.get(dkey) or {}
            if "logs" in entry and isinstance(entry["logs"], list):
                for l in entry["logs"]:
                    out.append({
                        "date": entry.get("date") or dkey,
                        "text": l.get("log", ""),
                        "squadronId": l.get("squadronId"),
                    })
        return out

    # Squadron members (Personnel + missionPlanes + fallback)
    def _build_squadron_members(
        self,
        raw: Dict[str, Any],
        campaign_name: str,
        squadron_id: Optional[int],
        missions: List[Dict[str, Any]],
        pilot_name: str,
        pilot_serial: Optional[int],
        pilot_total_missions: int,
    ) -> List[Dict[str, Any]]:
        members: List[Dict[str, Any]] = []

        # 1) Catálogo
        catalog = self._load_squadron_catalog(campaign_name, squadron_id) if squadron_id else {}
        if catalog:
            for p in self._normalize_personnel_catalog(catalog):
                name = p.get("name") or p.get("pilotName") or "N/A"
                rank = p.get("rank") or p.get("pilotRank") or p.get("pilotRankText") or "N/A"
                missions_flown = (
                    p.get("missions") or p.get("missionsFlown") or p.get("missionFlown") or p.get("missionCount") or
                    p.get("sorties") or p.get("numMissions") or 0
                )
                victories_raw = p.get("victories")
                if isinstance(victories_raw, (list, tuple, dict)):
                    victories = len(victories_raw)
                else:
                    victories = _safe_int(victories_raw or p.get("kills") or p.get("victoryCount") or 0)
                status_code = p.get("pilotActiveStatus")
                status_text = p.get("status") or p.get("pilotActiveStatusText")
                status = status_text if isinstance(status_text, str) and status_text.strip() else ("Ativo" if status_code is None else self._get_pilot_status(status_code))
                members.append({
                    "name": name,
                    "rank": rank,
                    "victories": victories,
                    "missions_flown": _safe_int(missions_flown),
                    "status": status,
                })

        # 2) missionPlanes (se não houve catálogo)
        if not members:
            raw_missions = raw.get("missions", []) or []
            by_date: Dict[str, List[Dict[str, Any]]] = {}
            for rm in raw_missions:
                hdr = (rm.get("missionHeader") or {})
                rdate = hdr.get("date") or rm.get("date") or ""
                by_date.setdefault(rdate, []).append(rm)

            if missions:
                last = missions[-1]
                last_date = last.get("date", "")
                raw_candidates = by_date.get(last_date, [])
                chosen_raw = raw_candidates[0] if raw_candidates else None

                mission_planes = (chosen_raw or {}).get("missionPlanes") or {}
                if isinstance(mission_planes, dict):
                    for _, p in mission_planes.items():
                        p = p or {}
                        name = p.get("pilotName") or "N/A"
                        serial = p.get("pilotSerialNumber")
                        rank = p.get("pilotRank") or "N/A"
                        missions_flown = p.get("missionsFlown") or p.get("missionFlown") or p.get("missions") or 0
                        victories = _safe_int(p.get("victories") or 0)
                        status = "Jogador" if (pilot_serial is not None and serial == pilot_serial) else "Ativo"
                        members.append({
                            "name": name,
                            "rank": rank,
                            "victories": victories,
                            "missions_flown": _safe_int(missions_flown),
                            "status": status,
                        })

        # 3) Fallback final
        if not members and missions:
            last = missions[-1]
            for name in last.get("squadmates", []) or []:
                members.append({
                    "name": name,
                    "rank": "N/A",
                    "victories": 0,
                    "missions_flown": 0,
                    "status": "Ativo",
                })
            members.insert(0, {
                "name": pilot_name,
                "rank": "N/A",
                "victories": 0,
                "missions_flown": pilot_total_missions,
                "status": "Jogador",
            })

        # Ordenar por missões e vitórias
        members.sort(key=lambda x: (x.get("missions_flown", 0), x.get("victories", 0)), reverse=True)
        return members

    # Personnel
    def _load_squadron_catalog(self, campaign_name: str, squadron_id: Optional[int]) -> Dict[str, Any] | List[Any]:
        if not squadron_id:
            return {}
        candidate = (
            self.pwcg_root
            / "User" / "Campaigns" / campaign_name / "Personnel" / f"{int(squadron_id)}.json"
        )
        if not candidate.exists():
            return {}
        try:
            import json
            with candidate.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _normalize_personnel_catalog(self, catalog: Any) -> List[Dict[str, Any]]:
        pilots: List[Dict[str, Any]] = []

        if isinstance(catalog, list):
            return [p for p in catalog if isinstance(p, dict)]

        if not isinstance(catalog, dict):
            return pilots

        for key in ["pilots", "members", "personnel", "roster", "squadronMemberCollection"]:
            v = catalog.get(key)
            if isinstance(v, dict):
                pilots.extend([p for p in v.values() if isinstance(p, dict)])
            elif isinstance(v, list):
                pilots.extend([p for p in v if isinstance(p, dict)])

        for key in ["active", "reserve", "wounded", "kia", "mia", "transfer", "retired"]:
            v = catalog.get(key)
            if isinstance(v, list):
                pilots.extend([p for p in v if isinstance(p, dict)])

        if not pilots and all(isinstance(v, dict) for v in catalog.values()):
            pilots.extend(list(catalog.values()))

        # Deduplicar por nome
        seen = set()
        out = []
        for p in pilots:
            nm = str(p.get("name") or p.get("pilotName") or "").strip().lower()
            if nm and nm not in seen:
                seen.add(nm)
                out.append(p)
        return out

    # Extrações de squadronId
    def _extract_squadron_id_from_raw(self, raw: Dict[str, Any]) -> Optional[int]:
        for rm in (raw.get("missions") or [])[::-1]:
            hdr = (rm.get("missionHeader") or {})
            sid = hdr.get("squadronId") or hdr.get("squadronID") or rm.get("squadronId") or rm.get("squadronID")
            if sid:
                return sid
        return None

    def _extract_squadron_id_from_planes(self, raw: Dict[str, Any], pilot_serial: int) -> Optional[int]:
        for rm in (raw.get("missions") or [])[::-1]:
            mission_planes = rm.get("missionPlanes") or {}
            if isinstance(mission_planes, dict):
                for obj in mission_planes.values():
                    if not isinstance(obj, dict):
                        continue
                    if str(obj.get("pilotSerialNumber")) == str(pilot_serial):
                        sid = obj.get("squadronId") or obj.get("squadronID")
                        if sid:
                            return sid
        return None

    # Enriquecimento de missões
    def _enrich_missions_with_reports(self, missions: List[Dict[str, Any]], raw: Dict[str, Any]) -> None:
        reports = raw.get("combat_reports") or []
        if not missions or not reports:
            return
        by_date: Dict[str, List[Dict[str, Any]]] = {}
        for r in reports:
            by_date.setdefault(r.get("date") or "", []).append(r)
        for mission in missions:
            candidates = by_date.get(mission.get("date") or "", [])
            if not candidates:
                continue
            chosen = None
            if len(candidates) == 1:
                chosen = candidates[0]
            else:
                def score(rep: Dict[str, Any]) -> int:
                    s = 0
                    if rep.get("squadron") == mission.get("squadron"): s += 2
                    if rep.get("type") == mission.get("aircraft"): s += 1
                    if rep.get("duty") == mission.get("type"): s += 1
                    if rep.get("time") == mission.get("time"): s += 1
                    return s
                candidates = sorted(candidates, key=score, reverse=True)
                if candidates and score(candidates[0]) > 0:
                    chosen = candidates[0]
            if chosen:
                mission["report"]["narrative"] = chosen.get("narrative", "") or ""
                mission["report"]["haReport"] = chosen.get("haReport", "") or ""
                if not mission.get("squadmates"):
                    names = self._extract_names_from_hareport(mission["report"]["haReport"])
                    if names:
                        mission["squadmates"] = names

    # Utils
    @staticmethod
    def _first_non_empty(values: List[Optional[str]]) -> Optional[str]:
        for v in values:
            if isinstance(v, str) and v.strip():
                return v
        return None

    @staticmethod
    def _extract_names_from_hareport(text: str) -> List[str]:
        if not text:
            return []
        lines = [ln.strip() for ln in text.splitlines()]
        names: List[str] = []
        collecting = False
        for ln in lines:
            if not collecting and ln.lower().startswith("this mission was flown by"):
                collecting = True
                continue
            if collecting:
                if not ln:
                    break
                if any(ch.isdigit() for ch in ln):
                    continue
                names.append(ln)
        seen = set()
        uniq = []
        for n in names:
            if n not in seen:
                seen.add(n)
                uniq.append(n)
        return uniq

    @staticmethod
    def _get_pilot_status(code: Any) -> str:
        try:
            code = int(code)
        except Exception:
            return "Ativo"
        mapping = {
            0: "Ativo",
            1: "Em descanso",
            2: "Ferido",
            3: "Hospital",
            4: "MIA",
            5: "KIA",
            6: "Transferido",
        }
        return mapping.get(code, "Ativo")
