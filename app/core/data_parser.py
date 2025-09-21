from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

class PWCGFileNames:
    CAMPAIGN = "Campaign.json"
    ACES = "CampaignAces.json"
    LOG = "CampaignLog.json"
    PILOT_EXTRA = "pilot_extra.json"
    DECORATIONS = "decorations.json"
    MISSION_DATA_DIR = "MissionData"
    COMBAT_REPORTS_DIR = "CombatReports"
    MISSION_DATA_PATTERN = "*.MissionData.json"
    COMBAT_REPORT_PATTERN = "*.CombatReport.json"

class IL2DataParser:
    def __init__(self, pwcg_root: str | Path) -> None:
        self.base_path = Path(pwcg_root) / "User" / "Campaigns"

    def get_campaigns(self) -> List[str]:
        if not self.base_path.exists():
            return []
        return [d.name for d in self.base_path.iterdir() if d.is_dir()]

    def _safe_load_json(self, path: Path) -> Any:
        if not path.exists():
            return {}
        try:
            with path.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _load_many_json(self, paths: List[Path]) -> List[Any]:
        out: List[Any] = []
        for p in paths:
            try:
                with p.open(encoding="utf-8") as f:
                    out.append(json.load(f))
            except Exception:
                continue
        return out

    def parse_campaign_json(self, campaign_name: str) -> Optional[Dict[str, Any]]:
        campaign_dir = self.base_path / campaign_name
        if not campaign_dir.exists():
            return None
        campaign = self._safe_load_json(campaign_dir / PWCGFileNames.CAMPAIGN)
        aces = self._safe_load_json(campaign_dir / PWCGFileNames.ACES)
        log = self._safe_load_json(campaign_dir / PWCGFileNames.LOG)
        pilot_extra = self._safe_load_json(campaign_dir / PWCGFileNames.PILOT_EXTRA)
        decorations = self._safe_load_json(campaign_dir / PWCGFileNames.DECORATIONS)
        mission_dir = campaign_dir / PWCGFileNames.MISSION_DATA_DIR
        mission_files = list(mission_dir.glob(PWCGFileNames.MISSION_DATA_PATTERN)) if mission_dir.exists() else []
        missions = self._load_many_json(sorted(mission_files))
        combat_dir = campaign_dir / PWCGFileNames.COMBAT_REPORTS_DIR
        combat_files: List[Path] = []
        if combat_dir.exists():
            combat_files.extend(combat_dir.glob(PWCGFileNames.COMBAT_REPORT_PATTERN))
            for sub in combat_dir.iterdir():
                if sub.is_dir():
                    combat_files.extend(sub.glob(PWCGFileNames.COMBAT_REPORT_PATTERN))
        combat_reports = self._load_many_json(sorted(combat_files))
        return {
            "campaign": campaign,
            "aces": aces,
            "log": log,
            "pilot_extra": pilot_extra,
            "decorations": decorations,
            "missions": missions,
            "combat_reports": combat_reports,
            "campaign_name": campaign_name,
            "campaign_path": str(campaign_dir),
        }
