import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["MKLDNN_VERBOSE"] = "0"
os.environ["ATEN_NO_MKL"] = "1"
os.environ["ATEN_NO_MKLDNN"] = "1"

import torch
torch.backends.mkldnn.enabled = False
torch.set_num_threads(1)
required_version = "1.8.2+cpu"
if torch.__version__ != required_version:
    raise RuntimeError(f"Найдена torch {torch.__version__}, требуется {required_version}")

print("Версия PyTorch ок:", torch.__version__)


CHARS = "агдежикмпрстуфцчшщя"

class SimpleCRNN(torch.nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.cnn = torch.nn.Sequential(
            torch.nn.Conv2d(1, 32, 3, padding=1), torch.nn.BatchNorm2d(32), torch.nn.ReLU(), torch.nn.MaxPool2d(2, 2),
            torch.nn.Conv2d(32, 64, 3, padding=1), torch.nn.BatchNorm2d(64), torch.nn.ReLU(), torch.nn.MaxPool2d(2, 2),
            torch.nn.Dropout(0.25)
        )
        self.rnn = torch.nn.LSTM(64 * 12, 128, batch_first=True, bidirectional=True)
        self.fc = torch.nn.Linear(128 * 2, num_classes + 1)

    def forward(self, x):
        x = self.cnn(x)
        b, c, h, w = x.size()
        x = x.permute(0, 3, 1, 2).reshape(b, w, -1)
        x, _ = self.rnn(x)
        x = self.fc(x)
        return x