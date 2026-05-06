import torch


def select_device():
    return "cuda" if torch.cuda.is_available() else "cpu"


def run(model, inputs):
    device = select_device()
    model = model.to(device)
    inputs = inputs.to(device)
    return model(inputs)
