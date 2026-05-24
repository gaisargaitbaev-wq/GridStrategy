"""
Mean Reversion Channel (MRC) Indicator Implementation
Ported from TradingView Pine Script: https://github.com/farendzulkifli/MeanReversionChannel
"""
import numpy as np
from typing import Tuple


class SuperSmoother:
    """SuperSmoother MA filter for trend calculation"""
    
    @staticmethod
    def apply(data: np.ndarray, length: int) -> np.ndarray:
        """
        Apply SuperSmoother filter to data
        
        Args:
            data: Input price data
            length: Lookback period
            
        Returns:
            Smoothed array
        """
        pi = np.pi
        a1 = np.exp(-np.sqrt(2) * pi / length)
        b1 = 2 * a1 * np.cos(np.sqrt(2) * pi / length)
        c3 = -np.power(a1, 2)
        c2 = b1
        c1 = 1 - c2 - c3
        
        output = np.zeros_like(data, dtype=float)
        output[0] = data[0]
        
        if len(data) > 1:
            output[1] = (c1 * data[1] + c2 * data[0] + c3 * data[0])
        
        for i in range(2, len(data)):
            output[i] = (c1 * data[i] + c2 * output[i-1] + c3 * output[i-2])
        
        return output


class MRCIndicator:
    """Mean Reversion Channel Indicator"""
    
    def __init__(
        self,
        length: int = 200,
        inner_mult: float = 1.0,
        outer_mult: float = 2.415,
        filter_type: str = "SuperSmoother"
    ):
        """
        Initialize MRC Indicator
        
        Args:
            length: Lookback period (default 200)
            inner_mult: Inner channel multiplier (default 1.0)
            outer_mult: Outer channel multiplier (default 2.415)
            filter_type: Filter type ('SuperSmoother', 'EMA', 'SMA')
        """
        self.length = length
        self.inner_mult = inner_mult
        self.outer_mult = outer_mult
        self.filter_type = filter_type
        self.pi = np.pi
        self.mult = self.pi * inner_mult
        self.mult2 = self.pi * outer_mult
    
    def calculate(
        self,
        close: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        true_range: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Calculate MRC levels
        
        Args:
            close: Close prices
            high: High prices
            low: Low prices
            true_range: True Range values
            
        Returns:
            Tuple: (meanline, meanrange, upband1, loband1, upband2, loband2, condition)
        """
        # Calculate mean line based on filter type
        hlc3 = (high + low + close) / 3
        
        if self.filter_type == "SuperSmoother":
            meanline = SuperSmoother.apply(hlc3, self.length)
        elif self.filter_type == "EMA":
            meanline = self._ema(hlc3, self.length)
        else:  # SMA
            meanline = self._sma(hlc3, self.length)
        
        # Calculate mean range (ATR-like)
        meanrange = SuperSmoother.apply(true_range, self.length)
        
        # Calculate bands
        upband1 = meanline + (meanrange * self.mult)
        loband1 = meanline - (meanrange * self.mult)
        upband2 = meanline + (meanrange * self.mult2)
        loband2 = meanline - (meanrange * self.mult2)
        
        # Calculate condition (signal for trading)
        condition = self._calculate_condition(close, high, low, meanline, meanrange)
        
        return meanline, meanrange, upband1, loband1, upband2, loband2, condition
    
    @staticmethod
    def _sma(data: np.ndarray, length: int) -> np.ndarray:
        """Simple Moving Average"""
        output = np.zeros_like(data, dtype=float)
        for i in range(len(data)):
            if i < length:
                output[i] = np.mean(data[:i+1])
            else:
                output[i] = np.mean(data[i-length+1:i+1])
        return output
    
    @staticmethod
    def _ema(data: np.ndarray, length: int) -> np.ndarray:
        """Exponential Moving Average"""
        alpha = 2 / (length + 1)
        output = np.zeros_like(data, dtype=float)
        output[0] = data[0]
        for i in range(1, len(data)):
            output[i] = alpha * data[i] + (1 - alpha) * output[i-1]
        return output
    
    @staticmethod
    def _calculate_condition(
        close: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        meanline: np.ndarray,
        meanrange: np.ndarray
    ) -> np.ndarray:
        """
        Calculate MRC condition (-3 to 3)
        
        Signal meaning:
        -3: Oversold (Strong) - Below S2
        -2: Oversold - At S2
        -1: Oversold (Weak) - Between S1 and S2
        0: Price at Mean Line
        1: Overbought (Weak) - Between R1 and R2
        2: Overbought - At R2
        3: Overbought (Strong) - Above R2
        """
        gradsize = 0.5
        condition = np.zeros_like(close, dtype=int)
        
        for i in range(len(close)):
            upband2 = meanline[i] + (meanrange[i] * 2.415 * np.pi)
            loband2 = meanline[i] - (meanrange[i] * 2.415 * np.pi)
            
            if close[i] > meanline[i]:
                upband2_1 = upband2 + (meanrange[i] * gradsize * 4)
                upband2_9 = upband2 + (meanrange[i] * gradsize * -4)
                
                if high[i] >= upband2_9 and high[i] < upband2:
                    condition[i] = 1
                elif high[i] >= upband2 and high[i] < upband2_1:
                    condition[i] = 2
                elif high[i] >= upband2_1:
                    condition[i] = 3
                elif close[i] <= meanline[i] + meanrange[i]:
                    condition[i] = 4
                else:
                    condition[i] = 5
            
            elif close[i] < meanline[i]:
                loband2_1 = loband2 - (meanrange[i] * gradsize * 4)
                loband2_9 = loband2 - (meanrange[i] * gradsize * -4)
                
                if low[i] <= loband2_9 and low[i] > loband2:
                    condition[i] = -1
                elif low[i] <= loband2 and low[i] > loband2_1:
                    condition[i] = -2
                elif low[i] <= loband2_1:
                    condition[i] = -3
                elif close[i] >= meanline[i] - meanrange[i]:
                    condition[i] = -4
                else:
                    condition[i] = -5
        
        return condition
