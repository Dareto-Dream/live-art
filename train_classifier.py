import os
import torch
import torch.nn as nn
import torchvision.datasets as datasets
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import torch.onnx

# Paths
DATA_DIR = "/mnt/usb/sketch_dataset"
ONNX_PATH = "models/quickdraw.onnx"
IMG_SIZE = 224
EPOCHS = 10
BATCH_SIZE = 32

# Preprocessing
transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=3),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor()
])

# Load dataset
dataset = datasets.ImageFolder(DATA_DIR, transform=transform)
loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)
num_classes = len(dataset.classes)

# CNN Model
class SketchCNN(nn.Module):
    def __init__(self, classes):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2),
            nn.Flatten(),
            nn.Linear(64 * 56 * 56, 256), nn.ReLU(),
            nn.Linear(256, classes)
        )
    def forward(self, x): return self.net(x)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = SketchCNN(num_classes).to(device)
opt = torch.optim.Adam(model.parameters(), lr=1e-4)
loss_fn = nn.CrossEntropyLoss()

# Training
for epoch in range(EPOCHS):
    model.train()
    total = 0
    correct = 0
    for imgs, labels in loader:
        imgs, labels = imgs.to(device), labels.to(device)
        opt.zero_grad()
        out = model(imgs)
        loss = loss_fn(out, labels)
        loss.backward()
        opt.step()
        pred = torch.argmax(out, dim=1)
        correct += (pred == labels).sum().item()
        total += labels.size(0)
    acc = correct / total
    print(f"[Epoch {epoch+1}] Accuracy: {acc:.2%}")

# Save to ONNX
dummy = torch.randn(1, 3, IMG_SIZE, IMG_SIZE).to(device)
torch.onnx.export(model, dummy, ONNX_PATH,
                  input_names=["input"], output_names=["output"],
                  dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}},
                  opset_version=11)

print(f"[DONE] Model exported to {ONNX_PATH}")
