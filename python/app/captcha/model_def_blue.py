import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["MKLDNN_VERBOSE"] = "0"
os.environ["ATEN_NO_MKL"] = "1"
os.environ["ATEN_NO_MKLDNN"] = "1"

import torch.nn as nn

CHARS = "агдежикмпрстуфцчшщя"

class SimpleCRNN(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2, 2),
            nn.Dropout(0.25)
        )
        self.rnn = nn.LSTM(64 * 12, 128, batch_first=True, bidirectional=True)
        self.fc = nn.Linear(128 * 2, num_classes + 1)

    def forward(self, x):
        x = self.cnn(x)
        b, c, h, w = x.size()
        x = x.permute(0, 3, 1, 2).reshape(b, w, -1)
        x, _ = self.rnn(x)
        x = self.fc(x)
        return x