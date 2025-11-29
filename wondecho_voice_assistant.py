"""Voice-driven garbage classification workflow for MaixCam + WonderEcho.

The logic now relies entirely on the module's出厂词条：
1. 等待唤醒词"3: 小幻小幻"，模块自带回应"我在"。
2. 等待命令词"56: 开启垃圾分类"，模块播报"已开启"。
3. 板卡拍照、上传至垃圾分类服务器。
4. 服务器返回四类垃圾中的一类，脚本调用 WonderEcho 被动播报词条
   150–153（FF 01–04）告知结果。
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import requests
import smbus  # type: ignore
from maix import app, audio, camera

# ----------------------------- Configuration ---------------------------------

@dataclass
class VoiceIds:
    wake_word: int       # WonderEcho 命令/唤醒语义编号
    query_word: int      # WonderEcho 命令语义编号
    fallback_cmd_type: int = 0x00  # ASR_CMDMAND


@dataclass
class AudioAssets:
    events: Dict[str, str] = field(default_factory=dict)
    categories: Dict[str, str] = field(default_factory=dict)
    volume: int = 80


@dataclass
class CameraConfig:
    width: int = 640
    height: int = 480
    snapshot_path: str = "/tmp/garbage_snapshot.jpg"


@dataclass
class ServerConfig:
    url: str
    timeout: int = 15


@dataclass
class AssistantConfig:
    bus_id: int = 4
    module_address: int = 0x34
    voice_ids: VoiceIds = field(default_factory=lambda: VoiceIds(wake_word=3, query_word=56))
    audio: AudioAssets = field(default_factory=AudioAssets)
    camera: CameraConfig = field(default_factory=CameraConfig)
    server: ServerConfig = field(default_factory=lambda: ServerConfig(url="http://10.4.0.3:8000/classify"))
    category_phrase_ids: Dict[str, int] = field(default_factory=dict)
    poll_interval: float = 0.1  # seconds
    query_timeout: float = 15.0  # seconds to wait for second command
    post_wake_delay: float = 2.0  # seconds to wait after wake word (let module finish speaking)
    post_query_delay: float = 1.0  # seconds to wait after query word before taking photo


# --------------------------- Voice module driver -----------------------------

ASR_RESULT_ADDR = 0x64
ASR_SPEAK_ADDR = 0x6E
ASR_CMDMAND = 0x00
ASR_ANNOUNCER = 0xFF


class ASRModule:
    def __init__(self, address: int, bus_id: int) -> None:
        self.address = address
        self.bus = smbus.SMBus(bus_id)
        self._send = [0, 0]

    def _write_block(self, reg: int, payload: list[int]) -> bool:
        try:
            self.bus.write_i2c_block_data(self.address, reg, payload)
            return True
        except OSError as err:
            print(f"[ASR] write error: {err}")
            return False

    def read_result(self) -> Optional[int]:
        try:
            data = self.bus.read_i2c_block_data(self.address, ASR_RESULT_ADDR, 1)
            if data:
                return data[0]
        except OSError as err:
            print(f"[ASR] read error: {err}")
        return None

    def speak(self, cmd: int, phrase_id: int) -> bool:
        if cmd not in (ASR_CMDMAND, ASR_ANNOUNCER):
            return False
        self._send[0] = cmd
        self._send[1] = phrase_id
        return self._write_block(ASR_SPEAK_ADDR, self._send)


# ------------------------------ Audio output ---------------------------------

class AudioResponder:
    def __init__(self, assets: AudioAssets, voice_module: Optional[ASRModule] = None) -> None:
        self.assets = assets
        self.voice = voice_module

    def _play_wav(self, path: str) -> bool:
        if not path or not os.path.exists(path):
            return False
        player = audio.Player(path)
        player.volume(self.assets.volume)
        player.play()
        return True

    def respond(self, event_key: str, fallback_phrase_id: Optional[int] = None) -> None:
        wav_path = self.assets.events.get(event_key)
        played = self._play_wav(wav_path) if wav_path else False
        if not played and fallback_phrase_id is not None and self.voice:
            self.voice.speak(ASR_CMDMAND, fallback_phrase_id)

    def announce_category(self, category: str, fallback_phrase_id: Optional[int] = None) -> None:
        wav_path = self.assets.categories.get(category)
        if wav_path and self._play_wav(wav_path):
            return
        print(f"[Audio] No WAV for category '{category}', fallback to TTS/ASR.")
        if fallback_phrase_id is not None and self.voice:
            self.voice.speak(ASR_ANNOUNCER, fallback_phrase_id)


# ------------------------------ Camera + HTTP --------------------------------

class PhotoClassifier:
    def __init__(self, cam_cfg: CameraConfig, server_cfg: ServerConfig) -> None:
        self.cam_cfg = cam_cfg
        self.server_cfg = server_cfg
        self.cam = camera.Camera(cam_cfg.width, cam_cfg.height)

    def capture_to_file(self) -> str:
        img = self.cam.read()
        snapshot_path = self.cam_cfg.snapshot_path
        os.makedirs(os.path.dirname(snapshot_path), exist_ok=True)
        img.save(snapshot_path)
        return snapshot_path

    def classify(self, image_path: str) -> Optional[str]:
        with open(image_path, "rb") as stream:
            try:
                response = requests.post(
                    self.server_cfg.url,
                    files={"file": stream},
                    timeout=self.server_cfg.timeout,
                )
                response.raise_for_status()
                payload = response.json()
                category = payload.get("category")
                print(f"[Server] Category: {category}")
                return category
            except requests.RequestException as err:
                print(f"[Server] Request failed: {err}")
                return None


# ----------------------------- Assistant logic --------------------------------

class GarbageVoiceAssistant:
    def __init__(self, cfg: AssistantConfig) -> None:
        self.cfg = cfg
        self.voice_module = ASRModule(cfg.module_address, cfg.bus_id)
        self.audio = AudioResponder(cfg.audio, self.voice_module)
        self.classifier = PhotoClassifier(cfg.camera, cfg.server)

    def _poll_until(self, target_id: int, timeout: float) -> bool:
        start = time.time()
        while not app.need_exit():
            result = self.voice_module.read_result()
            if result == target_id:
                return True
            if timeout > 0 and (time.time() - start) > timeout:
                return False
            time.sleep(self.cfg.poll_interval)
        return False

    def _handle_query(self) -> None:
        self.audio.respond("photo_ack")
        snapshot = self.classifier.capture_to_file()
        category = self.classifier.classify(snapshot)
        if category:
            self.audio.respond("result_prefix")
            fallback_id = self.cfg.category_phrase_ids.get(category)
            self.audio.announce_category(category, fallback_phrase_id=fallback_id)
        else:
            self.audio.respond("network_error")

    def run(self) -> None:
        ids = self.cfg.voice_ids
        print("[Assistant] Waiting for wake word...")
        while not app.need_exit():
            result = self.voice_module.read_result()
            if result == ids.wake_word:
                print("[Assistant] Wake word detected.")
                # Wait for module to finish speaking "我在"
                time.sleep(self.cfg.post_wake_delay)
                print("[Assistant] Awaiting query word...")
                if self._poll_until(ids.query_word, self.cfg.query_timeout):
                    print("[Assistant] Query detected.")
                    # Wait for module to finish speaking "已开启"
                    time.sleep(self.cfg.post_query_delay)
                    print("[Assistant] Capturing image...")
                    self._handle_query()
                else:
                    print("[Assistant] Query timeout.")
            time.sleep(self.cfg.poll_interval)


# ------------------------------ Entrypoint ------------------------------------

def build_default_config() -> AssistantConfig:
    audio_assets = AudioAssets(
        events={
            "wake_ack": "",
            "photo_ack": "",
            "result_prefix": "",
            "network_error": "",
        },
        categories={},
        volume=85,
    )

    cfg = AssistantConfig(
        bus_id=4,
        module_address=0x34,
        voice_ids=VoiceIds(wake_word=3, query_word=56),
        audio=audio_assets,
        camera=CameraConfig(),
        server=ServerConfig(url="http://10.4.0.3:8000/classify", timeout=15),
        category_phrase_ids={
            "可回收物": 1,   # FF 01 -> 播报语150
            "厨余垃圾": 2,   # FF 02 -> 播报语151
            "有害垃圾": 3,   # FF 03 -> 播报语152
            "其他垃圾": 4,   # FF 04 -> 播报语153
        },
        query_timeout=15.0,
        post_wake_delay=2.0,
        post_query_delay=1.0,
    )
    return cfg


def main() -> None:
    cfg = build_default_config()
    assistant = GarbageVoiceAssistant(cfg)
    try:
        assistant.run()
    except KeyboardInterrupt:
        print("[Assistant] Stopped by user.")


if __name__ == "__main__":
    main()
