import json
import os
import time
from pathlib import Path
from typing import Dict

import requests
from confluent_kafka import Producer


def load_env() -> Dict[str, str]:
    required = ["KAFKA_BOOTSTRAP", "KAFKA_TOPIC", "STT_API_URL", "STT_API_KEY"]
    config: Dict[str, str] = {}
    for key in required:
        value = os.getenv(key)
        if not value:
            raise RuntimeError(f"환경변수 {key} 가 설정되어 있지 않습니다.")
        config[key] = value
    return config


def create_producer(bootstrap_servers: str) -> Producer:
    return Producer(
        {
            "bootstrap.servers": bootstrap_servers,
            "client.id": "voice-producer",
            "linger.ms": 50,
            "acks": "1",
        }
    )


def transcribe_audio(api_url: str, api_key: str, audio_path: Path) -> Dict:
    with audio_path.open("rb") as audio_file:
        files = {"file": audio_file}
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.post(api_url, headers=headers, files=files, timeout=30)

    response.raise_for_status()
    return response.json()


def build_message(session_id: str, transcript: Dict) -> Dict:
    return {
        "session_id": session_id,
        "channel": "voice",
        "transcript": transcript.get("text", ""),
        "confidence": transcript.get("confidence", 0.0),
        "segments": transcript.get("segments", []),
        "timestamp": int(time.time() * 1000),
    }


def send_message(producer: Producer, topic: str, payload: Dict) -> None:
    producer.produce(topic, json.dumps(payload).encode("utf-8"))
    producer.flush()


def main() -> None:
    config = load_env()
    producer = create_producer(config["KAFKA_BOOTSTRAP"])

    audio_file = os.getenv("AUDIO_FILE_PATH", "sample.wav")
    audio_path = Path(audio_file)
    use_mock = config["STT_API_URL"].lower() == "mock"

    if audio_path.exists() and not use_mock:
        transcript = transcribe_audio(
            config["STT_API_URL"],
            config["STT_API_KEY"],
            audio_path,
        )
    else:
        transcript = {
            "text": "샘플 통화입니다. 배송 문의를 도와드리겠습니다.",
            "confidence": 0.95,
            "segments": [
                {"start": 0.0, "end": 2.5, "text": "샘플 통화입니다."},
                {"start": 2.5, "end": 4.8, "text": "배송 문의를 도와드리겠습니다."},
            ],
        }

    payload = build_message("session-voice-001", transcript)
    send_message(producer, config["KAFKA_TOPIC"], payload)
    print("메시지 전송 완료:", json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
