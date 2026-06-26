import React, { useState, useEffect } from 'react';
import { ProductTable } from './ProductTable';
import type { Product } from './ProductTable';
import { PriceChart } from './PriceChart';
import type { PricePoint } from './PriceChart';
import { 
  Database, 
  Activity, 
  AlertOctagon, 
  Cpu, 
  Terminal, 
  Flame, 
  ExternalLink,
  ShieldCheck,
  Loader2
} from 'lucide-react';

export const Dashboard: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
  const [history, setHistory] = useState<PricePoint[]>([]);
  const [scrapingStates, setScrapingStates] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<string[]>([]);
  const [systemAlerts, setSystemAlerts] = useState<{ id: string; msg: string; time: string }[]>([]);

  const addLog = (msg: string) => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [`[${time}] ${msg}`, ...prev.slice(0, 49)]);
  };

  const fetchProducts = async () => {
    try {
      const res = await fetch('/api/products');
      if (!res.ok) throw new Error(`API responded with ${res.status}`);
      
      const data: Product[] = await res.json();
      const safeData = data || [];
      setProducts(safeData);
      
      if (safeData.length > 0 && !selectedProductId) {
        setSelectedProductId(safeData[0].id);
      }
      
      const sessionAlerts: typeof systemAlerts = [];
      safeData.forEach(p => {
        if (p.is_anomaly && p.latest_price !== null) {
          sessionAlerts.push({
            id: `${p.id}-${p.last_updated}`,
            msg: `CRITICAL: Anomaly on ${p.name} ($${p.latest_price.toFixed(2)}) [ONNX Conf: ${(p.anomaly_confidence || 0).toFixed(4)}]`,
            time: p.last_updated ? new Date(p.last_updated).toLocaleTimeString() : new Date().toLocaleTimeString()
          });
        }
      });
      
      setSystemAlerts(prev => {
        const unique = [...sessionAlerts, ...prev];
        const seen = new Set();
        return unique.filter(item => !seen.has(item.id) && seen.add(item.id)).slice(0, 10);
      });

    } catch (err) {
      console.error("Failed to sync catalog:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async (id: string) => {
    try {
      const res = await fetch(`/api/products/${id}/history`);
      if (res.ok) {
        const data = await res.json();
        setHistory(data || []);
      }
    } catch (err) {
      console.error(`History fetch dropped for ${id}:`, err);
    }
  };

  const handleTriggerScrape = async (id: string) => {
    setScrapingStates(prev => ({ ...prev, [id]: true }));
    addLog(`Dispatching Celery crawl worker for target: ${id}`);
    
    try {
      const res = await fetch(`/api/scrape?product_id=${id}`, { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        addLog(`Broker acknowledged. Task ID: ${data.task_id.substring(0, 8)}...`);
      } else {
        addLog(`Task rejection on worker cluster for target ${id}`);
      }
    } catch (err) {
      addLog(`Pipeline trigger exception: ${err}`);
    } finally {
      // Keep UI active briefly to simulate pipeline queuing network turnaround
      setTimeout(() => {
        setScrapingStates(prev => ({ ...prev, [id]: false }));
        fetchProducts();
        if (selectedProductId) fetchHistory(selectedProductId);
      }, 2000);
    }
  };

  const handleScrapeAll = () => {
    if (!products.length) {
      addLog("Global bypass: Active catalog collection is empty.");
      return;
    }
    products.forEach(p => handleTriggerScrape(p.id));
  };

  useEffect(() => {
    fetchProducts();
    const ticker = setInterval(fetchProducts, 3000);
    return () => clearInterval(ticker);
  }, [selectedProductId]);

  useEffect(() => {
    if (!selectedProductId) return;
    fetchHistory(selectedProductId);
    const item = products.find(p => p.id === selectedProductId);
    addLog(`Attached consumer pipeline node to: ${item ? item.name : selectedProductId}`);
  }, [selectedProductId]);

  const totalProducts = products.length;
  const activeAnomalies = products.filter(p => p.is_anomaly).length;
  const totalIngestedRecords = products.reduce((acc, p) => acc + (p.stats?.count || 0), 0);
  const selectedProduct = products.find(p => p.id === selectedProductId);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#07090e] flex flex-col items-center justify-center text-slate-200">
        <Loader2 className="h-8 w-8 text-indigo-500 animate-spin mb-3" />
        <p className="text-xs font-mono text-slate-500">bootstrapping platform context...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#07090e] bg-gradient-to-br from-[#07090e] via-[#0b0e14] to-[#0d1424] text-slate-100 p-6 md:p-8 font-sans">
      
      <header className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8 border-b border-slate-800/60 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
            </span>
            <span className="text-[10px] font-bold uppercase tracking-widest text-indigo-400/90">Event-Driven Stream Architecture</span>
          </div>
          <h1 className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-slate-100 via-indigo-200 to-indigo-400 bg-clip-text text-transparent">
  AeroPrice Intelligence Platform
</h1>
<p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
  A real-time price monitoring, streaming, and anomaly detection pipeline utilizing Python <span className="text-indigo-300 font-mono">asyncio</span>, <span className="text-indigo-300 font-mono">Celery</span>, Apache <span className="text-indigo-300 font-mono">Kafka</span>, <span className="text-indigo-300 font-mono">PostgreSQL</span>, and scikit-learn <span className="text-indigo-300 font-mono">ONNX</span> models.
</p>
        </div>
        
        <div className="flex items-center gap-3">
          <a href="http://localhost:3000" target="_blank" rel="noreferrer" className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 border border-slate-800 hover:bg-slate-800 rounded-xl text-xs font-semibold shadow transition-all active:scale-95">
            <Activity size={13} />
            <span>Grafana Metrics</span>
            <ExternalLink size={11} className="opacity-50" />
          </a>
          <button onClick={handleScrapeAll} className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold shadow-md transition-all active:scale-95">
            <Flame size={13} />
            <span>Sync Entire Catalog</span>
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto space-y-8">
        
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-slate-900/40 backdrop-blur-md rounded-2xl border border-slate-800/80 p-5 flex items-center gap-4">
            <div className="p-3 bg-indigo-950/40 rounded-xl border border-indigo-800/30 text-indigo-400"><Database size={20} /></div>
            <div>
              <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Monitored Items</div>
              <div className="text-xl font-bold font-mono text-slate-200">{totalProducts}</div>
            </div>
          </div>

          <div className="bg-slate-900/40 backdrop-blur-md rounded-2xl border border-slate-800/80 p-5 flex items-center gap-4">
            <div className="p-3 bg-rose-950/40 rounded-xl border border-rose-800/30 text-rose-400"><AlertOctagon size={20} /></div>
            <div>
              <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Active Outliers</div>
              <div className="text-xl font-bold font-mono text-rose-400">{activeAnomalies}</div>
            </div>
          </div>

          <div className="bg-slate-900/40 backdrop-blur-md rounded-2xl border border-slate-800/80 p-5 flex items-center gap-4">
            <div className="p-3 bg-emerald-950/40 rounded-xl border border-emerald-800/30 text-emerald-400"><Activity size={20} /></div>
            <div>
              <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">Kafka Ingest Volume</div>
              <div className="text-xl font-bold font-mono text-emerald-400">{totalIngestedRecords}</div>
            </div>
          </div>

          <div className="bg-slate-900/40 backdrop-blur-md rounded-2xl border border-slate-800/80 p-5 flex items-center gap-4">
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-indigo-400"><Cpu size={20} /></div>
            <div>
              <div className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">ONNX Subsystem</div>
              <div className="text-sm font-bold text-emerald-400 flex items-center gap-1 mt-0.5">
                <ShieldCheck size={15} />
                <span>Isolation Forest</span>
              </div>
            </div>
          </div>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-7">
            <ProductTable 
              products={products}
              selectedProductId={selectedProductId}
              onSelectProduct={setSelectedProductId}
              onTriggerScrape={handleTriggerScrape}
              scrapingStates={scrapingStates}
            />
          </div>
          <div className="lg:col-span-5">
            <PriceChart 
              productName={selectedProduct ? selectedProduct.name : "Select Target Component"}
              history={history}
              avgPrice={selectedProduct?.stats?.avg || 0}
            />
          </div>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          <div className="lg:col-span-6 bg-slate-900/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4 border-b border-slate-800/60 pb-3">
              <AlertOctagon className="text-rose-400" size={16} />
              <h3 className="text-sm font-bold text-slate-300">ONNX Inference Feed</h3>
            </div>
            <div className="space-y-2.5 max-h-[220px] overflow-y-auto pr-1 font-sans">
              {systemAlerts.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-2">No data streaming anomalies flagged.</p>
              ) : (
                systemAlerts.map(alert => (
                  <div key={alert.id} className="p-3 bg-rose-950/10 border border-rose-900/20 rounded-xl flex items-start gap-2.5">
                    <AlertOctagon size={14} className="text-rose-500 mt-0.5 shrink-0" />
                    <div className="flex-1">
                      <p className="text-xs font-medium text-rose-300/90 leading-tight">{alert.msg}</p>
                      <span className="text-[9px] text-slate-500 font-mono mt-1 block">{alert.time}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="lg:col-span-6 bg-slate-900/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6">
            <div className="flex items-center justify-between mb-4 border-b border-slate-800/60 pb-3">
              <div className="flex items-center gap-2">
                <Terminal className="text-indigo-400" size={16} />
                <h3 className="text-sm font-bold text-slate-300">Broker Stream Console</h3>
              </div>
              <span className="text-[9px] bg-slate-950 border border-slate-800 text-slate-500 px-1.5 py-0.5 rounded font-mono">STDOUT</span>
            </div>
            <div className="bg-slate-950/60 p-4 rounded-xl font-mono text-[11px] text-indigo-300/90 space-y-2 h-[220px] overflow-y-auto border border-slate-900/80 shadow-inner">
              {logs.length === 0 ? (
                <p className="text-slate-600 italic">Listening for consumer thread events...</p>
              ) : (
                logs.map((log, idx) => (
                  <div key={idx} className="border-l border-indigo-500/20 pl-2 leading-relaxed">{log}</div>
                ))
              )}
            </div>
          </div>
        </section>

      </main>
    </div>
  );
};

export default Dashboard;