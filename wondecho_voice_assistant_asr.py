"""Voice-driven garbage classification workflow for MaixCam + WonderEcho (ASR Version).

Updated workflow using MaixCam ASR (Keyword Spotting):
1. 用户说"小幻小幻" → WonderEcho播报"我在"
2. 用户说"开启垃圾分类" → MaixCam 识别到关键词 "kai1 qi3 la1 ji1 fen1 lei4"
3. **MaixCam 识别成功** → 板卡自动拍照
4. 上传照片至垃圾分类服务器
5. 服务器返回分类结果，**MaixCam 扬声器播放提示音**

Requires:
- /root/models/am_3332_192_int8.mud (Acoustic model for speech recognition)

Architecture:
- 使用多线程架构避免 Overrun：
  - ASR 线程：持续运行 speech.run()，保持音频缓冲区被消费
  - 主线程：处理拍照、上传、播报等耗时操作
"""
from __future__ import annotations

import os
import time
import threading
from queue import Queue, Empty
from dataclasses import dataclass, field
from typing import Dict, Optional

import requests
import smbus  # type: ignore
from maix import app, audio, camera, nn
import numpy as np

# ----------------------------- Configuration ---------------------------------

@dataclass
class AudioConfig:
    sample_rate: int = 16000
    # ASR model path
    asr_model_path: str = "/root/models/am_3332_192_int8.mud"
    # Keywords to listen for (Pinyin)
    keywords: list[str] = field(default_factory=lambda: ['kai1 qi3 la1 ji1 fen1 lei4'])
    # Thresholds for keywords
    thresholds: list[float] = field(default_factory=lambda: [0.3])


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
    post_trigger_delay: float = 0.0


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
            print(f"[Audio] File not found: {path}")
            return False
        
        player = None
        try:
            print(f"[Audio] Playing: {path}")
            player = audio.Player(path)
            player.volume(self.assets.volume)
            player.play()
            
            # 等待播放完成
            time.sleep(2.0)
            
            print(f"[Audio] Playback finished")
            return True
        except Exception as e:
            print(f"[Audio] Playback error: {e}")
            return False
        finally:
            if player is not None:
                try:
                    del player
                    time.sleep(0.2)
                except:
                    pass

    def respond(self, event_key: str, fallback_phrase_id: Optional[int] = None) -> None:
        wav_path = self.assets.events.get(event_key)
        played = self._play_wav(wav_path) if wav_path else False
        if not played and fallback_phrase_id is not None and self.voice:
            self.voice.speak(ASR_CMDMAND, fallback_phrase_id)

    def announce_category(self, category: str, fallback_phrase_id: Optional[int] = None) -> bool:
        wav_path = self.assets.categories.get(category)
        if not wav_path:
            print(f"[Audio] ✗ No audio file configured for category: {category}")
            return False
        
        if not os.path.exists(wav_path):
            print(f"[Audio] ✗ Audio file not found: {wav_path}")
            return False
        
        print(f"[Audio] Playing result for '{category}': {wav_path}")
        if self._play_wav(wav_path):
            print(f"[Audio] ✓ Successfully announced: {category}")
            return True
        else:
            print(f"[Audio] ✗ Failed to play audio for: {category}")
            return False


# ------------------------------ Camera + HTTP --------------------------------

class PhotoClassifier:
    def __init__(self, cam_cfg: CameraConfig, server_cfg: ServerConfig) -> None:
        self.cam_cfg = cam_cfg
        self.server_cfg = server_cfg
        self.cam = camera.Camera(cam_cfg.width, cam_cfg.height)
        _ = self.cam.read()

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

class KeywordSpotter:
    """Monitor microphone input for specific keywords using Maix ASR.
    
    使用独立线程持续运行 speech.run()，避免 overrun。
    检测到关键词时，将事件放入队列供主线程消费。
    """
    
    def __init__(self, cfg: AudioConfig) -> None:
        self.cfg = cfg
        self.speech = None
        self.detected_keyword_index = -1
        
        # 事件队列：ASR 线程检测到关键词后，放入队列
        self.event_queue: Queue[int] = Queue(maxsize=10)
        
        # 线程控制
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # 暂停标志：当主线程在播放音频时，暂时忽略检测结果
        self._paused = False
        
        if not os.path.exists(cfg.asr_model_path):
            print(f"[ASR] Error: Model file not found at {cfg.asr_model_path}")
            return
        
        try:
            self.speech = nn.Speech(cfg.asr_model_path)
            self.speech.init(nn.SpeechDevice.DEVICE_MIC)
            
            # Register callback
            self.speech.kws(cfg.keywords, cfg.thresholds, self._callback, True)
            print(f"[ASR] Initialized. Listening for: {cfg.keywords}")
        except Exception as e:
            print(f"[ASR] Initialization failed: {e}")
            self.speech = None

    def _callback(self, data: list[float], length: int):
        """Callback from ASR engine with probabilities."""
        for i in range(length):
            # 调试输出：打印所有置信度 > 0.05 的结果
            # 这样可以看到模型是否在"听"，以及置信度是多少
            if data[i] > 0.05:
                kw = self.cfg.keywords[i] if i < len(self.cfg.keywords) else f"kw{i}"
                threshold = self.cfg.thresholds[i] if i < len(self.cfg.thresholds) else 0.3
                status = "✓ TRIGGER!" if data[i] > threshold else ""
                print(f"[ASR] '{kw}' Prob: {data[i]:.3f} (threshold: {threshold}) {status}")

            # 检测到关键词且未暂停
            if i < len(self.cfg.thresholds) and data[i] > self.cfg.thresholds[i] and not self._paused:
                self.detected_keyword_index = i
                # 放入队列，不阻塞（如果队列满了就丢弃）
                try:
                    self.event_queue.put_nowait(i)
                except:
                    pass  # 队列满了，丢弃这个事件

    def _asr_thread_loop(self):
        """ASR 线程主循环：持续调用 speech.run() 消费音频数据。"""
        print("[ASR Thread] Started")
        while self._running and not app.need_exit():
            if self.speech:
                try:
                    # 持续运行，保持缓冲区被消费
                    frames = self.speech.run(1)
                    if frames < 0:
                        print("[ASR Thread] Error in speech.run()")
                        time.sleep(0.1)
                except Exception as e:
                    print(f"[ASR Thread] Exception: {e}")
                    time.sleep(0.1)
            else:
                time.sleep(0.1)
        print("[ASR Thread] Stopped")

    def start(self):
        """启动 ASR 监听线程。"""
        if self._thread is not None and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._asr_thread_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止 ASR 监听线程。"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def pause(self):
        """暂停检测（但继续消费音频数据，避免 overrun）。"""
        self._paused = True
        # 清空队列中积压的事件
        while not self.event_queue.empty():
            try:
                self.event_queue.get_nowait()
            except Empty:
                break

    def resume(self):
        """恢复检测。"""
        self._paused = False

    def get_event(self, timeout: float = 0.1) -> int:
        """从队列获取检测事件，返回关键词索引或 -1。"""
        try:
            return self.event_queue.get(timeout=timeout)
        except Empty:
            return -1


class GarbageVoiceAssistant:
    def __init__(self, cfg: AssistantConfig) -> None:
        self.cfg = cfg
        self.voice_module = ASRModule(cfg.module_address, cfg.bus_id)
        self.audio = AudioResponder(cfg.audio_assets, self.voice_module)
        self.classifier = PhotoClassifier(cfg.camera, cfg.server)
        # Use KeywordSpotter with threading
        self.kws = KeywordSpotter(cfg.audio_config)

    def run(self) -> None:
        """Main loop: voice-triggered garbage classification.
        
        架构说明：
        - ASR 线程：持续运行 speech.run()，保持音频缓冲区被消费（避免 overrun）
        - 主线程：处理拍照、上传、播报等耗时操作
        - 通过队列通信：ASR 线程检测到关键词 → 放入队列 → 主线程取出处理
        """
        print("[Assistant] 语音垃圾分类已就绪")
        print("[Assistant] 说「开启垃圾」触发拍照")
        print("[Assistant] 正在监听...\n")
        
        # 启动 ASR 监听线程
        self.kws.start()
        
        last_trigger_time = 0
        min_trigger_interval = 3.0
        
        try:
            while not app.need_exit():
                # 从队列获取检测事件（非阻塞，超时 0.1 秒）
                keyword_idx = self.kws.get_event(timeout=0.1)
                
                if keyword_idx >= 0:
                    current_time = time.time()
                    keyword = self.cfg.audio_config.keywords[keyword_idx]
                    
                    # Debounce
                    if current_time - last_trigger_time < min_trigger_interval:
                        continue
                    
                    print(f"[Assistant] Keyword detected: '{keyword}'! Capturing...")
                    
                    # 暂停 ASR 检测（但线程继续运行，消费音频数据）
                    self.kws.pause()
                    
                    # Capture photo
                    snapshot = self.classifier.capture_to_file()
                    print(f"[Assistant] Photo captured: {snapshot}")
                    
                    # Upload to server and announce result
                    self._handle_classification(snapshot)
                    
                    last_trigger_time = time.time()
                    
                    # 恢复 ASR 检测
                    self.kws.resume()
                    print("[Assistant] Listening for keywords...\n")
        finally:
            # 确保线程被正确停止
            self.kws.stop()
    
    def _handle_classification(self, snapshot: str) -> None:
        """Upload snapshot to server and announce result."""
        print("[Assistant] Uploading to server...")
        category = self.classifier.classify(snapshot)
        
        if category:
            print(f"[Assistant] Classification result: {category}")
            success = self.audio.announce_category(category)
            if success:
                print(f"[Assistant] ✓ Result announced successfully")
                time.sleep(0.5)  # 短暂等待，让用户听清结果
            else:
                print(f"[Assistant] ✗ Failed to announce result")
        else:
            print("[Assistant] Classification failed - server error")


# ------------------------------ Entrypoint ------------------------------------

def build_default_config() -> AssistantConfig:
    audio_dir = "/root/garbage_audio"
    
    audio_assets = AudioAssets(
        events={},
        categories={
            "可回收物": f"{audio_dir}/recyclable.wav",
            "厨余垃圾": f"{audio_dir}/kitchen.wav",
            "有害垃圾": f"{audio_dir}/hazardous.wav",
            "其他垃圾": f"{audio_dir}/other.wav",
        },
        volume=85,
    )
    
    # Configure ASR - 监听"开启垃圾"
    audio_config = AudioConfig(
        sample_rate=16000,
        asr_model_path="/root/models/am_3332_192_int8.mud",
        keywords=['kai1 qi3 la1 ji1'],  # 开启垃圾
        thresholds=[0.2],
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
            "可回收物": 1,
            "厨余垃圾": 2,
            "有害垃圾": 3,
            "其他垃圾": 4,
        },
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
