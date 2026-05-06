import torch


def select_device():
    return "cuda" if torch.cuda.is_available() else "cpu"


def run(model, inputs):
    device = select_device()
    return model.to(device)(inputs.to(device))
