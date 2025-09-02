import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["MKLDNN_VERBOSE"] = "0"
os.environ["ATEN_NO_MKL"] = "1"
os.environ["ATEN_NO_MKLDNN"] = "1"

import torch
from torchvision import transforms
from PIL import Image
from io import BytesIO
import os

from app.captcha.model_def_yellow import BetterCRNN, CHARS

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

num_classes = len(CHARS)
model = BetterCRNN(num_classes).to(device)

model_path = os.path.join(os.path.dirname(__file__), "..", "models", "model_yellow.pt")
model.load_state_dict(torch.load(model_path, map_location=device))
model.eval()

transform = transforms.Compose([
    transforms.Grayscale(),
    transforms.Resize((60, 200)),
    transforms.ToTensor()
])

def predict_captcha_from_bytes(png_data: bytes) -> str:
    image = Image.open(BytesIO(png_data)).convert("RGB")
    image = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(image)
        output = torch.nn.functional.log_softmax(output, dim=2)
        preds = torch.argmax(output, dim=2)[0].tolist()

    decoded = []
    prev = -1
    for p in preds:
        if p != prev and p != num_classes:
            decoded.append(CHARS[p])
        prev = p

    return "".join(decoded)
