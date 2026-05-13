import json
import os


class HighScoreManager:
    def __init__(self, filename="data/highscores.json"):
        self.filename = filename
        self.scores = self.load()

    def load(self):
        folder = os.path.dirname(self.filename)

        if folder != "":
            os.makedirs(folder, exist_ok=True)

        if not os.path.exists(self.filename):
            return {}

        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                return json.load(file)
        except:
            return {}

    def save(self):
        with open(self.filename, "w", encoding="utf-8") as file:
            json.dump(self.scores, file, indent=4)

    def get(self, stage_name):
        return self.scores.get(stage_name, 0)

    def update(self, stage_name, score):
        old_score = self.get(stage_name)

        if score > old_score:
            self.scores[stage_name] = score
            self.save()
            return True

        return False