import { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, BarChart2, Plus, X, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const CROP_EMOJIS = {
  Wheat: "🌾",
  Tomato: "🍅",
  Maize: "🌽",
  Onion: "🧅",
  Soybean: "🌿",
  Rice: "🍚",
  Cotton: "☁️",
  Potato: "🥔",
  Sugarcane: "🎋"
};

export default function MarketPricesWidget({ location }) {
  const { authFetch } = useAuth();
  const [trackedCrops, setTrackedCrops] = useState(["Wheat", "Tomato", "Maize", "Onion", "Soybean"]);
  const [supportedCrops, setSupportedCrops] = useState([]);
  const [marketData, setMarketData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);

  const stateName = location ? location.split(',').pop().trim() : "Maharashtra";

  // Fetch supported crops list once
  useEffect(() => {
    authFetch('http://localhost:8000/api/v1/market/')
      .then(res => res.json())
      .then(data => {
        if (data.success && data.supported_crops) {
          setSupportedCrops(data.supported_crops);
        }
      })
      .catch(err => console.error("Failed to load supported crops:", err));
  }, [authFetch]);

  // Fetch prices for tracked crops
  useEffect(() => {
    if (trackedCrops.length === 0) {
      setMarketData([]);
      setLoading(false);
      return;
    }

    setLoading(true);
    const fetchPromises = trackedCrops.map(crop =>
      authFetch(`http://localhost:8000/api/v1/market/${encodeURIComponent(crop)}?state=${encodeURIComponent(stateName)}`)
        .then(res => res.json())
        .catch(err => null)
    );

    Promise.all(fetchPromises).then(results => {
      const validData = results.filter(res => res && res.success).map(res => {
        const trendDir = res.market_trend?.trend_direction;
        let trendIcon = "stable";
        if (trendDir === "rising" || trendDir === "up") trendIcon = "up";
        if (trendDir === "falling" || trendDir === "down") trendIcon = "down";

        return {
          crop: CROP_EMOJIS[res.crop] || "🌱",
          name: res.crop,
          unit: "per quintal",
          price: `₹${res.current_price_per_quintal.toLocaleString()}`,
          change: res.market_trend?.percentage_change ? `${trendIcon === 'up' ? '+' : trendIcon === 'down' ? '-' : ''}${res.market_trend.percentage_change}%` : "Stable",
          trend: trendIcon
        };
      });
      setMarketData(validData);
      setLoading(false);
    });
  }, [trackedCrops, stateName, authFetch]);

  const toggleCrop = (crop) => {
    if (trackedCrops.includes(crop)) {
      setTrackedCrops(prev => prev.filter(c => c !== crop));
    } else {
      if (trackedCrops.length < 5) {
        setTrackedCrops(prev => [...prev, crop]);
      }
    }
  };

  return (
    <div className="widget-card">
      <div className="widget-header">
        <div className="widget-title">
          <BarChart2 size={12} />
          Market Prices
        </div>
        <button 
          className="widget-action" 
          onClick={() => setIsEditing(!isEditing)}
          style={{ background: 'none', border: 'none', color: 'var(--accent-green)', cursor: 'pointer' }}
        >
          {isEditing ? 'Done' : 'Edit'}
        </button>
      </div>

      {isEditing && (
        <div style={{ padding: '0 16px 12px', display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          <div style={{ width: '100%', fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>
            Select up to 5 crops to track:
          </div>
          {supportedCrops.map(crop => {
            const isTracked = trackedCrops.includes(crop);
            const isDisabled = !isTracked && trackedCrops.length >= 5;
            return (
              <button
                key={crop}
                onClick={() => toggleCrop(crop)}
                disabled={isDisabled}
                style={{
                  padding: '4px 8px', fontSize: 11, borderRadius: 12,
                  border: `1px solid ${isTracked ? 'var(--accent-green)' : 'var(--border-subtle)'}`,
                  background: isTracked ? 'rgba(34,197,94,0.1)' : 'transparent',
                  color: isTracked ? 'var(--accent-green)' : (isDisabled ? 'var(--text-muted)' : 'var(--text-primary)'),
                  cursor: isDisabled ? 'not-allowed' : 'pointer',
                  display: 'flex', alignItems: 'center', gap: 4,
                  opacity: isDisabled ? 0.5 : 1
                }}
              >
                {CROP_EMOJIS[crop] || "🌱"} {crop}
                {isTracked && <X size={10} />}
              </button>
            );
          })}
        </div>
      )}

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, color: 'var(--text-muted)' }}>
          <Loader2 size={20} className="animate-spin" style={{ marginRight: 8 }} />
          Loading prices...
        </div>
      ) : marketData.length === 0 ? (
        <div style={{ padding: 20, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
          No crops selected. Click Edit to add crops.
        </div>
      ) : (
        <div className="market-table">
          {marketData.map((item) => (
            <div className="market-row" key={item.name}>
              <div className="market-crop">
                <div className="crop-icon">{item.crop}</div>
                <div>
                  <div className="crop-name">{item.name}</div>
                  <div className="crop-unit">{item.unit}</div>
                </div>
              </div>
              <div className="market-price-info">
                <div className="market-price">{item.price}</div>
                <div className={`market-change ${item.trend}`}>
                  {item.trend === "up" && <TrendingUp size={10} style={{ display: 'inline', marginRight: 2 }} />}
                  {item.trend === "down" && <TrendingDown size={10} style={{ display: 'inline', marginRight: 2 }} />}
                  {item.trend === "stable" && <Minus size={10} style={{ display: 'inline', marginRight: 2 }} />}
                  {item.change}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
