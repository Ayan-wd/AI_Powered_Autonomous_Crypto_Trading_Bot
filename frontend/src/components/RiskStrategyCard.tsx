import React from 'react';
import type { RiskStatusResponse, StrategyDecisionResponse } from '../services/api';
import { ShieldCheck, ShieldAlert, Cpu, Crosshair, RefreshCw, Zap } from 'lucide-react';

interface RiskStrategyCardProps {
  riskStatus: RiskStatusResponse | null;
  strategyDecision: StrategyDecisionResponse | null;
  onEvaluateStrategy: () => void;
  loading: boolean;
}

export const RiskStrategyCard: React.FC<RiskStrategyCardProps> = ({
  riskStatus,
  strategyDecision,
  onEvaluateStrategy,
  loading,
}) => {
  const isPermitted = riskStatus?.trading_permitted ?? true;
  const circuitBreaker = riskStatus?.circuit_breaker_active ?? false;
  const action = strategyDecision?.action ?? 'HOLD / NO TRADE';

  const getActionBadge = (act: string) => {
    switch (act) {
      case 'BUY':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'SELL':
        return 'bg-rose-500/10 text-rose-400 border-rose-500/30';
      default:
        return 'bg-zinc-900 text-zinc-300 border-zinc-700';
    }
  };

  return (
    <div className="bg-[#09090b] border border-zinc-800 rounded-xl p-5 flex flex-col justify-between shadow-xl">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between border-b border-zinc-800 pb-3 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-black rounded-lg text-white border border-zinc-800">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-white">Risk & Strategy Gatekeeper</h3>
              <p className="text-xs text-zinc-400 font-mono">Position Sizing & Drawdown Protection</p>
            </div>
          </div>

          <button
            onClick={onEvaluateStrategy}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-mono font-medium rounded-lg bg-black hover:bg-zinc-900 text-zinc-300 hover:text-white border border-zinc-800 transition disabled:opacity-50 cursor-pointer"
            title="Re-evaluate Multi-Factor Strategy Engine"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-white' : ''}`} />
            <span>Evaluate Signal</span>
          </button>
        </div>

        {/* Risk Status Badges Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
          <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-2.5 text-center">
            <div className="text-[11px] text-zinc-400 font-mono uppercase tracking-wider">Trading Status</div>
            <div className="mt-1 flex items-center justify-center gap-1">
              {isPermitted && !circuitBreaker ? (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1 animate-pulse" />
                  PERMITTED
                </span>
              ) : (
                <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <ShieldAlert className="w-3 h-3 mr-1" />
                  HALTED
                </span>
              )}
            </div>
          </div>

          <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-2.5 text-center">
            <div className="text-[11px] text-zinc-400 font-mono uppercase tracking-wider">Max Drawdown</div>
            <div className="mt-1 font-mono text-xs font-bold text-white">
              {riskStatus ? `${riskStatus.drawdown_pct.toFixed(2)}%` : '0.00%'}
              <span className="text-[10px] text-zinc-500 font-normal ml-1">
                / {riskStatus?.max_drawdown_limit_pct ?? 10}%
              </span>
            </div>
          </div>

          <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-2.5 text-center">
            <div className="text-[11px] text-zinc-400 font-mono uppercase tracking-wider">Daily Loss</div>
            <div className="mt-1 font-mono text-xs font-bold text-white">
              ${riskStatus ? riskStatus.daily_loss_usd.toFixed(2) : '0.00'}
              <span className="text-[10px] text-zinc-500 font-normal ml-1">
                ({riskStatus ? riskStatus.daily_loss_pct.toFixed(1) : '0.0'}%)
              </span>
            </div>
          </div>

          <div className="bg-black/60 border border-zinc-800/80 rounded-lg p-2.5 text-center">
            <div className="text-[11px] text-zinc-400 font-mono uppercase tracking-wider">Consecutive Losses</div>
            <div className="mt-1 font-mono text-xs font-bold text-white">
              {riskStatus?.consecutive_losses ?? 0}
              <span className="text-[10px] text-zinc-500 font-normal ml-1">
                / {riskStatus?.max_consecutive_losses_limit ?? 30} max
              </span>
            </div>
          </div>
        </div>

        {/* Live Signal & Sizing Section */}
        <div className="bg-black/40 border border-zinc-800/80 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-medium text-zinc-300">
              <Zap className="w-4 h-4 text-white" />
              <span>Multi-Factor Strategy Signal</span>
            </div>
            <span
              className={`px-2.5 py-1 text-xs font-mono font-bold tracking-wider rounded-md border ${getActionBadge(
                action
              )}`}
            >
              {action}
            </span>
          </div>

          {strategyDecision?.order_details && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-zinc-800/80 text-xs font-mono">
              <div className="p-2 bg-zinc-950 rounded border border-zinc-800">
                <div className="text-[10px] text-zinc-500">ENTRY PRICE</div>
                <div className="text-white font-semibold">${strategyDecision.order_details.entry_price.toFixed(2)}</div>
              </div>
              <div className="p-2 bg-zinc-950 rounded border border-zinc-800">
                <div className="text-[10px] text-rose-400/80">STOP LOSS (1 ATR)</div>
                <div className="text-rose-400 font-semibold">${strategyDecision.order_details.stop_loss.toFixed(2)}</div>
              </div>
              <div className="p-2 bg-zinc-950 rounded border border-zinc-800">
                <div className="text-[10px] text-emerald-400/80">TAKE PROFIT (2 ATR)</div>
                <div className="text-emerald-400 font-semibold">${strategyDecision.order_details.take_profit.toFixed(2)}</div>
              </div>
              <div className="p-2 bg-zinc-950 rounded border border-zinc-800">
                <div className="text-[10px] text-zinc-400">POSITION SIZE</div>
                <div className="text-white font-semibold">
                  ${strategyDecision.order_details.position_size_usd.toFixed(2)}
                </div>
              </div>
            </div>
          )}

          {/* Reasoning / Numerical Explanation */}
          <div className="pt-2 border-t border-zinc-800/80">
            <div className="flex items-center gap-1.5 text-[11px] text-zinc-400 font-medium mb-1.5 font-mono">
              <Cpu className="w-3.5 h-3.5 text-zinc-400" />
              <span>Quantitative Rationale:</span>
            </div>
            <div className="space-y-1">
              <div className="text-xs text-zinc-300 bg-black/80 p-2.5 rounded border border-zinc-800 leading-relaxed font-mono">
                {strategyDecision?.reason || 'Awaiting strategy signal evaluation...'}
              </div>
              {strategyDecision?.numerical_explanation && strategyDecision.numerical_explanation.length > 0 && (
                <ul className="text-[11px] text-zinc-400 space-y-0.5 pl-4 list-disc font-mono">
                  {strategyDecision.numerical_explanation.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Footer / Safety Guard */}
      <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-[11px] text-zinc-400 font-mono">
        <div className="flex items-center gap-1.5">
          <Crosshair className="w-3.5 h-3.5 text-zinc-500" />
          <span>Max Sizing: $10,000.00 | 25% Max Risk Fraction</span>
        </div>
        <span className="text-zinc-300 font-medium">Drawdown Control Active</span>
      </div>
    </div>
  );
};
