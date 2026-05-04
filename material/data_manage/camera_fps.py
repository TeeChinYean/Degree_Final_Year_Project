import cv2
import time

def test_camera_limit(width=320, height=240):
    # 使用 CAP_DSHOW 驱动以获得更快的启动速度和控制力
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    # 强制设置一个极高的 FPS 请求，看硬件是否能响应
    cap.set(cv2.CAP_PROP_FPS, 120) 

    print(f"Testing {width}x{height}...")
    
    start_time = time.time()
    num_frames = 0
    test_duration = 5.0 # 测试 5 秒

    while (time.time() - start_time) < test_duration:
        ret, frame = cap.read()
        if not ret:
            break
        num_frames += 1

    actual_fps = num_frames / (time.time() - start_time)
    print(f"摄像头在当前分辨率下的物理极限为: {actual_fps:.2f} FPS")
    
    cap.release()

if __name__ == "__main__":
    # 分别测试不同分辨率下的表现
    test_camera_limit(320, 240)
    test_camera_limit(640, 480)
    test_camera_limit(1280, 720)
    
    
## 获取摄像头性能的代码示例，测试不同分辨率下的实际帧率表现，以评估是否存在硬件限制或带宽竞争问题。
# import cv2
# import time

# def test_camera_performance(width=320, height=240):
#     # 使用 CAP_DSHOW 驱动
#     cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
#     cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
#     cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
#     cap.set(cv2.CAP_PROP_FPS, 120) 

#     print(f"\n--- Testing {width}x{height} ---")
    
#     num_frames = 0
#     test_duration = 5.0
#     latencies = []
    
#     # 预热摄像头（防止第一帧初始化耗时干扰平均值）
#     for _ in range(5): cap.read()
    
#     start_test = time.perf_counter()
    
#     while (time.perf_counter() - start_test) < test_duration:
#         # 记录单帧获取开始时间
#         t0 = time.perf_counter()
        
#         ret, frame = cap.read()
        
#         # 记录单帧获取结束时间
#         t1 = time.perf_counter()
        
#         if not ret:
#             break
            
#         # 计算该帧耗时 (毫秒)
#         duration_ms = (t1 - t0) * 1000
#         latencies.append(duration_ms)
#         num_frames += 1

#     total_time = time.perf_counter() - start_test
#     actual_fps = num_frames / total_time
#     avg_latency = sum(latencies) / len(latencies) if latencies else 0
    
#     print(f"结果汇总:")
#     print(f" - 物理 FPS 极限: {actual_fps:.2f}")
#     print(f" - 单帧获取耗时 (平均): {avg_latency:.2f} ms")
#     print(f" - 总获取帧数: {num_frames}")
    
#     if avg_latency > (1000 / actual_fps) * 1.1:
#         print(" [警告] 获取耗时波动较大，可能存在硬件抖动或 USB 带宽竞争。")
        
#     cap.release()

# if __name__ == "__main__":
#     # 针对你的 320p 项目进行重点测试
#     test_camera_performance(320, 240)