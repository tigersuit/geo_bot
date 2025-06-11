
import json
from typing import List, Dict

def load_calculations(filename: str) -> List[Dict]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_calculation(filename: str, data: Dict):
    calculations = load_calculations(filename)
    calculations.append(data)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(calculations, f, ensure_ascii=False, indent=2)

ADVICES = [
    "✅ Добавляйте 20% запас при площади < 100 м² для компенсации возможных потерь.",
    "🛠️ Используйте геотекстиль для улучшения дренажа и предотвращения смешивания слоев грунта.",
    "🚜 При укладке под дорожки выбирайте плотность от 150 г/м² и выше.",
    "🌧️ Для парковок и отмосток лучше брать 200 г/м² и выше для прочности.",
    "📦 Храните геотекстиль в сухом месте, чтобы избежать намокания перед укладкой.",
    "💡 Регулярно проверяйте наличие повреждений и своевременно ремонтируйте.",
]
