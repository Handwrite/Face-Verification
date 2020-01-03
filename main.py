# Python Libraries
import os
import numpy as np
import logging
import time 
import random

# My Libraries
from src.loadConfig import loadConfig
from src.dataset import FaceDataset
from src.load_imglist import ImageList
from src.utils import model_save

def train_svm(X_train, Y_train, X_test, Y_test):
    # Cheat with sklearn svm
    from sklearn.svm import SVC
    from sklearn.metrics import classification_report, confusion_matrix
    
    svclassifier = SVC(kernel='linear')
    svclassifier.fit(X_train, Y_train)
    Y_pred = svclassifier.predict(X_test)
    
    logger.info(confusion_matrix(Y_test, Y_pred))
    logger.info(classification_report(Y_test, Y_pred))

def train_eigenFaces(X_train, Y_train, X_test, Y_test, X):
    # Cheat with sklearn pca
    from sklearn.decomposition import PCA
    from sklearn.svm import SVC
    from sklearn.metrics import classification_report, confusion_matrix
    
    pca = PCA(n_components=5)
    pca.fit(X)
    
    X_train1 = pca.transform(X_train[:, :10000])
    X_train2 = pca.transform(X_train[:, 10000:])
    distance = (X_train1 - X_train2)**2/(X_train1 + X_train2)
    
    svclassifier = SVC(kernel='linear')
    svclassifier.fit(distance, Y_train)
    
    X_test1 = pca.transform(X_test[:, :10000])
    X_test2 = pca.transform(X_test[:, 10000:])
    distance_test = (X_test1 - X_test2)**2/(X_test1 + X_test2)
    Y_pred = svclassifier.predict(distance_test)
    
    print(confusion_matrix(Y_test, Y_pred))
    print(classification_report(Y_test, Y_pred))
  
def train_nn(src_dir):
    # Cheat with pytorch nn
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    import torch.optim as optim
    from torch.utils.data import Dataset
    from torch.utils.data import DataLoader
    from sklearn.metrics import classification_report
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    fh = logging.FileHandler('log.txt', 'w')
    fh.setLevel(logging.INFO)
    sh = logging.StreamHandler()
    sh.setLevel(logging.INFO)
    logger.addHandler(fh)
    logger.addHandler(sh)

    class Net(nn.Module):
        def __init__(self):
            super(Net, self).__init__()
            self.conv1 = nn.Conv2d(1, 64, 3, padding=1)
            self.conv2 = nn.Conv2d(64, 64, 3, padding=1)
            self.pool = nn.MaxPool2d(2, 2)
            
            self.conv3 = nn.Conv2d(64, 128, 3, padding=1)
            self.conv4 = nn.Conv2d(128, 128, 3, padding=1)
            
            self.conv5 = nn.Conv2d(128, 256, 3, padding=1)
            self.conv6 = nn.Conv2d(256, 256, 3, padding=1)
            
            self.conv7 = nn.Conv2d(256, 512, 3, padding=1)
            self.conv8 = nn.Conv2d(512, 512, 3, padding=1)
            self.conv9 = nn.Conv2d(512, 512, 3, padding=1)

            self.fc1 = nn.Linear(6**2 * 512, 4096)
            self.fc2 = nn.Linear(4096, 2)
    
        def forward(self, x):
            x = F.relu(self.conv1(x))
            x = self.pool(F.relu(self.conv2(x)))
            
            x = F.relu(self.conv3(x))
            x = self.pool(F.relu(self.conv4(x)))
            
            x = F.relu(self.conv5(x))
            x = self.pool(F.relu(self.conv6(x)))

            x = F.relu(self.conv7(x))
            x = F.relu(self.conv8(x))
            x = self.pool(self.conv9(x))
            
            x = x.view(-1, 6**2 * 512)
            x = F.relu(self.fc1(x))
            x = F.relu(self.fc2(x))
            return x

    conf = loadConfig("config.json")
    L = nn.CrossEntropyLoss()
    
    train_data = ImageList(src_dir=src_dir)
    train_loader = DataLoader(train_data, batch_size=8, shuffle=True)
    
    device = torch.device("cuda")
    model = Net()
    model = model.to(device)
    optimizer = optim.Adam(params = model.parameters(), lr = 1e-4)

    # Start training
    for epoch in range(2):
        logger.info("epoch: {} ".format(epoch))
        loss = 0

        for i, data in enumerate(train_loader):
            optimizer.zero_grad()
            
            img = data["image"].to(device)
            label = data["label"].to(device)
            
            outputs = model(img)

            loss = L(outputs, label)
            loss.backward()
            optimizer.step()

            if (i % 500 == 0):
                logger.info("loss: {}".format(loss.item()))

        if epoch % conf.save_interval == 0:
            model_save(model, epoch, logger)
        

src_dir = r"F:\DataSets\webface"
train_nn(src_dir)
