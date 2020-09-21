from __future__ import absolute_import
import sys

import torch
from torch import nn
import numpy as np

class TripletLoss(nn.Module):
    """Triplet loss with hard positive/negative mining.

    Reference:
    Hermans et al. In Defense of the Triplet Loss for Person Re-Identification. arXiv:1703.07737.

    Code imported from https://github.com/Cysu/open-reid/blob/master/reid/loss/triplet.py.

    Args:
        margin (float): margin for triplet.
    """
    def __init__(self,margin=0.3):
        super(TripletLoss, self).__init__()
        self.margin = margin
        self.ranking_loss = nn.MarginRankingLoss(margin=margin)

    def forward(self,inputs,targets):
        """
        Args:
            inputs: feature matrix with shape (batch_size, feat_dim)
            targets: ground truth labels with shape (num_classes)
        """
        n=inputs.size(0)
        dist=torch.pow(inputs,2).sum(dim=1,keepdim=True).expand(n,n)\
            +torch.pow(inputs,2).sum(dim=1,keepdim=True).expand(n,n).t()
        dist=dist.addmm_(1,-2,inputs,inputs.t())
        dist=dist.clamp(min=1e-12).sqrt()
        mask=targets.expand(n,n).eq(targets.expand(n,n).t())
        dist_ap=[]
        dist_an=[]
        for i in range(n):
            dist_ap.append(dist[i][mask[i]].max().unsqueeze(0))
            dist_an.append(dist[i][mask[i]==False].min().unsqueeze(0))
        dist_ap=torch.cat(dist_ap)
        dist_an=torch.cat(dist_an)
        # print(dist_an,dist_ap)
        # Compute ranking hinge loss
        y = torch.ones_like(dist_an)
        loss = self.ranking_loss(dist_an, dist_ap, y)
        return loss

class CrossEntropyLabelSmooth(nn.Module):
    """Cross entropy loss with label smoothing regularizer.

    Reference:
    Szegedy et al. Rethinking the Inception Architecture for Computer Vision. CVPR 2016.
    Equation: y = (1 - epsilon) * y + epsilon / K.

    Args:
        num_classes (int): number of classes.
        epsilon (float): weight.
    """
    def __init__(self, num_classes, epsilon=0.1, use_gpu=True):
        super(CrossEntropyLabelSmooth, self).__init__()
        self.num_classes = num_classes
        self.epsilon = epsilon
        self.use_gpu = use_gpu
        self.logsoftmax = nn.LogSoftmax(dim=1)

    def forward(self, inputs, targets):
        """
        Args:
            inputs: prediction matrix (before softmax) with shape (batch_size, num_classes)
            targets: ground truth labels with shape (num_classes)
        """
        log_probs = self.logsoftmax(inputs)
        targets = torch.zeros(log_probs.size()).scatter_(1, targets.unsqueeze(1).data.cpu(), 1)
        if self.use_gpu: targets = targets.cuda()
        targets = (1 - self.epsilon) * targets + self.epsilon / self.num_classes
        loss = (- targets * log_probs).mean(0).sum()
        return loss

if __name__=='__main__':
    target=[1,1,1,1,2,2,2,2,3,3,3,3,4,4,4,4]
    target=torch.Tensor(target)
    features=torch.Tensor(16,2048)
    lossf=TripletLoss()
    loss=lossf.forward(features,target)
    pass
