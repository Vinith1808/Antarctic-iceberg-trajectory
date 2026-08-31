import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { MODEL_LEADERBOARD } from '../types/trajectory';

export default function ErrorChart() {
  const data = MODEL_LEADERBOARD.map(m => ({
    ...m,
    fill: m.model === 'Regime Hybrid' ? '#22d3ee' : '#475569',
  }));

  return (
    <div className="bg-slate-800/50 backdrop-blur rounded-xl border border-slate-700/50 p-4">
      <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">
        Held-Out Test Performance
      </h3>
      <p className="text-[10px] text-slate-500 mb-3">Mean Endpoint Error on held-out test set</p>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} layout="vertical" margin={{ left: 60, right: 20, top: 5, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} unit=" km" />
          <YAxis type="category" dataKey="model" tick={{ fill: '#cbd5e1', fontSize: 10 }} width={120} />
          <Tooltip
            contentStyle={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: '#e2e8f0' }}
            formatter={(v: unknown) => [`${Number(v).toFixed(3)} km`, 'Mean EPE']}
          />
          <Bar dataKey="epe_km" radius={[0, 4, 4, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
