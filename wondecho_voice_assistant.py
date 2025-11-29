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

    def announce_category(self, category: str, fallback_phrase_id: Optional[int] = None) -> bool:
        """Announce garbage category via WAV or WonderEcho I2C.
        
        Returns True if announcement was sent successfully.
        """
        wav_path = self.assets.categories.get(category)
        if wav_path and self._play_wav(wav_path):
            return True
        # Use WonderEcho I2C speak command
        if fallback_phrase_id is not None and self.voice:
            print(f"[Audio] Sending I2C speak command: 0xFF 0x{fallback_phrase_id:02X} for '{category}'")
            success = self.voice.speak(ASR_ANNOUNCER, fallback_phrase_id)
            if success:
                print(f"[Audio] ✓ WonderEcho will announce: {category}")
            else:
                print(f"[Audio] ✗ I2C speak command failed!")
            return success
        return False


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
        """Main loop: voice-triggered garbage classification.
        
        Workflow:
        1. Detect voice activity (user speaking to WonderEcho)
        2. Wait for user to finish speaking
        3. Wait for WonderEcho to finish responding (e.g. "已开启")
        4. Capture photo and upload to server
        5. Wait briefly, then announce classification result
        """
        print("[Assistant] Voice-activated garbage classification ready")
        print("[Assistant] Say: 小幻小幻 → 开启垃圾分类")
        print("[Assistant] Listening for voice triggers...\n")
        
        last_trigger_time = 0
        min_trigger_interval = 8.0  # Minimum time between triggers (full workflow)
        
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
                
                print("[Assistant] Voice detected! Waiting for speech to end...")
                
                # Wait for user + WonderEcho to finish speaking
                self.audio_monitor.wait_for_silence()
                
                # Additional delay to ensure WonderEcho finished "已开启" playback
                print("[Assistant] Waiting for WonderEcho response to complete...")
                time.sleep(1.5)
                
                # Now capture photo
                print("[Assistant] Capturing image...")
                snapshot = self.classifier.capture_to_file()
                print(f"[Assistant] Photo captured: {snapshot}")
                
                # Upload to server and get result
                self._handle_classification(snapshot)
                
                last_trigger_time = time.time()  # Update after full workflow
            
            time.sleep(0.1)
            
            time.sleep(0.1)
    
    def _handle_classification(self, snapshot: str) -> None:
        """Upload snapshot to server and announce result."""
        print("[Assistant] Uploading to server...")
        category = self.classifier.classify(snapshot)
        
        if category:
            print(f"[Assistant] Result: {category}")
            fallback_id = self.cfg.category_phrase_ids.get(category)
            
            if fallback_id:
                # Brief delay to ensure WonderEcho is ready for new command
                print("[Assistant] Preparing to announce result...")
                time.sleep(0.5)
                
                # Send I2C command to WonderEcho
                success = self.audio.announce_category(category, fallback_phrase_id=fallback_id)
                
                if success:
                    # Wait for announcement to complete before next trigger
                    time.sleep(2.0)
            else:
                print(f"[Assistant] ERROR: No phrase ID for category: {category}")
                print(f"[Assistant] Available categories: {list(self.cfg.category_phrase_ids.keys())}")
        else:
            print("[Assistant] Classification failed - server error")


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
        chunk_duration=0.25,  # Very fast sampling (250ms) for quick response
        energy_threshold=700.0,  # Higher threshold - only detect clear speech
        silence_timeout=0.6,  # Minimal timeout - WonderEcho phrases are ~1s total
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
            "可回收物": 1,   # FF 01 -> 播报语150 "可回收物"
            "厨余垃圾": 2,   # FF 02 -> 播报语151 "厨余垃圾"
            "有害垃圾": 3,   # FF 03 -> 播报语152 "有害垃圾"
            "其他垃圾": 4,   # FF 04 -> 播报语153 "其他垃圾"
        },
        post_trigger_delay=1.5,  # Reduced from 2.5s - faster photo trigger
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
