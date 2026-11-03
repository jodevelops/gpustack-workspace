"""Deployment IDs from the user's document, not assertions about model families."""
from . import store

MODELS = [
    {"id":"gpt-oss-120b","type":"chat","vision":False,"description":"Textanalyse, Strukturierung und Code","verified":False},
    {"id":"qwen3.8-27b","type":"chat","vision":False,"description":"Textarbeit · Deployment und Fähigkeiten prüfen","verified":False},
    {"id":"minimax-m2.7","type":"chat","vision":False,"description":"Text und Code · Deployment prüfen","verified":False},
    {"id":"internvl3-8b-instruct","type":"chat","vision":True,"description":"Text und Bilder · Bildqualität prüfen","verified":False},
    {"id":"qwen3-embedding-0.6b","type":"embedding","vision":False,"description":"Semantische Dokumentensuche","verified":False},
    {"id":"granite-embedding-107m-multilingual","type":"embedding","vision":False,"description":"Alternative für mehrsprachige Suche","verified":False},
    {"id":"jina-reranker-v2-base-multilingual","type":"reranker","vision":False,"description":"Suchtreffer nach Relevanz ordnen","verified":False},
    {"id":"faster-whisper-large-v3","type":"audio","vision":False,"description":"Audio in Text transkribieren","verified":False},
]

# Reference configurations are bundled, never fetched when opening the app.
# A deployment alias does not prove that these exact weights/settings are served.
REFERENCES = {
    "gpt-oss-120b": (131072, "openai/gpt-oss-120b"),
    "qwen3.8-27b": (262144, "Qwen/Qwen3.8-27B"),
    "minimax-m2.7": (204800, "MiniMaxAI/MiniMax-M2.7"),
    "internvl3-8b-instruct": (32768, "OpenGVLab/InternVL3-8B"),
}

def models():
    result = store.setting("models", MODELS)
    for model in result:
        reference = REFERENCES.get(model["id"])
        model["reference"] = ({"context_tokens":reference[0], "model":reference[1],
            "url":"https://huggingface.co/"+reference[1]+"/blob/main/config.json",
            "checked":"2026-10-07", "note":"Herstellerkonfiguration (max_position_embeddings); Zuordnung zum Deployment und etwaige RoPE-Erweiterungen prüfen."} if reference else None)
        model.setdefault("deployment_context_tokens", None)
        model.setdefault("deployment_output_tokens", None)
        model.setdefault("context_source", "")
        model.setdefault("stream_usage", False)
    return result

def output_ceiling(model):
    from . import limits
    values = [limits.current()["output_max_tokens"]]
    if model.get("deployment_context_tokens"):
        values.append(model["deployment_context_tokens"] - 1)
    if model.get("deployment_output_tokens"):
        values.append(model["deployment_output_tokens"])
    return max(1, min(values))

def validate_output(model, count):
    if count > output_ceiling(model):
        raise ValueError("Ausgabetokens übersteigen das lokale Maximum oder die eingetragenen Deployment-Limits. Modellprofil und Parameter prüfen; Input benötigt ebenfalls Platz im Kontext.")

def require(model_id, kind):
    model = next((m for m in models() if m["id"] == model_id and m["type"] == kind), None)
    if not model:
        raise ValueError("Dieses Modell ist nicht für diese Aufgabe freigegeben. Bitte Modellprofile prüfen.")
    return model
