import { useState, useEffect } from 'react';
import { Loader2, TrendingUp, TrendingDown, Minus, Activity, Plus, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const CROP_EMOJIS = {
  Wheat: "🌾", Tomato: "🍅", Maize: "🌽", Onion: "🧅", Soybean: "🌿",
  Cotton: "☁️", Rice: "🍚", Potato: "🥔", Sugarcane: "🎋", "Black Gram": "🌱",
  Garlic: "🧄", Turmeric: "🫚", Apple: "🍎", Mango: "🥭", Banana: "🍌"
};

const getEmoji = (crop) => CROP_EMOJIS[crop] || "🌱";

// Improved Smooth Sparkline with glow
const Sparkline = ({ data, color }) => {
  if (!data || data.length === 0) return null;
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  const width = 100;
  const height = 30;

  const points = data.map((val, i) => {
    const x = (i / (data.length - 1)) * width;
    const y = height - ((val - min) / range) * height;
    return `${x},${y}`;
  });

  const pathD = `M ${points[0]} ` + points.slice(1).map(p => `L ${p}`).join(' ');
  const areaD = `${pathD} L ${width},${height} L 0,${height} Z`;

  // Strip var(--...) to get actual color if needed for gradient IDs, or just use string hash
  const gradId = `grad-${color.replace(/[^a-zA-Z0-9]/g, '')}`;

  return (
    <svg width={width} height={height} style={{ overflow: 'visible', filter: 'drop-shadow(0px 2px 4px rgba(0,0,0,0.2))' }}>
      <defs>
        <linearGradient id={gradId} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.25" />
          <stop offset="100%" stopColor={color} stopOpacity="0.0" />
        </linearGradient>
      </defs>
      <path d={areaD} fill={`url(#${gradId})`} />
      <path d={pathD} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={points[points.length-1].split(',')[0]} cy={points[points.length-1].split(',')[1]} r="3" fill={color} />
    </svg>
  );
};

export default function DetailedMarketPage({ location }) {
  const { authFetch } = useAuth();
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  
  const [supportedCrops, setSupportedCrops] = useState([]);
  const [selectedCrops, setSelectedCrops] = useState(["Wheat", "Tomato", "Maize", "Onion", "Soybean", "Rice"]);
  const [isEditing, setIsEditing] = useState(false);

  const stateName = location ? location.split(',').pop().trim() : "Maharashtra";

  useEffect(() => {
    authFetch('http://localhost:8000/api/v1/market/')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.supported_crops) setSupportedCrops(data.supported_crops);
      });
  }, [authFetch]);

  useEffect(() => {
    if (selectedCrops.length === 0) {
      setData([]);
      setLoading(false);
      return;
    }
    
    setLoading(true);
    const cropsParam = selectedCrops.map(encodeURIComponent).join(',');
    authFetch(`http://localhost:8000/api/v1/market/dashboard?state=${encodeURIComponent(stateName)}&crops=${cropsParam}`)
      .then(res => res.json())
      .then(json => {
        if (json.success) {
          setData(json.crops_data || []);
        }
      })
      .catch(err => console.error("Failed to fetch market dashboard:", err))
      .finally(() => setLoading(false));
  }, [stateName, selectedCrops, authFetch]);

  const toggleCrop = (crop) => {
    if (selectedCrops.includes(crop)) {
      setSelectedCrops(prev => prev.filter(c => c !== crop));
    } else {
      if (selectedCrops.length < 15) {
        setSelectedCrops(prev => [...prev, crop]);
      }
    }
  };

  return (
    <div style={{ flex: 1, padding: 20, display: 'flex', flexDirection: 'column', gap: 20, minHeight: 0 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <Activity size={20} color="var(--accent-green)" />
            Market Intelligence
          </h2>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
            Detailed historical and forecasted price trends for {stateName} APMC
          </div>
        </div>
        <button 
          onClick={() => setIsEditing(!isEditing)}
          style={{ background: isEditing ? 'var(--accent-green)' : 'var(--bg-input)', color: isEditing ? '#000' : 'var(--text-primary)', border: 'none', padding: '8px 16px', borderRadius: 8, fontSize: 13, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}
        >
          {isEditing ? 'Save Selection' : 'Choose Crops'}
        </button>
      </div>

      {isEditing && (
        <div style={{ background: 'var(--bg-card)', padding: '16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', flexShrink: 0 }}>
          <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12 }}>
            Select up to 15 crops to monitor in your dashboard:
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {supportedCrops.map(crop => {
              const isSelected = selectedCrops.includes(crop);
              const isDisabled = !isSelected && selectedCrops.length >= 15;
              return (
                <button
                  key={crop}
                  onClick={() => toggleCrop(crop)}
                  disabled={isDisabled}
                  style={{
                    padding: '6px 12px', fontSize: 13, borderRadius: 20,
                    border: `1px solid ${isSelected ? 'var(--accent-green)' : 'var(--border-subtle)'}`,
                    background: isSelected ? 'rgba(34,197,94,0.15)' : 'transparent',
                    color: isSelected ? 'var(--accent-green)' : (isDisabled ? 'var(--text-muted)' : 'var(--text-primary)'),
                    cursor: isDisabled ? 'not-allowed' : 'pointer',
                    display: 'flex', alignItems: 'center', gap: 6,
                    opacity: isDisabled ? 0.5 : 1,
                    transition: 'all 0.2s'
                  }}
                >
                  {getEmoji(crop)} {crop}
                  {isSelected && <X size={12} />}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {loading ? (
        <div style={{ flex: 1, background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1, overflow: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-input)', fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>
                <th style={{ padding: '16px', fontWeight: 600 }}>Crop</th>
                <th style={{ padding: '16px', fontWeight: 600 }}>Current Price</th>
                <th style={{ padding: '16px', fontWeight: 600 }}>Trend</th>
                <th style={{ padding: '16px', fontWeight: 600 }}>Past 7 Days</th>
                <th style={{ padding: '16px', fontWeight: 600 }}>Next 7 Days</th>
                <th style={{ padding: '16px', fontWeight: 600 }}>AI Insight</th>
              </tr>
            </thead>
            <tbody>
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <tr key={i} className="animate-pulse" style={{ borderBottom: i === 6 ? 'none' : '1px solid var(--border-subtle)' }}>
                  <td style={{ padding: '16px' }}>
                    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                      <div style={{ width: 24, height: 24, borderRadius: '50%', background: 'var(--bg-input)' }} />
                      <div style={{ width: 60, height: 14, borderRadius: 4, background: 'var(--bg-input)' }} />
                    </div>
                  </td>
                  <td style={{ padding: '16px' }}>
                    <div style={{ width: 50, height: 16, borderRadius: 4, background: 'var(--bg-input)', marginBottom: 4 }} />
                    <div style={{ width: 70, height: 10, borderRadius: 4, background: 'var(--bg-input)' }} />
                  </td>
                  <td style={{ padding: '16px' }}>
                    <div style={{ width: 60, height: 24, borderRadius: 12, background: 'var(--bg-input)' }} />
                  </td>
                  <td style={{ padding: '16px' }}>
                    <div style={{ width: 100, height: 30, borderRadius: 4, background: 'var(--bg-input)' }} />
                  </td>
                  <td style={{ padding: '16px' }}>
                    <div style={{ width: 100, height: 30, borderRadius: 4, background: 'var(--bg-input)' }} />
                  </td>
                  <td style={{ padding: '16px' }}>
                    <div style={{ width: '100%', height: 12, borderRadius: 4, background: 'var(--bg-input)', marginBottom: 4 }} />
                    <div style={{ width: '70%', height: 12, borderRadius: 4, background: 'var(--bg-input)' }} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      ) : selectedCrops.length === 0 ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
          Please choose some crops to display.
        </div>
      ) : (
        <div style={{ flex: 1, background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1, overflow: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                <tr style={{ borderBottom: '1px solid var(--border-subtle)', background: 'var(--bg-input)', fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: 1 }}>
                <th style={{ padding: '16px', fontWeight: 600 }}>Crop</th>
                <th style={{ padding: '16px', fontWeight: 600 }}>Current Price</th>
                <th style={{ padding: '16px', fontWeight: 600 }}>Trend</th>
                <th style={{ padding: '16px', fontWeight: 600 }}>Past 7 Days</th>
                <th style={{ padding: '16px', fontWeight: 600 }}>Next 7 Days</th>
                <th style={{ padding: '16px', fontWeight: 600 }}>AI Insight</th>
              </tr>
            </thead>
            <tbody>
              {data.map((item, idx) => {
                const trendDir = item.market_trend?.trend_direction;
                let trendIcon = "stable";
                let trendColor = "var(--text-muted)";
                
                if (trendDir === "rising" || trendDir === "up") {
                  trendIcon = "up";
                  trendColor = "var(--accent-green)";
                } else if (trendDir === "falling" || trendDir === "down") {
                  trendIcon = "down";
                  trendColor = "var(--accent-red)";
                }

                const pastData = (item.historical_7_days || []).map(d => d.predicted_price);
                const futureData = (item.forecast_7_days || []).map(d => d.predicted_price);

                return (
                  <tr key={item.crop} style={{ borderBottom: idx === data.length - 1 ? 'none' : '1px solid var(--border-subtle)', transition: 'background 0.2s', ':hover': { background: 'var(--bg-input)' } }}>
                    <td style={{ padding: '16px', display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ fontSize: 24 }}>{getEmoji(item.crop)}</div>
                      <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 14 }}>{item.crop}</div>
                    </td>
                    <td style={{ padding: '16px', fontWeight: 600, color: 'var(--text-primary)', fontSize: 15 }}>
                      ₹{item.current_price_per_quintal.toLocaleString()}
                      <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 400, marginTop: 2 }}>per quintal</div>
                    </td>
                    <td style={{ padding: '16px' }}>
                      <div style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '6px 10px', borderRadius: 20, fontSize: 12, fontWeight: 700, color: trendColor, background: `${trendColor}15` }}>
                        {trendIcon === "up" && <TrendingUp size={14} strokeWidth={3} />}
                        {trendIcon === "down" && <TrendingDown size={14} strokeWidth={3} />}
                        {trendIcon === "stable" && <Minus size={14} strokeWidth={3} />}
                        {item.market_trend?.percentage_change}%
                      </div>
                    </td>
                    <td style={{ padding: '16px' }}>
                      <Sparkline data={pastData} color="var(--text-muted)" />
                    </td>
                    <td style={{ padding: '16px' }}>
                      <Sparkline data={futureData} color={trendColor} />
                    </td>
                    <td style={{ padding: '16px', fontSize: 13, color: 'var(--text-muted)', maxWidth: 220, lineHeight: 1.5 }}>
                      {item.price_alerts && item.price_alerts[0] ? item.price_alerts[0] : "Stable market conditions expected."}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          </div>
        </div>
      )}
    </div>
  );
}
