import argparse
import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torch.utils.data import DataLoader
import torchvision
from torch.profiler import profile, record_function, ProfilerActivity

class TrafficSignNet(nn.Module):
    def __init__(self):
        super(TrafficSignNet, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3)
        self.fc1 = nn.Linear(64 * 6 * 6, 128)
        self.fc2 = nn.Linear(128, 43) # 43 classes in GTSRB dataset

    def forward(self, x):
        x = torch.relu(self.conv1(x))
        x = torch.max_pool2d(x, 2)
        x = torch.relu(self.conv2(x))
        x = torch.max_pool2d(x, 2)
        x = torch.flatten(x, 1)
        x = torch.relu(self.fc1(x))
        x = self.fc2(x)
        return x

parser = argparse.ArgumentParser()
parser.add_argument('-m', '--model', type=str,
                    help='Model file path')

args = parser.parse_args()

model_path = args.model if args.model else './models/traffic_sign_net.pth'

# Load the model
model = TrafficSignNet()
model.load_state_dict(torch.load(model_path))
model.eval()

# Define transformations for the testing data
transform = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.ToTensor(),
    transforms.Normalize((0.5,), (0.5,))
])

# Load the GTSRB test dataset
test_set = torchvision.datasets.GTSRB(root='./data', split='test', download=True, transform=transform)
test_loader = DataLoader(test_set, batch_size=64, shuffle=False)

correct = 0
total = 0
with torch.no_grad():
    for data in test_loader:
        images, labels = data
        with profile(activities=[ProfilerActivity.CPU], record_shapes=True) as prof:
            with record_function("model_inference"):
                outputs = model(images)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

print("---------------------------------------------------------")
print(f'Accuracy of the model on the test images: {100 * correct / total:.2f}%')
print(prof.key_averages().table(sort_by="cpu_time_total", row_limit=10))