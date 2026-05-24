"""
Main Backtester for Grid Strategy
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from pathlib import Path

from backtester.mrc_indicator import MRCIndicator
from backtester.grid_engine import GridEngine, GridConfig
from backtester.order_manager import OrderSide


class BacktestRunner:
    """Main backtesting engine"""
    
    def __init__(self, config_path: str):
        """
        Initialize BacktestRunner
        
        Args:
            config_path: Path to configuration JSON file
        """
        with open(config_path, 'r') as f:
            config_dict = json.load(f)
        
        self.config_dict = config_dict
        self.grid_config = GridConfig(
            take_profit_percent=config_dict['take_profit_percent'],
            num_safety_orders=config_dict['num_safety_orders'],
            safety_order_step=config_dict['safety_order_step'],
            martingale=config_dict.get('martingale', 1.0),
            dynamic_step=config_dict.get('dynamic_step', 0.0),
            trading_deposit=config_dict['trading_deposit'],
            first_order_price=config_dict['first_order_price'],
            leverage=config_dict.get('leverage', 1.0),
            direction=config_dict.get('direction', 'long'),
            commission_percent=config_dict.get('commission_percent', 0.1)
        )
        
        # Indicator config
        self.indicator_config = config_dict.get('indicator_config', {})
        
        # Initialize indicator
        self.indicator = MRCIndicator(
            length=self.indicator_config.get('length', 200),
            inner_mult=self.indicator_config.get('inner_mult', 1.0),
            outer_mult=self.indicator_config.get('outer_mult', 2.415),
            filter_type=self.indicator_config.get('filter_type', 'SuperSmoother')
        )
        
        # Initialize grid engine
        self.grid_engine = GridEngine(self.grid_config)
        
        # Data
        self.df: Optional[pd.DataFrame] = None
        self.results: Dict = {}
    
    def load_data(self, csv_path: str) -> pd.DataFrame:
        """
        Load OHLCV data from CSV
        
        Expected columns: timestamp, open, high, low, close, volume
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            DataFrame with OHLCV data
        """
        self.df = pd.read_csv(csv_path)
        
        # Convert timestamp to datetime
        if 'timestamp' in self.df.columns:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        elif 'Date' in self.df.columns:
            self.df['timestamp'] = pd.to_datetime(self.df['Date'])
            self.df = self.df.drop('Date', axis=1)
        
        # Ensure required columns exist
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in self.df.columns:
                raise ValueError(f"Missing required column: {col}")
        
        # Calculate true range
        self.df['tr'] = self._calculate_true_range(
            self.df['high'].values,
            self.df['low'].values,
            self.df['close'].values
        )
        
        print(f"Data loaded: {len(self.df)} candles")
        print(f"Date range: {self.df['timestamp'].min()} to {self.df['timestamp'].max()}")
        
        return self.df
    
    @staticmethod
    def _calculate_true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """Calculate True Range"""
        tr = np.zeros_like(high, dtype=float)
        tr[0] = high[0] - low[0]
        
        for i in range(1, len(high)):
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
        
        return tr
    
    def run_backtest(self) -> Dict:
        """
        Run the backtest
        
        Returns:
            Results dictionary
        """
        if self.df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        print("\n" + "="*60)
        print("STARTING BACKTEST")
        print("="*60)
        
        # Calculate MRC indicator
        print("\nCalculating MRC indicator...")
        meanline, meanrange, upband1, loband1, upband2, loband2, condition = self.indicator.calculate(
            close=self.df['close'].values,
            high=self.df['high'].values,
            low=self.df['low'].values,
            true_range=self.df['tr'].values
        )
        
        self.df['meanline'] = meanline
        self.df['meanrange'] = meanrange
        self.df['r1'] = upband1
        self.df['s1'] = loband1
        self.df['r2'] = upband2
        self.df['s2'] = loband2
        self.df['condition'] = condition
        
        print("✓ Indicator calculated")
        
        # Run simulation
        print("Running simulation...")
        self._simulate_trading()
        
        # Generate results
        self.results = self._generate_results()
        
        print("\n" + "="*60)
        print("BACKTEST COMPLETED")
        print("="*60)
        
        return self.results
    
    def _simulate_trading(self) -> None:
        """Simulate trading based on signals"""
        active_position = None
        last_signal = None
        
        for idx in range(len(self.df)):
            row = self.df.iloc[idx]
            timestamp = row['timestamp']
            
            # Get price levels
            close = row['close']
            high = row['high']
            low = row['low']
            condition = row['condition']
            
            # === POSITION OPEN ===
            if active_position is None:
                signal_side = self._get_entry_signal(condition)
                
                if signal_side is not None and signal_side != last_signal:
                    # Open new position at S2 or R2
                    print(f"[{timestamp}] OPEN {signal_side.value.upper()} at {close:.8f}")
                    
                    active_position = self.grid_engine.open_position(
                        timestamp=timestamp,
                        entry_price=close,
                        signal_side=signal_side
                    )
                    
                    last_signal = signal_side
            
            # === POSITION MANAGEMENT ===
            else:
                # Check safety order fills
                filled = active_position.check_safety_order_fills(timestamp, high, low, close)
                if filled:
                    for order in filled:
                        print(f"[{timestamp}] SAFETY ORDER FILLED: {order.order_id} at {order.price:.8f}")
                
                # Check take-profit
                if active_position.check_take_profit(close):
                    print(f"[{timestamp}] TAKE-PROFIT HIT at {close:.8f}")
                    
                    pnl, pnl_percent = active_position.close_position(
                        timestamp=timestamp,
                        close_price=close,
                        reason="take_profit"
                    )
                    
                    print(f"  → PnL: {pnl:.8f} ({pnl_percent:.2f}%)")
                    
                    active_position = None
                    last_signal = None
    
    def _get_entry_signal(self, condition: int) -> Optional[OrderSide]:
        """
        Get entry signal from MRC condition
        
        condition > 0: Overbought (SELL signal)
        condition < 0: Oversold (BUY signal)
        """
        direction = self.grid_config.direction
        
        # BUY signal when price is oversold (crosses below S2)
        if condition == -2 or condition == -3:
            if direction in ['long', 'both']:
                return OrderSide.BUY
        
        # SELL signal when price is overbought (crosses above R2)
        if condition == 2 or condition == 3:
            if direction in ['short', 'both']:
                return OrderSide.SELL
        
        return None
    
    def _generate_results(self) -> Dict:
        """Generate backtest results"""
        stats = self.grid_engine.get_statistics()
        
        results = {
            'config': self.config_dict,
            'statistics': stats,
            'trades': [
                {
                    'trade_id': t.trade_id,
                    'entry_time': t.entry_time.isoformat(),
                    'exit_time': t.exit_time.isoformat(),
                    'duration_minutes': t.duration(),
                    'entry_price': t.entry_price,
                    'exit_price': t.exit_price,
                    'quantity': t.quantity,
                    'side': t.side.value,
                    'pnl': t.pnl,
                    'pnl_percent': t.pnl_percent,
                    'is_tp_close': t.is_tp_close
                }
                for t in self.grid_engine.order_manager.trades
            ]
        }
        
        return results
    
    def save_results(self, output_path: str) -> None:
        """Save backtest results to JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert non-serializable objects
        results_copy = json.loads(json.dumps(self.results, default=str))
        
        with open(output_file, 'w') as f:
            json.dump(results_copy, f, indent=2)
        
        print(f"\nResults saved to: {output_path}")
    
    def save_data_with_indicators(self, output_path: str) -> None:
        """Save data with calculated indicators"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.df.to_csv(output_file, index=False)
        print(f"\nData with indicators saved to: {output_path}")
    
    def print_summary(self) -> None:
        """Print summary statistics"""
        if not self.results:
            print("No results available. Run backtest first.")
            return
        
        stats = self.results['statistics']
        
        print("\n" + "="*60)
        print("SUMMARY STATISTICS")
        print("="*60)
        print(f"Total Trades:       {stats['total_trades']}")
        print(f"Winning Trades:     {stats['winning_trades']}")
        print(f"Losing Trades:      {stats['losing_trades']}")
        print(f"Win Rate:           {stats['win_rate']:.2f}%")
        print(f"Total PnL:          {stats['total_pnl']:.8f}")
        print(f"Average PnL:        {stats['avg_pnl']:.8f}")
        print(f"Average PnL %:      {stats['avg_pnl_percent']:.2f}%")
        print(f"Max PnL:            {stats['max_pnl']:.8f}")
        print(f"Min PnL:            {stats['min_pnl']:.8f}")
        print("="*60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python backtest_runner.py <config_path> [data_path]")
        sys.exit(1)
    
    config_path = sys.argv[1]
    data_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Initialize backtester
    backtester = BacktestRunner(config_path)
    
    # Load data
    if data_path:
        backtester.load_data(data_path)
    else:
        print("Error: Data path required")
        sys.exit(1)
    
    # Run backtest
    results = backtester.run_backtest()
    
    # Save results
    backtester.save_results("results/backtest_results.json")
    backtester.save_data_with_indicators("results/data_with_indicators.csv")
    
    # Print summary
    backtester.print_summary()
