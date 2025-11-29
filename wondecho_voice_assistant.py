"""Voice-driven garbage classification workflow for MaixCam + WonderEcho.

Updated workflow using audio monitoring instead of I2C polling:
1. 用户说"小幻小幻" → WonderEcho播报"我在"
2. 用户说"开启垃圾分类" → WonderEcho播报"已开启" 
3. **麦克风监听到"已开启"语音** → 板卡自动拍照
4. 上传照片至垃圾分类服务器
5. 服务器返回分类结果，调用 WonderEcho 被动播报词条 150–153 (FF 01–04)

Note: I2C register 0x64 does not update with recognition results, 
so we use audio-triggered approach instead.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

import requests
import smbus  # type: ignore
from maix import app, audio, camera
import numpy as np  # For audio processing

# ----------------------------- Configuration ---------------------------------

@dataclass
class AudioConfig:
    sample_rate: int = 16000
    chunk_duration: float = 0.5  # seconds  
    energy_threshold: float = 500.0  # Voice activity detection threshold
    silence_timeout: float = 3.0  # seconds to wait after last voice activity


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
    voice_ids: VoiceIds = field(default_factory=lambda: VoiceIds(wake_word=3, query_word=100))
    audio_config: AudioConfig = field(default_factory=AudioConfig)
    audio_assets: AudioAssets = field(default_factory=AudioAssets)
    camera: CameraConfig = field(default_factory=CameraConfig)
    server: ServerConfig = field(default_factory=lambda: ServerConfig(url="http://10.4.0.3:8000/classify"))
    category_phrase_ids: Dict[str, int] = field(default_factory=dict)
    post_trigger_delay: float = 2.5  # seconds to wait after detecting trigger phrase before taking photo


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

    def clear_result(self) -> bool:
        """Clear the result register by writing 0x00."""
        try:
            self.bus.write_byte_data(self.address, ASR_RESULT_ADDR, 0x00)
            return True
        except OSError as err:
            print(f"[ASR] clear error: {err}")
            return False

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

class AudioMonitor:
    """Monitor microphone input to detect voice activity."""
    
    def __init__(self, cfg: AudioConfig) -> None:
        self.cfg = cfg
        self.recorder = audio.Recorder(sample_rate=cfg.sample_rate)
        
    def detect_voice_activity(self, duration: float) -> bool:
        """Record for specified duration and check if voice energy exceeds threshold."""
        samples_needed = int(self.cfg.sample_rate * duration)
        data = self.recorder.record(samples_needed)
        
        if data is None or len(data) == 0:
            return False
        
        # Calculate RMS energy
        try:
            # Convert bytes to numpy array if needed
            if isinstance(data, bytes):
                import struct
                samples = struct.unpack(f'{len(data)//2}h', data)
            else:
                samples = data
            
            energy = sum(abs(s) for s in samples) / len(samples)
            return energy > self.cfg.energy_threshold
        except Exception as e:
            print(f"[Audio] Energy calculation error: {e}")
            return False
    
    def wait_for_silence(self) -> None:
        """Wait until audio energy drops below threshold (indicates end of speech)."""
        print("[Audio] Waiting for speech to end...")
        silence_start = None
        
        while True:
            has_voice = self.detect_voice_activity(self.cfg.chunk_duration)
            
            if has_voice:
                silence_start = None  # Reset silence timer
            else:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start > self.cfg.silence_timeout:
                    print("[Audio] Silence detected, speech ended")
                    return
            
            time.sleep(0.1)


class GarbageVoiceAssistant:
    def __init__(self, cfg: AssistantConfig) -> None:
        self.cfg = cfg
        self.voice_module = ASRModule(cfg.module_address, cfg.bus_id)
        self.audio = AudioResponder(cfg.audio_assets, self.voice_module)
        self.classifier = PhotoClassifier(cfg.camera, cfg.server)
        self.audio_monitor = AudioMonitor(cfg.audio_config)

    def _handle_query(self) -> None:
        """Legacy method - kept for compatibility."""
        self.audio.respond("photo_ack")
        snapshot = self.classifier.capture_to_file()
        self._handle_classification(snapshot)

    def _handle_query_with_snapshot(self, snapshot: str) -> None:
        """Legacy method - kept for compatibility."""
        self._handle_classification(snapshot)

    def run(self) -> None:
        """Main loop: monitor audio for voice activity, trigger photo on speech detection."""
        print("[Assistant] Voice-activated garbage classification ready")
        print("[Assistant] Say: 小幻小幻 → 开启垃圾分类")
        print("[Assistant] Listening for voice triggers...\n")
        
        last_trigger_time = 0
        min_trigger_interval = 5.0  # Minimum seconds between triggers
        
        while not app.need_exit():
            # Detect voice activity
            has_voice = self.audio_monitor.detect_voice_activity(
                self.cfg.audio_config.chunk_duration
            )
            
            if has_voice:
                current_time = time.time()
                
                # Debounce: ignore if too soon after last trigger
                if current_time - last_trigger_time < min_trigger_interval:
                    time.sleep(0.1)
                    continue
                
                print("[Assistant] Voice detected! Waiting for speech to complete...")
                
                # Wait for silence (speech finished)
                self.audio_monitor.wait_for_silence()
                
                # Delay to let WonderEcho finish playback
                print(f"[Assistant] Waiting {self.cfg.post_trigger_delay}s for module playback...")
                time.sleep(self.cfg.post_trigger_delay)
                
                # Take photo
                print("[Assistant] Capturing image...")
                snapshot = self.classifier.capture_to_file()
                print(f"[Assistant] Photo saved: {snapshot}")
                
                # Upload and get classification
                self._handle_classification(snapshot)
                
                last_trigger_time = current_time
            
            time.sleep(0.1)
    
    def _handle_classification(self, snapshot: str) -> None:
        """Upload snapshot to server and announce result."""
        print("[Assistant] Uploading to classification server...")
        category = self.classifier.classify(snapshot)
        
        if category:
            print(f"[Assistant] Classification result: {category}")
            fallback_id = self.cfg.category_phrase_ids.get(category)
            
            if fallback_id:
                print(f"[Assistant] Announcing result via WonderEcho (phrase {fallback_id})...")
                self.audio.announce_category(category, fallback_phrase_id=fallback_id)
            else:
                print(f"[Assistant] No phrase ID configured for category: {category}")
        else:
            print("[Assistant] Classification failed - server error")
            self.audio.respond("network_error")


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
    
    audio_config = AudioConfig(
        sample_rate=16000,
        chunk_duration=0.3,  # Faster sampling for quicker response
        energy_threshold=600.0,  # Higher threshold to ignore echoes and background noise
        silence_timeout=0.8,  # Shorter timeout - WonderEcho phrases are very brief (~1s)
    )

    cfg = AssistantConfig(
        bus_id=4,
        module_address=0x34,
        voice_ids=VoiceIds(wake_word=3, query_word=56),
        audio_config=audio_config,
        audio_assets=audio_assets,
        camera=CameraConfig(),
        server=ServerConfig(url="http://10.4.0.3:8000/classify", timeout=15),
        category_phrase_ids={
            "可回收物": 1,   # FF 01 -> 被动播报语ID 1
            "厨余垃圾": 2,   # FF 02 -> 被动播报语ID 2  
            "有害垃圾": 3,   # FF 03 -> 被动播报语ID 3
            "其他垃圾": 4,   # FF 04 -> 被动播报语ID 4
        },
        post_trigger_delay=2.5,  # Wait for WonderEcho to finish playback
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
