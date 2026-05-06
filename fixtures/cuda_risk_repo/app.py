import os

import torch


os.environ["CUDA_VISIBLE_DEVICES"] = "0"


def run(model, inputs):
    if torch.cuda.is_available():
        model = model.cuda()
    return model(inputs.cuda())
