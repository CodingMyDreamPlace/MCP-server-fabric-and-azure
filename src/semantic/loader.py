import os
import yaml

class SemanticLoader:
    def __init__(self, entities_dir: str = "config/entities"):
        self.entities_dir = entities_dir
        self._cache: dict = {}
        self._load_all()

    def _load_all(self):
        for fname in os.listdir(self.entities_dir):
            if fname.endswith(".yaml"):
                with open(f"{self.entities_dir}/{fname}") as f:
                    entity = yaml.safe_load(f)
                    self._cache[entity["entity"]] = entity

    def get_entity(self, name: str) -> dict:
        if name not in self._cache:
            raise ValueError(f"Entidad '{name}' no existe. Disponibles: {list(self._cache)}")
        return self._cache[name]

    def list_entities(self) -> list[dict]:
        return [
            {"entity": k, "description": v["description"], "backends": list(v["backends"].keys())}
            for k, v in self._cache.items()
        ]