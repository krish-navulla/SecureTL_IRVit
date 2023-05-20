'''
Secure Triplet Loss Project Repository (https://github.com/jtrpinto/SecureTL)

File: face_train_securetl_model.py
- Used to train a model with face data, with the original formulation of the Secure Triplet Loss.

  REQUIRES:
  - facenet_pytorch package by Tim Esler
    (https://github.com/timesler/facenet-pytorch)

"Secure Triplet Loss: Achieving Cancelability and Non-Linkability in End-to-End Deep Biometrics"
João Ribeiro Pinto, Miguel V. Correia, and Jaime S. Cardoso
IEEE Transactions on Biometrics, Behavior, and Identity Science

joao.t.pinto@inesctec.pt  |  https://jtrpinto.github.io
'''

import os
import torch
import numpy as np
import pickle as pk
from models import SecureModel, SecureFaceNetwork, SecureIrisNetwork, SecureAttentionIrisNetwork
from losses import SecureTripletLoss
from dataset import SecureFaceDataset
from trainer import train_secure_triplet_model
from torch.utils.data import DataLoader
from facenet_pytorch import InceptionResnetV1

import facenet_pytorch
from facenet_pytorch.models.inception_resnet_v1 import InceptionResnetV1
from facenet_pytorch.models.inception_resnet_v1 import BasicConv2d



DEVICE = 'cuda:0' if torch.cuda.is_available() else 'cpu'

SAVE_MODEL = 'Securetl_Iris_Inception_model_50'
TRAIN_SET = '/content/SecureTL/IRIS_Inception_resnet/face_train_data.npy'

LEARN_RATE = 1e-4      # learning rate
REG = 0.001            # L2 regularization hyperparameter

N_EPOCHS = 50
BATCH_SIZE = 32
VALID_SPLIT = .2 
PATIENCE = 50

print('Training model: ' + SAVE_MODEL)

# Preparing and dividing the dataset
trainset = SecureFaceDataset(TRAIN_SET)

dataset_size = len(trainset)  # number of samples in training + validation sets
indices = list(range(dataset_size))
split = int(np.floor(VALID_SPLIT * dataset_size))  # number of samples in validation set
np.random.seed(42)
np.random.shuffle(indices)
train_indices, valid_indices = indices[split:], indices[:split]

train_sampler = torch.utils.data.sampler.SubsetRandomSampler(train_indices)
valid_sampler = torch.utils.data.sampler.SubsetRandomSampler(valid_indices)

train_loader = DataLoader(trainset, batch_size=BATCH_SIZE, shuffle=False, num_workers=4, sampler=train_sampler)
valid_loader = DataLoader(trainset, batch_size=BATCH_SIZE, shuffle=False, num_workers=4, sampler=valid_sampler)

# Creating the network and the model
pretrained = InceptionResnetV1(pretrained='vggface2')
pretrained.conv2d_1a = BasicConv2d(1, 32, kernel_size=3, stride=2)

network = SecureFaceNetwork(pretrained, dropout_prob=0.5).to(DEVICE)
#for Iris Inception/CNN
# network = SecureIrisNetwork(dropout_prob = 0.5).to(DEVICE)

#for Iris Vision Transformer
network.freeze_parameters()  # Freezing all parameters except the fully-connected layer(s)

model = SecureModel(network)
loss = SecureTripletLoss(margin=1.0)
optimizer = torch.optim.Adam(model.parameters(), lr=LEARN_RATE, weight_decay=REG)

# Training the model
train_hist, valid_hist = train_secure_triplet_model(model, loss, optimizer, train_loader, N_EPOCHS, BATCH_SIZE, DEVICE, patience=PATIENCE, valid_loader=valid_loader, filename=SAVE_MODEL )

