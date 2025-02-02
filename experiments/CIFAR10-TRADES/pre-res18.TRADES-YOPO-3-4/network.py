import config
import torch
import torch.nn as nn
import torch.nn.functional as F
# from base_model.preact_resnet import PreActResNet18

class PreActBlock(nn.Module):
    '''Pre-activation version of the BasicBlock.'''
    expansion = 1

    def __init__(self, in_planes, planes, stride=1):
        super(PreActBlock, self).__init__()
        self.bn1 = nn.BatchNorm2d(in_planes)
        self.conv1 = nn.Conv2d(in_planes, planes, kernel_size=3, stride=stride, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(planes)
        self.conv2 = nn.Conv2d(planes, planes, kernel_size=3, stride=1, padding=1, bias=False)

        if stride != 1 or in_planes != self.expansion * planes:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_planes, self.expansion * planes, kernel_size=1, stride=stride, bias=False)
            )

    def forward(self, x):
        out = F.relu(self.bn1(x))
        shortcut = self.shortcut(out) if hasattr(self, 'shortcut') else x
        out = self.conv1(out)
        out = self.conv2(F.relu(self.bn2(out)))
        out += shortcut
        return out



def PreActResNet18():
    return PreActResNet(PreActBlock, [2, 2, 2, 2])

class PreActResNet(nn.Module):

    def __init__(self, block, num_blocks, num_classes=10):
        super(PreActResNet, self).__init__()
        self.in_planes = 64

        self.other_layers = nn.ModuleList()

        self.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)

        self.layer_one = self.conv1


        self.other_layer1 = self._make_layer(block, 64, num_blocks[0], stride=1)
        self.other_layer2 = self._make_layer(block, 128, num_blocks[1], stride=2)
        self.other_layer3 = self._make_layer(block, 256, num_blocks[2], stride=2)
        self.other_layer4 = self._make_layer(block, 512, num_blocks[3], stride=2)

        self.linear = GlobalpoolFC(512 * block.expansion, num_classes)
        self.other_layers.append(self.linear)

    def _make_layer(self, block, planes, num_blocks, stride):
        strides = [stride] + [1] * (num_blocks - 1)
        layers = []
        for stride in strides:
            layers.append(block(self.in_planes, planes, stride))
            self.other_layers.append(layers[-1])

            self.in_planes = planes * block.expansion
        return nn.Sequential(*layers)

    def forward(self, x):

        x = self.layer_one(x)
        self.layer_one_out = x
        self.layer_one_out.requires_grad_()
        self.layer_one_out.retain_grad()
        x = self.layer_one_out

        for layer in self.other_layers:
            x = layer(x)


        '''
        out = self.conv1(x)
        out = self.layer1(out)
        out = self.layer2(out)
        out = self.layer3(out)
        out = self.layer4(out)
        out = F.avg_pool2d(out, 4)
        out = out.view(out.size(0), -1)
        out = self.linear(out)
        return out
        '''
        return x


class GlobalpoolFC(nn.Module):

    def __init__(self, num_in, num_class):
        super(GlobalpoolFC, self).__init__()
        self.pool = nn.AdaptiveAvgPool2d(output_size=1)
        self.fc = nn.Linear(num_in, num_class)

    def forward(self, x):
        y = self.pool(x)
        y = y.reshape(y.shape[0], -1)
        y = self.fc(y)
        return y



def create_network():
    return PreActResNet18()


def test():
    net = create_network()
    y = net((torch.randn(1, 3, 32, 32)))
    print(y.size())
