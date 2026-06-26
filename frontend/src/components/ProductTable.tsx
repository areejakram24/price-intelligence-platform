import React from 'react';
import { RefreshCw, AlertTriangle, CheckCircle, Eye } from 'lucide-react';

export interface ProductStats {
  avg: number;
  min: number;
  max: number;
  count: number;
}

export interface Product {
  id: string;
  name: string;
  url: string;
  source: string;
  category: string;
  created_at: string;
  latest_price: number | null;
  currency: string;
  is_anomaly: boolean;
  anomaly_confidence: number;
  last_updated: string | null;
  stats: ProductStats;
}

interface ProductTableProps {
  products: Product[];
  selectedProductId: string | null;
  onSelectProduct: (id: string) => void;
  onTriggerScrape: (id: string) => void;
  scrapingStates: Record<string, boolean>;
}

export const ProductTable: React.FC<ProductTableProps> = ({
  products = [],
  selectedProductId,
  onSelectProduct,
  onTriggerScrape,
  scrapingStates,
}) => {
  return (
    <div className="bg-slate-900/40 backdrop-blur-md rounded-2xl border border-slate-800/80 shadow-xl overflow-hidden">
      <div className="p-5 border-b border-slate-800/60 flex justify-between items-center bg-slate-950/20">
        <div>
          <h2 className="text-lg font-bold text-slate-200">Data Stream Monitor</h2>
          <p className="text-xs text-slate-400 mt-0.5">Track engine states and dispatch manual sync requests</p>
        </div>
        <span className="text-[11px] font-mono bg-slate-950 border border-slate-800 text-slate-400 px-2.5 py-1 rounded-lg">
          count: {products.length}
        </span>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="border-b border-slate-800/60 text-[11px] font-bold text-slate-400 uppercase tracking-wider bg-slate-950/10">
              <th className="p-4">Target Identifiers</th>
              <th className="p-4">Category</th>
              <th className="p-4">Latest Stream Value</th>
              <th className="p-4">Pipeline Status</th>
              <th className="p-4">Last Ingestion</th>
              <th className="p-4 text-right pr-6">Automation Layer</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/40 text-xs">
            {!products.length ? (
              <tr>
                <td colSpan={6} className="p-8 text-center text-slate-500 font-medium italic">
                  No execution contexts found in cluster database.
                </td>
              </tr>
            ) : (
              products.map((p) => {
                const activeNode = selectedProductId === p.id;
                const activeWorker = scrapingStates[p.id] || false;
                
                return (
                  <tr 
                    key={p.id}
                    onClick={() => onSelectProduct(p.id)}
                    className={`transition-colors duration-100 hover:bg-slate-800/20 cursor-pointer ${
                      activeNode ? 'bg-indigo-500/5 border-l-2 border-indigo-500' : ''
                    }`}
                  >
                    <td className="p-4">
                      <div className="font-semibold text-slate-200">{p.name}</div>
                      <div className="text-[10px] text-slate-500 font-mono mt-0.5 truncate max-w-[180px]">{p.id}</div>
                    </td>
                    <td className="p-4 text-slate-400 font-medium">
                      {p.category}
                    </td>
                    <td className="p-4">
                      {p.latest_price !== null ? (
                        <div className="font-mono font-bold text-slate-200">
                          ${p.latest_price.toFixed(2)}
                        </div>
                      ) : (
                        <span className="text-slate-600 font-mono">--</span>
                      )}
                      {p.latest_price !== null && p.stats?.avg > 0 && (
                        <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                          μ: ${p.stats.avg.toFixed(2)}
                        </div>
                      )}
                    </td>
                    <td className="p-4">
                      {p.is_anomaly ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-950/30 text-rose-400 border border-rose-900/30">
                          <AlertTriangle size={11} />
                          OUTLIER DETECTED
                        </span>
                      ) : p.latest_price !== null ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-emerald-950/30 text-emerald-400 border border-emerald-900/30">
                          <CheckCircle size={11} />
                          NOMINAL
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-slate-950 text-slate-500 border border-slate-800">
                          IDLE
                        </span>
                      )}
                    </td>
                    <td className="p-4 font-mono text-slate-400">
                      {p.last_updated ? (
                        new Date(p.last_updated).toLocaleTimeString()
                      ) : (
                        <span className="text-slate-600">NULL</span>
                      )}
                    </td>
                    <td className="p-4 text-right pr-6" onClick={(e) => e.stopPropagation()}>
                      <div className="inline-flex items-center gap-2">
                        {activeNode ? (
                          <span className="text-[10px] font-mono text-indigo-400/70 mr-1 flex items-center gap-1">
                            <Eye size={12} />
                            <span>Attached</span>
                          </span>
                        ) : (
                          <button
                            onClick={() => onSelectProduct(p.id)}
                            className="p-1.5 rounded-lg bg-slate-950 border border-slate-850 hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                          >
                            <Eye size={13} />
                          </button>
                        )}
                        <button
                          onClick={() => onTriggerScrape(p.id)}
                          disabled={activeWorker}
                          className={`flex items-center gap-1 px-3 py-1.5 rounded-lg font-bold tracking-tight text-[11px] transition-all shadow-sm ${
                            activeWorker 
                              ? 'bg-slate-950 text-slate-600 border border-slate-850 cursor-not-allowed'
                              : 'bg-indigo-600 hover:bg-indigo-500 text-white active:scale-95'
                          }`}
                        >
                          <RefreshCw size={11} className={activeWorker ? 'animate-spin text-slate-600' : ''} />
                          <span>{activeWorker ? 'Syncing' : 'Sync Task'}</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ProductTable;