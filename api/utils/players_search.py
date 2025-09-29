from dataclasses import dataclass
from pybaseball import chadwick_register
import pandas as pd
from rapidfuzz import process, fuzz

class PlayersIndex:
    def __init__(self):
        self.df = None
        self._names: list[str] = []
        self._names_lower: list[str] = []
    
    def load(self):
        if self.df is None:
            df = chadwick_register()[["key_mlbam", "name_first", "name_last"]].fillna("")
            df["full_name"] = (df["name_first"].astype(str) + " " + df["name_last"].astype(str)).str.strip()
            self.df = df
            self._names = df["full_name"].tolist()
            self._names_lower = [n.lower() for n in self._names]
    
    def search(self, query: str) -> list[dict]:
        score_cutoff = 70

        self.load()
        q = (query or "").strip()
        if not q:
            return []
        q_lower = q.lower()
        matches = process.extract(
            q_lower,
            self._names_lower,
            limit=5,
            scorer=fuzz.WRatio,
            score_cutoff=score_cutoff,
        )

        return [
            {
                "id": int(self.df.iloc[idx]["key_mlbam"]),
                "name": self._names[idx],
                "score": score,
            }
            for name, score, idx in matches
        ]

players_index = PlayersIndex()