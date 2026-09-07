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
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40 shadow-emerald-500/10';
      case 'SELL':
        return 'bg-rose-500/20 text-rose-400 border-rose-500/40 shadow-rose-500/10';
      default:
        return 'bg-amber-500/20 text-amber-300 border-amber-500/30 shadow-amber-500/10';
    }
  };

  return (
    <div className="bg-slate-900/60 backdrop-blur-md border border-slate-800/80 rounded-xl p-5 flex flex-col justify-between shadow-xl">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-semibold text-sm text-slate-200">Risk & Strategy Gatekeeper</h3>
              <p className="text-xs text-slate-400">Institutional Position Sizing & Drawdown Protection</p>
            </div>
          </div>

          <button
            onClick={onEvaluateStrategy}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-300 border border-indigo-500/30 transition-colors disabled:opacity-50 cursor-pointer"
            title="Re-evaluate Multi-Factor Strategy Engine"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Evaluate Signal</span>
          </button>
        </div>

        {/* Risk Status Badges Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-4">
          <div className="bg-slate-950/60 border border-slate-800/60 rounded-lg p-2.5 text-center">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider">Trading Status</div>
            <div className="mt-1 flex items-center justify-center gap-1">
              {isPermitted && !circuitBreaker ? (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1 animate-pulse" />
                  PERMITTED
                </span>
              ) : (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  <ShieldAlert className="w-3 h-3 mr-1" />
                  HALTED
                </span>
              )}
            </div>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/60 rounded-lg p-2.5 text-center">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider">Max Drawdown</div>
            <div className="mt-1 font-mono text-xs font-bold text-slate-200">
              {riskStatus ? `${riskStatus.drawdown_pct.toFixed(2)}%` : '0.00%'}
              <span className="text-[10px] text-slate-500 font-normal ml-1">
                / {riskStatus?.max_drawdown_limit_pct ?? 10}%
              </span>
            </div>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/60 rounded-lg p-2.5 text-center">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider">Daily Loss</div>
            <div className="mt-1 font-mono text-xs font-bold text-slate-200">
              ${riskStatus ? riskStatus.daily_loss_usd.toFixed(2) : '0.00'}
              <span className="text-[10px] text-slate-500 font-normal ml-1">
                ({riskStatus ? riskStatus.daily_loss_pct.toFixed(1) : '0.0'}%)
              </span>
            </div>
          </div>

          <div className="bg-slate-950/60 border border-slate-800/60 rounded-lg p-2.5 text-center">
            <div className="text-[11px] text-slate-400 uppercase tracking-wider">Consecutive Losses</div>
            <div className="mt-1 font-mono text-xs font-bold text-slate-200">
              {riskStatus?.consecutive_losses ?? 0}
              <span className="text-[10px] text-slate-500 font-normal ml-1">
                / {riskStatus?.max_consecutive_losses_limit ?? 3} max
              </span>
            </div>
          </div>
        </div>

        {/* Live Signal & Sizing Section */}
        <div className="bg-slate-950/40 border border-slate-800/60 rounded-xl p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-300">
              <Zap className="w-4 h-4 text-amber-400" />
              <span>Multi-Factor Strategy Signal</span>
            </div>
            <span
              className={`px-2.5 py-1 text-xs font-bold tracking-wider rounded-md border shadow-sm ${getActionBadge(
                action
              )}`}
            >
              {action}
            </span>
          </div>

          {strategyDecision?.order_details && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-slate-800/60 text-xs font-mono">
              <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
                <div className="text-[10px] text-slate-500">ENTRY PRICE</div>
                <div className="text-slate-200 font-semibold">${strategyDecision.order_details.entry_price.toFixed(2)}</div>
              </div>
              <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
                <div className="text-[10px] text-rose-400/80">STOP LOSS (1 ATR)</div>
                <div className="text-rose-400 font-semibold">${strategyDecision.order_details.stop_loss.toFixed(2)}</div>
              </div>
              <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
                <div className="text-[10px] text-emerald-400/80">TAKE PROFIT (2 ATR)</div>
                <div className="text-emerald-400 font-semibold">${strategyDecision.order_details.take_profit.toFixed(2)}</div>
              </div>
              <div className="p-2 bg-slate-900/60 rounded border border-slate-800">
                <div className="text-[10px] text-indigo-400/80">POSITION SIZE</div>
                <div className="text-indigo-300 font-semibold">
                  ${strategyDecision.order_details.position_size_usd.toFixed(2)} (1% Risk)
                </div>
              </div>
            </div>
          )}

          {/* Reasoning / Numerical Explanation */}
          <div className="pt-2 border-t border-slate-800/60">
            <div className="flex items-center gap-1.5 text-[11px] text-slate-400 font-medium mb-1.5">
              <Cpu className="w-3.5 h-3.5 text-indigo-400" />
              <span>Quantitative Gatekeeper Rationale:</span>
            </div>
            <div className="space-y-1">
              <div className="text-xs text-slate-300 bg-slate-900/80 p-2 rounded border border-slate-800/80 leading-relaxed font-mono">
                {strategyDecision?.reason || 'Awaiting strategy signal evaluation...'}
              </div>
              {strategyDecision?.numerical_explanation && strategyDecision.numerical_explanation.length > 0 && (
                <ul className="text-[11px] text-slate-400 space-y-0.5 pl-4 list-disc font-mono">
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
      <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400">
        <div className="flex items-center gap-1.5">
          <Crosshair className="w-3.5 h-3.5 text-slate-500" />
          <span>Max Cap: $10.00 | Risk: 1% Fixed Fractional</span>
        </div>
        <span className="font-mono text-emerald-400/90 font-medium">Anti-Martingale Enforced</span>
      </div>
    </div>
  );
};
