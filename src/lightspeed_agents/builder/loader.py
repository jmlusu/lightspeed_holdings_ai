import json
from pathlib import Path
import yaml


class CompanyLoader:

    def __init__(self, company_dir: str = "company"):
        self.company_dir = Path(company_dir)

    def load(self):

        return {
            "agents": self._load_json("agent-registry.json"),
            "departments": self._load_yaml("departments.yaml"),
            "models": self._load_yaml("models.yaml"),
            "workflows": self._load_yaml("workflows.yaml"),
            "kpis": self._load_yaml("config/kpis.yaml"),
        }

    def _load_json(self, filename):

        path = self.company_dir / filename

        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_yaml(self, filename):

        path = self.company_dir / filename

        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
