import torch

CHARS = "0123456789"
num_classes = len(CHARS)

class BetterCRNN(torch.nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.cnn = torch.nn.Sequential(
            torch.nn.Conv2d(1, 64, 3, padding=1), torch.nn.BatchNorm2d(64), torch.nn.ReLU(), torch.nn.MaxPool2d(2, 2),
            torch.nn.Conv2d(64, 128, 3, padding=1), torch.nn.BatchNorm2d(128), torch.nn.ReLU(), torch.nn.MaxPool2d(2, 2),
            torch.nn.Conv2d(128, 256, 3, padding=1), torch.nn.BatchNorm2d(256), torch.nn.ReLU(),
            torch.nn.Conv2d(256, 256, 3, padding=1), torch.nn.BatchNorm2d(256), torch.nn.ReLU(), torch.nn.MaxPool2d((2, 1)),
            torch.nn.Dropout(0.3),
        )

        self.rnn = torch.nn.LSTM(256 * 7, 256, batch_first=True, bidirectional=True, num_layers=2)
        self.fc = torch.nn.Linear(512, num_classes + 1)

    def forward(self, x):
        x = self.cnn(x)
        b, c, h, w = x.size()
        x = x.permute(0, 3, 1, 2).reshape(b, w, -1)
        x, _ = self.rnn(x)
        x = self.fc(x)
        return x
