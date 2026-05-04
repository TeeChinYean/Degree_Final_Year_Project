from ultralytics import YOLO

# Load the trained model
model = YOLO(r"F:\Degree_Final_Year_Project\pt\secondTrain\3R_fine_tune3\weights\best.pt")

# Validate using dataset defined in data.yaml
metrics = model.val(
    data=r"F:\Degree_Final_Year_Project\3R2\data.yaml",
    device=0  # set to 'cpu' if no GPU
)

# Print useful values
print("mAP50-95:", metrics.box.map)
print("mAP50:", metrics.box.map50)
print("mAP75:", metrics.box.map75)
print("Class-wise mAP:", metrics.box.maps)  # list per class
