"""
PyTorch Neural Network Architecture for Cadastral Boundary Segmentation.
Implements a lightweight U-Net with DoubleConv blocks, Residual skip paths,
and 1-channel Sigmoid output for binary boundary probability mapping.
Designed for memory-efficient training and high-throughput ONNX Runtime inference.
"""

from typing import List, Optional, Any

try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    class nn:
        class Module:
            pass


if TORCH_AVAILABLE:
    class DoubleConv(nn.Module):
        """(Conv -> BatchNorm -> ReLU) * 2 with residual option"""
        def __init__(self, in_channels: int, out_channels: int, mid_channels: Optional[int] = None):
            super().__init__()
            if not mid_channels:
                mid_channels = out_channels
            self.double_conv = nn.Sequential(
                nn.Conv2d(in_channels, mid_channels, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(mid_channels),
                nn.ReLU(inplace=True),
                nn.Conv2d(mid_channels, out_channels, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True)
            )
            self.residual = None
            if in_channels != out_channels:
                self.residual = nn.Sequential(
                    nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
                    nn.BatchNorm2d(out_channels)
                )

        def forward(self, x: Any) -> Any:
            res = x if self.residual is None else self.residual(x)
            return self.double_conv(x) + res


    class DownBlock(nn.Module):
        """Downscaling with maxpool then DoubleConv"""
        def __init__(self, in_channels: int, out_channels: int):
            super().__init__()
            self.maxpool_conv = nn.Sequential(
                nn.MaxPool2d(2),
                DoubleConv(in_channels, out_channels)
            )

        def forward(self, x: Any) -> Any:
            return self.maxpool_conv(x)


    class UpBlock(nn.Module):
        """Upscaling then DoubleConv"""
        def __init__(self, in_channels: int, out_channels: int, bilinear: bool = True):
            super().__init__()
            if bilinear:
                self.up = nn.Upsample(scale_factor=2, mode="bilinear", align_corners=True)
                self.conv = DoubleConv(in_channels, out_channels, in_channels // 2)
            else:
                self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
                self.conv = DoubleConv(in_channels, out_channels)

        def forward(self, x1: Any, x2: Any) -> Any:
            x1 = self.up(x1)
            diff_y = x2.size()[2] - x1.size()[2]
            diff_x = x2.size()[3] - x1.size()[3]

            x1 = nn.functional.pad(x1, [diff_x // 2, diff_x - diff_x // 2,
                                        diff_y // 2, diff_y - diff_y // 2])
            x = torch.cat([x2, x1], dim=1)
            return self.conv(x)


    class CadastralBoundaryUNet(nn.Module):
        """
        Lightweight U-Net architecture for aerial cadastral boundary extraction.
        
        Args:
            in_channels: 3 for RGB aerial images
            num_classes: 1 for binary cadastral boundary probability
            base_channels: Base channel multiplier (default: 32)
            bilinear: True for bilinear upsampling (reduces parameters)
        """
        def __init__(
            self,
            in_channels: int = 3,
            num_classes: int = 1,
            base_channels: int = 32,
            bilinear: bool = True
        ):
            super().__init__()
            self.in_channels = in_channels
            self.num_classes = num_classes
            self.bilinear = bilinear

            c = base_channels
            self.inc = DoubleConv(in_channels, c)
            self.down1 = DownBlock(c, c * 2)
            self.down2 = DownBlock(c * 2, c * 4)
            self.down3 = DownBlock(c * 4, c * 8)
            factor = 2 if bilinear else 1
            self.down4 = DownBlock(c * 8, c * 16 // factor)

            self.up1 = UpBlock(c * 16, c * 8 // factor, bilinear)
            self.up2 = UpBlock(c * 8, c * 4 // factor, bilinear)
            self.up3 = UpBlock(c * 4, c * 2 // factor, bilinear)
            self.up4 = UpBlock(c * 2, c, bilinear)
            self.outc = nn.Conv2d(c, num_classes, kernel_size=1)
            self.sigmoid = nn.Sigmoid()

        def forward(self, x: Any) -> Any:
            x1 = self.inc(x)
            x2 = self.down1(x1)
            x3 = self.down2(x2)
            x4 = self.down3(x3)
            x5 = self.down4(x4)

            x = self.up1(x5, x4)
            x = self.up2(x, x3)
            x = self.up3(x, x2)
            x = self.up4(x, x1)
            logits = self.outc(x)
            probs = self.sigmoid(logits)
            return probs

else:
    class CadastralBoundaryUNet:
        """Dummy fallback definition when PyTorch is not loaded locally."""
        def __init__(self, *args, **kwargs):
            pass
