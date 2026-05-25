"""
Grid Trading Engine
Manages grid strategy execution with safety orders
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime
import numpy as np
from backtester.order_manager import Order, OrderSide, OrderType, OrderStatus, OrderManager, Trade


@dataclass
class GridConfig:
    """Grid configuration"""
    take_profit_percent: float  # Take profit % on market order
    num_safety_orders: int      # Number of limit orders
    safety_order_step: float    # Distance between orders in %
    martingale: float           # Martingale multiplier (1.0 = no increase)
    dynamic_step: float         # Dynamic step to increase grid span in %
    trading_deposit: float      # Trading deposit
    first_order_price: float    # Price of first order
    leverage: float             # Leverage multiplier
    direction: str              # "long", "short", or "both"
    commission_percent: float = 0.1  # Trading commission
    maintenance_margin_percent: float = 0.005  # Maintenance margin for isolated margin (fraction)


class GridPosition:
    """Manages a single grid position"""
    
    def __init__(
        self,
        position_id: str,
        config: GridConfig,
        entry_price: float,
        side: OrderSide,
        order_manager: OrderManager,
        timestamp: datetime
    ):
        """
        Initialize GridPosition
        
        Args:
            position_id: Unique position ID
            config: Grid configuration
            entry_price: Entry price for market order
            side: BUY or SELL
            order_manager: Order manager instance
            timestamp: Position open time
        """
        self.position_id = position_id
        self.config = config
        self.entry_price = entry_price
        self.side = side
        self.order_manager = order_manager
        self.timestamp = timestamp
        
        # Calculate position size
        self.position_size = self._calculate_position_size()
        
        # Orders
        self.market_order: Optional[Order] = None
        self.safety_orders: List[Order] = []
        self.closed_safety_orders: List[Order] = []
        
        # Track PnL
        self.entry_price_filled = 0.0
        self.is_closed = False
        self.close_reason = ""
    
    def _calculate_position_size(self) -> float:
        """Calculate position size based on deposit and leverage"""
        position_value = self.config.trading_deposit * self.config.leverage
        return position_value / self.entry_price
    
    def open_market_order(self, timestamp: datetime) -> Order:
        """Open market order"""
        self.market_order = self.order_manager.create_order(
            timestamp=timestamp,
            side=self.side,
            order_type=OrderType.MARKET,
            price=self.entry_price,
            quantity=self.position_size,
            order_id=f"MARKET_{self.position_id}"
        )
        
        # Fill immediately (market order)
        self.order_manager.fill_order(self.market_order, self.entry_price, self.position_size)
        self.entry_price_filled = self.entry_price
        
        return self.market_order
    
    def open_safety_orders(self, timestamp: datetime) -> List[Order]:
        """Create safety orders (grid of limit orders)"""
        self.safety_orders = []
        
        for i in range(self.config.num_safety_orders):
            # Calculate distance from market order
            # Distance increases with dynamic_step
            step_distance = self.config.safety_order_step + (i * self.config.dynamic_step)
            
            if self.side == OrderSide.BUY:
                # For BUY: safety orders placed BELOW entry price
                order_price = self.entry_price * (1 - step_distance / 100)
            else:  # SELL
                # For SELL: safety orders placed ABOVE entry price
                order_price = self.entry_price * (1 + step_distance / 100)
            
            # Calculate quantity with martingale
            if self.config.martingale > 1.0:
                # Quantity increases geometrically
                order_quantity = self.position_size * (self.config.martingale ** i)
            else:
                # Fixed quantity
                order_quantity = self.position_size
            
            order = self.order_manager.create_order(
                timestamp=timestamp,
                side=self.side,
                order_type=OrderType.LIMIT,
                price=order_price,
                quantity=order_quantity,
                order_id=f"SAFETY_{self.position_id}_{i+1}"
            )
            
            self.safety_orders.append(order)
        
        return self.safety_orders
    
    def check_safety_order_fills(
        self,
        timestamp: datetime,
        high: float,
        low: float,
        current_price: float
    ) -> List[Order]:
        """Check if any safety orders are filled"""
        filled_orders = []
        
        for order in self.safety_orders:
            if order.status != OrderStatus.PENDING:
                continue
            
            # Check if price touched this level
            if self.side == OrderSide.BUY:
                # BUY limit orders trigger on low price
                if low <= order.price:
                    self.order_manager.fill_order(order, order.price, order.quantity)
                    filled_orders.append(order)
            else:  # SELL
                # SELL limit orders trigger on high price
                if high >= order.price:
                    self.order_manager.fill_order(order, order.price, order.quantity)
                    filled_orders.append(order)
        
        return filled_orders
    
    def check_take_profit(self, current_price: float) -> bool:
        """Check if take-profit is hit"""
        if not self.market_order or self.market_order.status != OrderStatus.FILLED:
            return False
        
        tp_price = self._calculate_tp_price()
        
        if self.side == OrderSide.BUY:
            return current_price >= tp_price
        else:  # SELL
            return current_price <= tp_price
    
    def _calculate_tp_price(self) -> float:
        """Calculate take-profit price"""
        tp_percent = self.config.take_profit_percent
        
        if self.side == OrderSide.BUY:
            return self.entry_price * (1 + tp_percent / 100)
        else:  # SELL
            return self.entry_price * (1 - tp_percent / 100)

    def check_liquidation(self, high: float, low: float, current_price: float) -> tuple:
        """Check if the position should be liquidated under isolated margin simplified model.

        Returns (liquidated: bool, liquidation_price: float).
        Simplified formula:
          liq_price_long  = entry_price * (1 - (1 - maintenance_margin)/leverage)
          liq_price_short = entry_price * (1 + (1 - maintenance_margin)/leverage)
        Liquidation triggers when price touches that level (low <= liq for long, high >= liq for short).
        """
        if not self.market_order or self.market_order.status != OrderStatus.FILLED:
            return False, 0.0

        entry = self.entry_price_filled if self.entry_price_filled else self.entry_price
        mm = getattr(self.config, 'maintenance_margin_percent', 0.005)
        L = self.config.leverage if self.config.leverage != 0 else 1.0

        offset = (1.0 - mm) / L
        if self.side == OrderSide.BUY:
            liq_price = entry * (1.0 - offset)
            if low <= liq_price:
                return True, liq_price
        else:
            liq_price = entry * (1.0 + offset)
            if high >= liq_price:
                return True, liq_price

        return False, liq_price
    
    def close_position(
        self,
        timestamp: datetime,
        close_price: float,
        reason: str = "take_profit"
    ) -> Tuple[float, float]:
        """
        Close position and calculate PnL
        
        Returns:
            (total_pnl, pnl_percent)
        """
        self.is_closed = True
        self.close_reason = reason
        
        total_pnl = 0.0
        total_cost = 0.0
        total_quantity = 0.0
        
        # Close market order
        if self.market_order and self.market_order.status == OrderStatus.FILLED:
            self.order_manager.close_order(
                self.market_order,
                close_price,
                self.market_order.filled_quantity
            )
            total_pnl += self.market_order.pnl
            total_cost += self.market_order.filled_price * self.market_order.filled_quantity
            total_quantity += self.market_order.filled_quantity
        
        # Close filled safety orders
        for order in self.safety_orders:
            if order.status == OrderStatus.FILLED:
                self.order_manager.close_order(
                    order,
                    close_price,
                    order.filled_quantity
                )
                total_pnl += order.pnl
                total_cost += order.filled_price * order.filled_quantity
                total_quantity += order.filled_quantity
                self.closed_safety_orders.append(order)
        
        # Cancel unfilled safety orders
        for order in self.safety_orders:
            if order.status == OrderStatus.PENDING:
                self.order_manager.cancel_order(order)
        
        # Calculate overall PnL percentage
        pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0
        
        # Record the closed position as a single trade
        if self.market_order and self.market_order.status == OrderStatus.CLOSED:
            exit_order = Order(
                order_id=f"EXIT_{self.position_id}",
                timestamp=timestamp,
                side=self.side,
                order_type=OrderType.MARKET,
                price=close_price,
                quantity=total_quantity,
                filled_price=close_price,
                filled_quantity=total_quantity,
                status=OrderStatus.FILLED,
                commission=0.0,
                pnl=0.0
            )
            trade = Trade(
                trade_id=f"TRADE_{self.position_id}",
                entry_order=self.market_order,
                exit_order=exit_order,
                entry_time=self.market_order.timestamp,
                exit_time=timestamp,
                entry_price=self.market_order.filled_price,
                exit_price=close_price,
                quantity=total_quantity,
                side=self.market_order.side,
                pnl=total_pnl,
                pnl_percent=pnl_percent,
                is_tp_close=(reason == "take_profit"),
                close_reason=reason
            )
            self.order_manager.trades.append(trade)
        
        return total_pnl, pnl_percent
    
    def get_total_quantity(self) -> float:
        """Get total filled quantity (market + safety orders)"""
        total = 0.0
        
        if self.market_order and self.market_order.status == OrderStatus.FILLED:
            total += self.market_order.filled_quantity
        
        for order in self.safety_orders:
            if order.status == OrderStatus.FILLED:
                total += order.filled_quantity
        
        return total
    
    def get_average_entry_price(self) -> float:
        """Get weighted average entry price"""
        total_cost = 0.0
        total_quantity = 0.0
        
        if self.market_order and self.market_order.status == OrderStatus.FILLED:
            total_cost += self.market_order.filled_price * self.market_order.filled_quantity
            total_quantity += self.market_order.filled_quantity
        
        for order in self.safety_orders:
            if order.status == OrderStatus.FILLED:
                total_cost += order.filled_price * order.filled_quantity
                total_quantity += order.filled_quantity
        
        return total_cost / total_quantity if total_quantity > 0 else 0.0


class GridEngine:
    """Grid trading engine"""
    
    def __init__(self, config: GridConfig):
        """Initialize GridEngine"""
        self.config = config
        self.order_manager = OrderManager(config.commission_percent)
        self.positions: List[GridPosition] = []
        self.position_counter = 0
    
    def open_position(
        self,
        timestamp: datetime,
        entry_price: float,
        signal_side: OrderSide
    ) -> GridPosition:
        """
        Open a new grid position
        
        Args:
            timestamp: Current timestamp
            entry_price: Entry price
            signal_side: BUY or SELL signal
            
        Returns:
            GridPosition instance
        """
        self.position_counter += 1
        position_id = f"POS_{self.position_counter}"
        
        position = GridPosition(
            position_id=position_id,
            config=self.config,
            entry_price=entry_price,
            side=signal_side,
            order_manager=self.order_manager,
            timestamp=timestamp
        )
        
        # Open market order
        position.open_market_order(timestamp)
        
        # Open safety orders
        position.open_safety_orders(timestamp)
        
        self.positions.append(position)
        
        return position
    
    def get_active_positions(self) -> List[GridPosition]:
        """Get all active (non-closed) positions"""
        return [p for p in self.positions if not p.is_closed]
    
    def get_statistics(self) -> dict:
        """Get trading statistics"""
        return self.order_manager.get_statistics()
