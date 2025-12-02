"""
简化的 ASR 测试脚本 - 用于调试语音识别是否正常工作。

这个脚本与官方示例保持一致，使用单线程架构。
运行后，无论您说什么，都会打印所有关键词的概率。
"""
from maix import app, nn

print("[Test] Loading ASR model...")
speech = nn.Speech("/root/models/am_3332_192_int8.mud")
speech.init(nn.SpeechDevice.DEVICE_MIC)

# 测试关键词（与官方示例类似）
kw_tbl = [
    'kai1 qi3',           # 开启 (2字)
    'fen1 lei4',          # 分类 (2字)  
    'ni3 hao3',           # 你好 (2字)
    'kai1 shi3',          # 开始 (2字)
]
kw_gate = [0.1, 0.1, 0.1, 0.1]

# 用于追踪是否收到过任何回调
callback_count = 0

def callback(data: list[float], length: int):
    """回调函数：打印所有关键词的概率（包括 0）"""
    global callback_count
    callback_count += 1
    
    # 每次回调都打印，这样可以确认回调是否被调用
    output_parts = []
    for i in range(length):
        kw_name = kw_tbl[i] if i < len(kw_tbl) else f"kw{i}"
        prob = data[i]
        # 标记高概率的关键词
        marker = " ★" if prob > 0.1 else ""
        output_parts.append(f"{kw_name}: {prob:.3f}{marker}")
    
    print(f"[Callback #{callback_count}] " + " | ".join(output_parts))

print(f"[Test] Registering {len(kw_tbl)} keywords: {kw_tbl}")
speech.kws(kw_tbl, kw_gate, callback, True)

print("[Test] ASR initialized. Start speaking!")
print("[Test] Try saying: '开启', '分类', '你好', '开始'")
print("[Test] Press Ctrl+C to stop.\n")

frame_count = 0
try:
    while not app.need_exit():
        frames = speech.run(1)
        frame_count += 1
        
        # 每 100 帧打印一次状态，确认程序在运行
        if frame_count % 100 == 0:
            print(f"[Status] Processed {frame_count} frames, {callback_count} callbacks received")
        
        if frames < 1:
            print("[Test] run() returned < 1, exiting...")
            break
except KeyboardInterrupt:
    print("\n[Test] Stopped by user.")
    
print(f"[Test] Total: {frame_count} frames, {callback_count} callbacks")
