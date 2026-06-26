import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from 'recharts';
import { AlertCircle, TrendingUp } from 'lucide-react';

export interface PricePoint {
  id: number;
  price: number;
  currency: string;
  timestamp: string;
  is_anomaly: boolean;
  anomaly_confidence: number;
}

interface PriceChartProps {
  productName: string;
  history: PricePoint[];
  avgPrice: number;
}

const ChartDot = (props: any) => {
  const { cx, cy, payload } = props;
  if (!cx || !cy) return null;
  
  if (payload.is_anomaly) {
    return (
      <g key={`outlier-${payload.id}`}>
        <circle cx={cx} cy={cy} r={8} fill="#f43f5e" fillOpacity={0.3} className="animate-ping" />
        <circle cx={cx} cy={cy} r={5} fill="#e11d48" stroke="#ffffff" strokeWidth={1.5} />
      </g>
    );
  }

  return (
    <circle 
      key={`point-${payload.id}`}
      cx={cx} 
      cy={cy} 
      r={3} 
      fill="#6366f1" 
      stroke="#0f172a" 
      strokeWidth={1} 
    />
  );
};

export const PriceChart: React.FC<PriceChartProps> = ({ productName, history, avgPrice }) => {
  
  const formatXAxis = (str: string) => {
    try {
      const d = new Date(str);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return str;
    }
  };

  const CustomTooltip = ({ active, payload }: any) => {
    if (!active || !payload || !payload.length) return null;
    
    const data = payload[0].payload as PricePoint;
    const date = new Date(data.timestamp);
    
    return (
      <div className="bg-[#0b0f19] border border-slate-800/80 p-3.5 rounded-xl shadow-xl backdrop-blur-md font-sans">
        <p className="text-[10px] text-slate-500 font-mono mb-1.5">{date.toLocaleString()}</p>
        <div className="text-xs font-bold text-slate-200">
          Price: <span className="font-mono text-indigo-400">${data.price.toFixed(2)}</span>
        </div>
        {data.is_anomaly && (
          <div className="mt-2 flex items-center gap-1 text-[11px] text-rose-400 font-medium bg-rose-950/20 px-2 py-0.5 rounded border border-rose-900/30">
            <AlertCircle size={12} />
            <span>ONNX Flagged Anomaly ({(data.anomaly_confidence || 0).toFixed(4)})</span>
          </div>
        )}
      </div>
    );
  };

  const anomaliesCount = history.filter(h => h.is_anomaly).length;

  return (
    <div className="bg-slate-900/40 backdrop-blur-md rounded-2xl border border-slate-800/80 p-6 shadow-xl flex flex-col h-full">
      <div className="flex justify-between items-start gap-4 mb-4">
        <div>
          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-950/40 text-indigo-400 border border-indigo-900/30 uppercase tracking-wider">
            Stream Aggregations
          </span>
          <h2 className="text-lg font-bold text-slate-200 mt-1">{productName} Price Stream</h2>
        </div>
        
        <div className="flex gap-2.5 shrink-0">
          <div className="bg-slate-950/40 border border-slate-900 px-3 py-1.5 rounded-xl text-right">
            <div className="text-[9px] text-slate-500 font-medium uppercase">Ticks</div>
            <div className="text-sm font-bold text-indigo-400 font-mono">{history.length}</div>
          </div>
          {anomaliesCount > 0 && (
            <div className="bg-rose-950/20 border border-rose-900/30 px-3 py-1.5 rounded-xl text-right">
              <div className="text-[9px] text-rose-400 font-medium uppercase">Anomalies</div>
              <div className="text-sm font-bold text-rose-500 font-mono">{anomaliesCount}</div>
            </div>
          )}
        </div>
      </div>

      {!history || history.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-slate-600 py-12">
          <TrendingUp size={32} className="text-slate-800 mb-2 animate-pulse" />
          <p className="text-xs font-medium">Awaiting ingestion events...</p>
        </div>
      ) : (
        <div className="flex-1 min-h-[280px] w-full mt-2">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={history} margin={{ top: 10, right: 5, left: -25, bottom: 0 }}>
              <defs>
                <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366f1" stopOpacity={0.15}/>
                  <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" opacity={0.2} />
              <XAxis 
                dataKey="timestamp" 
                tickFormatter={formatXAxis} 
                stroke="#475569" 
                tick={{ fontSize: 9, fontFamily: 'monospace' }}
              />
              <YAxis 
                stroke="#475569"
                tick={{ fontSize: 9, fontFamily: 'monospace' }}
                domain={['auto', 'auto']}
                tickFormatter={(v) => `$${v}`}
              />
              <Tooltip content={<CustomTooltip />} />
              {avgPrice > 0 && (
                <ReferenceLine 
                  y={avgPrice} 
                  stroke="#ef4444" 
                  strokeDasharray="3 3" 
                  opacity={0.6}
                  label={{ value: `μ: $${avgPrice.toFixed(2)}`, fill: '#ef4444', fontSize: 9, position: 'top', fontFamily: 'monospace' }} 
                />
              )}
              <Area 
                type="monotone" 
                dataKey="price" 
                stroke="#6366f1" 
                strokeWidth={1.5}
                fillOpacity={1} 
                fill="url(#colorPrice)" 
                dot={<ChartDot />}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default PriceChart;