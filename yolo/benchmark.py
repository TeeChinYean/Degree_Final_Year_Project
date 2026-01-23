from ultralytics.utils.benchmarks import benchmark

# Benchmark on GPU
benchmark(model="F:/Degree_Final_Year_Project/runs/detect/fine2/train2/weights/best.pt", data="F:/Degree_Final_Year_Project/recycle/data.yaml", imgsz=640, half=False, device=0)
