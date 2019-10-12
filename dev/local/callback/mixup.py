#AUTOGENERATED! DO NOT EDIT! File to edit: dev/19_callback_mixup.ipynb (unless otherwise specified).

__all__ = ['reduce_loss', 'MixUp']

#Cell
from ..torch_basics import *
from ..test import *
from ..layers import *
from ..data.all import *
from ..optimizer import *
from ..learner import *
from .progress import *
from ..vision.core import *

from torch.distributions.beta import Beta

#Cell
def reduce_loss(loss, reduction='mean'):
    return loss.mean() if reduction=='mean' else loss.sum() if reduction=='sum' else loss

#Cell
class MixUp(Callback):
    run_after=[Normalize, Cuda]
    def __init__(self, alpha=0.4): self.distrib = Beta(tensor(alpha), tensor(alpha))
    def begin_fit(self): self.old_lf,self.learn.loss_func = self.learn.loss_func,self.lf
    def after_fit(self): self.learn.loss_func = self.old_lf

    def begin_batch(self):
        if not self.training: return
        lam = self.distrib.sample((self.y.size(0),)).squeeze().to(self.x.device)
        lam = torch.stack([lam, 1-lam], 1)
        self.lam = unsqueeze(lam.max(1)[0], n=3)
        shuffle = torch.randperm(self.y.size(0)).to(self.x.device)
        xb1,self.yb1 = tuple(L(self.xb).itemgot(shuffle)),tuple(L(self.yb).itemgot(shuffle))
        self.learn.xb = tuple(L(xb1,self.xb).map_zip(torch.lerp,weight=self.lam))

    def lf(self, pred, *yb):
        if not self.in_train: return self.old_lf(pred, *yb)
        with NoneReduce(self.old_lf) as lf:
            loss = torch.lerp(lf(pred,*self.yb1), lf(pred,*yb), self.lam)
        return reduce_loss(loss, getattr(self.old_lf, 'reduction', 'mean'))