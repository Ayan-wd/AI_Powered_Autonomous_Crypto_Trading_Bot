import React, { useEffect, useState, useMemo, useRef } from 'react';
import {
  CandlestickChart,
  LineChart,
  AreaChart,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import { apiService, type CandleResponse, type TickerResponse } from '../services/api';

interface RealtimeCoinChartProps {
  symbol: string;
  onSymbolChange: (symbol: string) => void;
  timeframe: string;
  onTimeframeChange: (tf: string) => void;
  currentTicker: TickerResponse | null;
  onSyncCandles?: () => Promise<void>;
  syncing?: boolean;
}

const COIN_CHIPS = [
  { symbol: 'BTCUSDT', label: 'BTC' },
  { symbol: 'ETHUSDT', label: 'ETH' },
  { symbol: 'SOLUSDT', label: 'SOL' },
  { symbol: 'BNBUSDT', label: 'BNB' },
  { symbol: 'DOGEUSDT', label: 'DOGE' },
  { symbol: 'ADAUSDT', label: 'ADA' },
];

const TIMEFRAMES = ['1m', '5m', '15m', '1h', '4h', '1d'];

export const RealtimeCoinChart: React.FC<RealtimeCoinChartProps> = ({
  symbol,
  onSymbolChange,
  timeframe,
  onTimeframeChange,
  currentTicker,
  onSyncCandles,
  syncing = false,
}) => {
  const [candles, setCandles] = useState<CandleResponse[]>([]);
  const [chartType, setChartType] = useState<'candle' | 'area' | 'line'>('area');
  const [showEma20, setShowEma20] = useState<boolean>(true);
  const [showEma50, setShowEma50] = useState<boolean>(false);
  const [showVolume, setShowVolume] = useState<boolean>(true);
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [lastPrice, setLastPrice] = useState<number | null>(null);
  const [priceFlash, setPriceFlash] = useState<'up' | 'down' | null>(null);
  const [chartLoading, setChartLoading] = useState<boolean>(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState<{ width: number; height: number }>({
    width: 800,
    height: 380,
  });

  // Effective symbol for single-coin display
  const activeSymbol = symbol === 'ALL' ? 'BTCUSDT' : symbol;

  // Responsive chart width
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth || 800,
          height: 380,
        });
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Fetch candle history
  const loadCandles = async (sym: string, tf: string) => {
    try {
      setChartLoading(true);
      const data = await apiService.getCandles(sym, tf, 70);
      if (data && data.length > 0) {
        setCandles(data);
      }
    } catch (e) {
      console.warn('Failed to fetch candles:', e);
    } finally {
      setChartLoading(false);
    }
  };

  useEffect(() => {
    loadCandles(activeSymbol, timeframe);
    const interval = setInterval(() => {
      loadCandles(activeSymbol, timeframe);
    }, 4000);
    return () => clearInterval(interval);
  }, [activeSymbol, timeframe]);

  // Real-time ticker update hook: updates last candle dynamically
  useEffect(() => {
    if (!currentTicker || currentTicker.symbol !== activeSymbol) return;

    const newPrice = currentTicker.price;
    if (lastPrice !== null && newPrice !== lastPrice) {
      setPriceFlash(newPrice > lastPrice ? 'up' : 'down');
      const timer = setTimeout(() => setPriceFlash(null), 900);
      return () => clearTimeout(timer);
    }
    setLastPrice(newPrice);

    // Merge real-time tick into latest candle in memory
    setCandles((prev) => {
      if (!prev || prev.length === 0) return prev;
      const updated = [...prev];
      const last = { ...updated[updated.length - 1] };
      last.close = newPrice;
      if (newPrice > last.high) last.high = newPrice;
      if (newPrice < last.low) last.low = newPrice;
      updated[updated.length - 1] = last;
      return updated;
    });
  }, [currentTicker, activeSymbol]);

  // Calculate moving averages
  const { ema20Values, ema50Values } = useMemo(() => {
    if (!candles || candles.length === 0) return { ema20Values: [], ema50Values: [] };

    const calculateEMA = (period: number) => {
      const k = 2 / (period + 1);
      const res: (number | null)[] = [];
      let ema = candles[0].close;
      for (let i = 0; i < candles.length; i++) {
        if (i < period - 1) {
          res.push(null);
        } else if (i === period - 1) {
          // Simple average as seed
          const sum = candles.slice(0, period).reduce((acc, c) => acc + c.close, 0);
          ema = sum / period;
          res.push(ema);
        } else {
          ema = candles[i].close * k + ema * (1 - k);
          res.push(ema);
        }
      }
      return res;
    };

    return {
      ema20Values: calculateEMA(20),
      ema50Values: calculateEMA(50),
    };
  }, [candles]);

  // Price calculations & bounds
  const { minPrice, maxPrice, maxVolume, priceRange } = useMemo(() => {
    if (!candles || candles.length === 0) {
      return { minPrice: 0, maxPrice: 1, maxVolume: 1, priceRange: 1 };
    }
    let min = Infinity;
    let max = -Infinity;
    let maxVol = 0;

    candles.forEach((c) => {
      if (c.low < min) min = c.low;
      if (c.high > max) max = c.high;
      if (c.volume > maxVol) maxVol = c.volume;
    });

    const padding = (max - min) * 0.08 || 1;
    return {
      minPrice: Math.max(0, min - padding),
      maxPrice: max + padding,
      maxVolume: maxVol || 1,
      priceRange: max - min + padding * 2 || 1,
    };
  }, [candles]);

  const livePrice = currentTicker?.price ?? (candles.length > 0 ? candles[candles.length - 1].close : 0);
  const priceChange = currentTicker?.price_change_24h_pct ?? 0;
  const isPositive = priceChange >= 0;

  // Chart coordinate mapping
  const chartWidth = dimensions.width;
  const chartHeight = dimensions.height;
  const paddingRight = 68;
  const paddingBottom = showVolume ? 55 : 30;
  const paddingTop = 20;
  const paddingLeft = 10;

  const innerWidth = Math.max(10, chartWidth - paddingLeft - paddingRight);
  const innerHeight = Math.max(10, chartHeight - paddingTop - paddingBottom);
  const volumeHeight = showVolume ? 35 : 0;
  const pricePlotHeight = innerHeight - volumeHeight;

  const getX = (index: number) => {
    if (candles.length <= 1) return paddingLeft + innerWidth / 2;
    return paddingLeft + (index / (candles.length - 1)) * innerWidth;
  };

  const getY = (price: number) => {
    return paddingTop + pricePlotHeight - ((price - minPrice) / priceRange) * pricePlotHeight;
  };

  // Generate SVG paths
  const linePath = useMemo(() => {
    if (candles.length === 0) return '';
    return candles
      .map((c, i) => `${i === 0 ? 'M' : 'L'} ${getX(i).toFixed(1)} ${getY(c.close).toFixed(1)}`)
      .join(' ');
  }, [candles, minPrice, priceRange, innerWidth, pricePlotHeight]);

  const areaPath = useMemo(() => {
    if (candles.length === 0) return '';
    const firstX = getX(0).toFixed(1);
    const lastX = getX(candles.length - 1).toFixed(1);
    const bottomY = (paddingTop + pricePlotHeight).toFixed(1);
    return `${linePath} L ${lastX} ${bottomY} L ${firstX} ${bottomY} Z`;
  }, [linePath, candles, pricePlotHeight]);

  const ema20Path = useMemo(() => {
    if (!showEma20 || candles.length === 0) return '';
    const points: string[] = [];
    ema20Values.forEach((val, i) => {
      if (val !== null) {
        points.push(`${points.length === 0 ? 'M' : 'L'} ${getX(i).toFixed(1)} ${getY(val).toFixed(1)}`);
      }
    });
    return points.join(' ');
  }, [ema20Values, showEma20, minPrice, priceRange, innerWidth, pricePlotHeight]);

  const ema50Path = useMemo(() => {
    if (!showEma50 || candles.length === 0) return '';
    const points: string[] = [];
    ema50Values.forEach((val, i) => {
      if (val !== null) {
        points.push(`${points.length === 0 ? 'M' : 'L'} ${getX(i).toFixed(1)} ${getY(val).toFixed(1)}`);
      }
    });
    return points.join(' ');
  }, [ema50Values, showEma50, minPrice, priceRange, innerWidth, pricePlotHeight]);

  const currentPriceY = getY(livePrice);

  const formatPrice = (p: number) => {
    if (p >= 1000) return `$${p.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (p >= 1) return `$${p.toFixed(3)}`;
    return `$${p.toFixed(4)}`;
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const mouseX = e.clientX - rect.left - paddingLeft;
    if (mouseX < 0 || mouseX > innerWidth || candles.length === 0) {
      setHoverIndex(null);
      return;
    }
    const ratio = mouseX / innerWidth;
    const index = Math.min(candles.length - 1, Math.max(0, Math.round(ratio * (candles.length - 1))));
    setHoverIndex(index);
  };

  const hoveredCandle = hoverIndex !== null && candles[hoverIndex] ? candles[hoverIndex] : null;

  return (
    <div className="bg-[#09090b] rounded-xl border border-zinc-800 text-white overflow-hidden shadow-2xl transition-all">
      {/* Top Header Bar */}
      <div className="p-4 sm:p-5 border-b border-zinc-800/90 flex flex-wrap items-center justify-between gap-4">
        {/* Coin Selector Chips & Ticker */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Quick Coin Buttons */}
          <div className="flex items-center gap-1 bg-black p-1 rounded-lg border border-zinc-800">
            {COIN_CHIPS.map((c) => (
              <button
                key={c.symbol}
                onClick={() => onSymbolChange(c.symbol)}
                className={`px-2.5 py-1 text-xs font-mono font-bold rounded transition ${
                  activeSymbol === c.symbol
                    ? 'bg-white text-black shadow-sm'
                    : 'text-zinc-400 hover:text-white hover:bg-zinc-900'
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>

          <div className="h-6 w-px bg-zinc-800 hidden sm:block" />

          {/* Live Price Display */}
          <div className="flex items-baseline gap-2.5">
            <span className="text-xl sm:text-2xl font-black font-mono tracking-tight text-white">
              {formatPrice(livePrice)}
            </span>
            <span
              className={`inline-flex items-center gap-0.5 text-xs font-mono font-bold px-2 py-0.5 rounded ${
                isPositive
                  ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                  : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
              }`}
            >
              {isPositive ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
              {isPositive ? '+' : ''}
              {priceChange.toFixed(2)}%
            </span>
            {priceFlash && (
              <span
                className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded transition animate-pulse ${
                  priceFlash === 'up' ? 'bg-emerald-400 text-black' : 'bg-rose-500 text-white'
                }`}
              >
                {priceFlash === 'up' ? 'TICK ▲' : 'TICK ▼'}
              </span>
            )}
          </div>
        </div>

        {/* Controls: Timeframe, Chart Type, Overlays */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Timeframe selector */}
          <div className="flex items-center bg-black p-1 rounded-lg border border-zinc-800 text-xs font-mono">
            {TIMEFRAMES.map((tf) => (
              <button
                key={tf}
                onClick={() => onTimeframeChange(tf)}
                className={`px-2 py-0.5 rounded transition ${
                  timeframe === tf
                    ? 'bg-white text-black font-bold shadow-sm'
                    : 'text-zinc-400 hover:text-white'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>

          {/* Chart Type Selector */}
          <div className="flex items-center bg-black p-1 rounded-lg border border-zinc-800 text-xs">
            <button
              onClick={() => setChartType('area')}
              className={`p-1.5 rounded transition ${
                chartType === 'area' ? 'bg-white text-black' : 'text-zinc-400 hover:text-white'
              }`}
              title="Area Gradient Glow"
            >
              <AreaChart className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setChartType('candle')}
              className={`p-1.5 rounded transition ${
                chartType === 'candle' ? 'bg-white text-black' : 'text-zinc-400 hover:text-white'
              }`}
              title="Candlestick OHLC"
            >
              <CandlestickChart className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setChartType('line')}
              className={`p-1.5 rounded transition ${
                chartType === 'line' ? 'bg-white text-black' : 'text-zinc-400 hover:text-white'
              }`}
              title="Simple Line"
            >
              <LineChart className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* EMA Overlays Toggle */}
          <div className="hidden md:flex items-center gap-1 bg-black p-1 rounded-lg border border-zinc-800 text-[11px] font-mono">
            <button
              onClick={() => setShowEma20(!showEma20)}
              className={`px-1.5 py-0.5 rounded transition ${
                showEma20 ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              EMA 20
            </button>
            <button
              onClick={() => setShowEma50(!showEma50)}
              className={`px-1.5 py-0.5 rounded transition ${
                showEma50 ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              EMA 50
            </button>
            <button
              onClick={() => setShowVolume(!showVolume)}
              className={`px-1.5 py-0.5 rounded transition ${
                showVolume ? 'bg-white/10 text-white border border-white/20' : 'text-zinc-500 hover:text-zinc-300'
              }`}
            >
              VOL
            </button>
          </div>

          {/* Sync Button */}
          {onSyncCandles && (
            <button
              onClick={onSyncCandles}
              disabled={syncing}
              className="px-2.5 py-1 text-xs font-mono text-zinc-300 hover:text-white bg-black hover:bg-zinc-900 border border-zinc-800 rounded-lg transition flex items-center gap-1.5"
              title="Sync latest historical candles from Binance"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin text-white' : ''}`} />
              <span className="hidden sm:inline">Sync</span>
            </button>
          )}
        </div>
      </div>

      {/* Hover Info Tooltip Bar */}
      <div className="px-5 py-2 border-b border-zinc-900 bg-black/40 text-[11px] font-mono text-zinc-400 flex flex-wrap items-center justify-between gap-4">
        {hoveredCandle ? (
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-zinc-300 font-semibold">{hoveredCandle.timestamp.slice(11, 19)}</span>
            <span>
              O: <strong className="text-white">{formatPrice(hoveredCandle.open)}</strong>
            </span>
            <span>
              H: <strong className="text-white">{formatPrice(hoveredCandle.high)}</strong>
            </span>
            <span>
              L: <strong className="text-white">{formatPrice(hoveredCandle.low)}</strong>
            </span>
            <span>
              C: <strong className="text-white">{formatPrice(hoveredCandle.close)}</strong>
            </span>
            <span>
              Vol: <strong className="text-white">{hoveredCandle.volume.toFixed(2)}</strong>
            </span>
          </div>
        ) : (
          <div className="flex items-center gap-4 text-zinc-400">
            <span>
              24h Vol: <strong className="text-white">${((currentTicker?.volume_24h || 0) / 1000).toFixed(1)}k</strong>
            </span>
            <span>
              Pair: <strong className="text-white">{activeSymbol}</strong>
            </span>
            <span>
              Interval: <strong className="text-white">{timeframe}</strong>
            </span>
          </div>
        )}

        <div className="flex items-center gap-2 text-zinc-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[10px] font-bold tracking-wider uppercase text-zinc-300">Live Updating</span>
        </div>
      </div>

      {/* SVG Canvas Area */}
      <div ref={containerRef} className="relative w-full h-[380px] bg-black select-none">
        {chartLoading && candles.length === 0 ? (
          <div className="absolute inset-0 flex items-center justify-center bg-black/60 z-20">
            <div className="flex items-center gap-2 text-xs font-mono text-zinc-400">
              <RefreshCw className="w-4 h-4 animate-spin text-white" />
              <span>Fetching exchange candlestick stream...</span>
            </div>
          </div>
        ) : null}

        <svg
          width="100%"
          height="100%"
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          className="overflow-visible cursor-crosshair"
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoverIndex(null)}
        >
          <defs>
            {/* White Area Gradient */}
            <linearGradient id="whiteAreaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#ffffff" stopOpacity="0.28" />
              <stop offset="50%" stopColor="#ffffff" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#ffffff" stopOpacity="0.00" />
            </linearGradient>

            {/* Subtle Grid Pattern */}
            <pattern id="gridPattern" width="60" height="40" patternUnits="userSpaceOnUse">
              <path d="M 60 0 L 0 0 0 40" fill="none" stroke="#18181b" strokeWidth="0.8" />
            </pattern>
          </defs>

          {/* Background Grid */}
          <rect x={paddingLeft} y={paddingTop} width={innerWidth} height={innerHeight} fill="url(#gridPattern)" />

          {/* Horizontal Reference Price Lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const p = minPrice + priceRange * (1 - ratio);
            const y = paddingTop + ratio * pricePlotHeight;
            return (
              <g key={ratio}>
                <line
                  x1={paddingLeft}
                  y1={y}
                  x2={paddingLeft + innerWidth}
                  y2={y}
                  stroke="#1c1c21"
                  strokeDasharray="2,3"
                />
                <text
                  x={paddingLeft + innerWidth + 8}
                  y={y + 3.5}
                  fill="#71717a"
                  fontSize="9.5"
                  fontFamily="monospace"
                >
                  {formatPrice(p)}
                </text>
              </g>
            );
          })}

          {/* Volume Histogram Bars */}
          {showVolume &&
            candles.map((c, i) => {
              const x = getX(i);
              const barHeight = (c.volume / maxVolume) * volumeHeight;
              const y = paddingTop + innerHeight - barHeight;
              const isUp = c.close >= c.open;
              const barWidth = Math.max(1.5, (innerWidth / candles.length) * 0.65);

              return (
                <rect
                  key={`vol-${i}`}
                  x={x - barWidth / 2}
                  y={y}
                  width={barWidth}
                  height={Math.max(1, barHeight)}
                  fill={isUp ? 'rgba(16, 185, 129, 0.25)' : 'rgba(244, 63, 94, 0.25)'}
                />
              );
            })}

          {/* Candlestick OHLC Mode */}
          {chartType === 'candle' &&
            candles.map((c, i) => {
              const x = getX(i);
              const openY = getY(c.open);
              const closeY = getY(c.close);
              const highY = getY(c.high);
              const lowY = getY(c.low);
              const isBullish = c.close >= c.open;
              const candleTop = Math.min(openY, closeY);
              const candleHeight = Math.max(2, Math.abs(openY - closeY));
              const candleWidth = Math.max(2.5, (innerWidth / candles.length) * 0.7);

              return (
                <g key={`candle-${i}`}>
                  {/* High/Low Wick */}
                  <line
                    x1={x}
                    y1={highY}
                    x2={x}
                    y2={lowY}
                    stroke={isBullish ? '#10b981' : '#f43f5e'}
                    strokeWidth="1.2"
                  />
                  {/* Candle Body */}
                  <rect
                    x={x - candleWidth / 2}
                    y={candleTop}
                    width={candleWidth}
                    height={candleHeight}
                    fill={isBullish ? '#ffffff' : '#18181b'}
                    stroke={isBullish ? '#ffffff' : '#f43f5e'}
                    strokeWidth="1.2"
                    rx="1"
                  />
                </g>
              );
            })}

          {/* Area Mode: Fill + Crisp Stroke */}
          {chartType === 'area' && (
            <>
              <path d={areaPath} fill="url(#whiteAreaGradient)" />
              <path d={linePath} fill="none" stroke="#ffffff" strokeWidth="2" strokeLinecap="round" />
            </>
          )}

          {/* Line Mode: Crisp Pure White Stroke */}
          {chartType === 'line' && (
            <path d={linePath} fill="none" stroke="#ffffff" strokeWidth="2.2" strokeLinecap="round" />
          )}

          {/* EMA 20 (Cyan) */}
          {showEma20 && ema20Path && (
            <path d={ema20Path} fill="none" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="3,2" opacity="0.85" />
          )}

          {/* EMA 50 (Gold/Amber) */}
          {showEma50 && ema50Path && (
            <path d={ema50Path} fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="4,3" opacity="0.85" />
          )}

          {/* Live Market Price Horizontal Dotted Line & Pill */}
          {livePrice >= minPrice && livePrice <= maxPrice && (
            <g>
              <line
                x1={paddingLeft}
                y1={currentPriceY}
                x2={paddingLeft + innerWidth}
                y2={currentPriceY}
                stroke={isPositive ? '#10b981' : '#f43f5e'}
                strokeWidth="1.2"
                strokeDasharray="3,3"
                opacity="0.8"
              />
              <circle
                cx={paddingLeft + innerWidth}
                cy={currentPriceY}
                r="3.5"
                fill={isPositive ? '#10b981' : '#f43f5e'}
                className="animate-pulse"
              />
              {/* Right margin price pill */}
              <rect
                x={paddingLeft + innerWidth + 4}
                y={currentPriceY - 8}
                width="60"
                height="16"
                rx="3"
                fill={isPositive ? '#064e3b' : '#4c0519'}
                stroke={isPositive ? '#10b981' : '#f43f5e'}
                strokeWidth="0.8"
              />
              <text
                x={paddingLeft + innerWidth + 7}
                y={currentPriceY + 3.5}
                fill="#ffffff"
                fontSize="9.5"
                fontFamily="monospace"
                fontWeight="bold"
              >
                {formatPrice(livePrice)}
              </text>
            </g>
          )}

          {/* Hover Crosshair */}
          {hoverIndex !== null && (
            <g>
              <line
                x1={getX(hoverIndex)}
                y1={paddingTop}
                x2={getX(hoverIndex)}
                y2={paddingTop + innerHeight}
                stroke="#52525b"
                strokeDasharray="2,2"
                strokeWidth="1"
              />
              {hoveredCandle && (
                <>
                  <line
                    x1={paddingLeft}
                    y1={getY(hoveredCandle.close)}
                    x2={paddingLeft + innerWidth}
                    y2={getY(hoveredCandle.close)}
                    stroke="#52525b"
                    strokeDasharray="2,2"
                    strokeWidth="1"
                  />
                  <circle
                    cx={getX(hoverIndex)}
                    cy={getY(hoveredCandle.close)}
                    r="4"
                    fill="#ffffff"
                    stroke="#000000"
                    strokeWidth="2"
                  />
                </>
              )}
            </g>
          )}
        </svg>
      </div>

      {/* Footer Info: Coins Quick Switcher Strip */}
      <div className="p-3 border-t border-zinc-800 bg-zinc-950 flex flex-wrap items-center justify-between text-xs gap-3">
        <div className="flex items-center gap-3">
          <span className="text-zinc-400 font-mono text-[11px]">Direct Coin Switch:</span>
          <div className="flex items-center gap-1.5">
            {COIN_CHIPS.map((chip) => (
              <button
                key={chip.symbol}
                onClick={() => onSymbolChange(chip.symbol)}
                className={`text-[11px] font-mono px-2 py-0.5 rounded border transition ${
                  activeSymbol === chip.symbol
                    ? 'bg-white text-black font-bold border-white'
                    : 'bg-black text-zinc-400 hover:text-white border-zinc-800'
                }`}
              >
                {chip.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4 text-[11px] font-mono text-zinc-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-0.5 bg-cyan-400 inline-block"></span> EMA 20
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-0.5 bg-amber-400 inline-block"></span> EMA 50
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-1 bg-white inline-block"></span> Price Line
          </span>
        </div>
      </div>
    </div>
  );
};
