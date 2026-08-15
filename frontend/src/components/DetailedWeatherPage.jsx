import { useState, useEffect } from 'react';
import { Loader2, CloudSun, CloudRain, Sun, Cloud, Wind, Droplets, Thermometer, AlertTriangle, CheckCircle, Info, Beaker, Sprout } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function DetailedWeatherPage({ location }) {
  const { authFetch } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const stateName = location ? location.split(',').pop().trim() : "Maharashtra";

  useEffect(() => {
    setLoading(true);
    setError(null);
    authFetch(`http://localhost:8000/api/v1/weather/${encodeURIComponent(stateName)}`)
      .then(res => res.json())
      .then(json => {
        if (json.success) {
          setData(json);
        } else {
          setError(json.detail || "Failed to load weather data");
        }
      })
      .catch(err => {
        console.error("Weather fetch error:", err);
        setError("Network error loading weather data.");
      })
      .finally(() => setLoading(false));
  }, [stateName, authFetch]);

  const getWeatherIcon = (conditions, size = 24) => {
    const c = conditions?.toLowerCase() || '';
    if (c.includes('rain')) return <CloudRain size={size} color="var(--accent-blue)" />;
    if (c.includes('cloud')) return <Cloud size={size} color="var(--text-muted)" />;
    if (c.includes('clear') || c.includes('sun')) return <Sun size={size} color="#FBBF24" />;
    return <CloudSun size={size} color="var(--text-primary)" />;
  };

  if (loading) {
    return (
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
        <Loader2 size={32} className="animate-spin" style={{ marginBottom: 16 }} />
        <div>Analyzing meteorological and agronomy data...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-red)' }}>
        <AlertTriangle size={24} style={{ marginRight: 8 }} />
        {error || "No data available."}
      </div>
    );
  }

  const { agricultural_params = {}, forecast = [], alerts = [], recommendations = [] } = data;

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 24, minHeight: 0 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <CloudSun size={24} color="var(--accent-blue)" />
            Weather & Agronomy Intelligence
          </h2>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
            Live meteorological data and farming conditions for {data.location}
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)' }}>{data.current_temperature}°C</div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{data.current_conditions}</div>
          </div>
          {getWeatherIcon(data.current_conditions, 40)}
        </div>
      </div>

      {/* Advanced Metrics (Option 1 Style) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 16 }}>
        <div style={{ background: 'var(--bg-card)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: 13, fontWeight: 600, textTransform: 'uppercase' }}>
            <span>Delta-T (Spray)</span>
            <Beaker size={16} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 28, fontWeight: 700, color: agricultural_params.spray_suitability === 'Optimal' ? 'var(--accent-green)' : 'var(--text-primary)' }}>
              {agricultural_params.delta_t || 'N/A'}
            </span>
          </div>
          <div style={{ fontSize: 13, color: agricultural_params.spray_suitability === 'Optimal' ? 'var(--accent-green)' : 'var(--text-muted)' }}>
            {agricultural_params.spray_suitability || 'Unknown'} for spraying
          </div>
        </div>

        <div style={{ background: 'var(--bg-card)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: 13, fontWeight: 600, textTransform: 'uppercase' }}>
            <span>Evapotranspiration</span>
            <Wind size={16} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 28, fontWeight: 700, color: 'var(--accent-blue)' }}>
              {agricultural_params.evapotranspiration || '0'}mm
            </span>
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            Water loss rate — Plan irrigation
          </div>
        </div>

        <div style={{ background: 'var(--bg-card)', padding: 16, borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: 13, fontWeight: 600, textTransform: 'uppercase' }}>
            <span>Soil Moisture</span>
            <Droplets size={16} />
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
            <span style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)' }}>
              {agricultural_params.soil_moisture_0_10cm || '0'}%
            </span>
          </div>
          <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
            Topsoil (0-10cm) capacity
          </div>
        </div>
      </div>

      {/* 7-Day Farm Forecast */}
      <div>
        <h3 style={{ fontSize: 16, color: 'var(--text-primary)', marginBottom: 16 }}>7-Day Farm Forecast</h3>
        <div style={{ display: 'flex', gap: 12, overflowX: 'auto', paddingBottom: 8, scrollbarWidth: 'thin' }}>
          {forecast.map((day, idx) => {
            const dateObj = new Date(day.date);
            const dayName = dateObj.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase();
            const dayNum = dateObj.getDate();
            const isToday = idx === 0;

            return (
              <div key={idx} style={{ 
                minWidth: 110, 
                background: isToday ? 'var(--bg-input)' : 'var(--bg-card)', 
                border: isToday ? '1px solid var(--accent-green)' : '1px solid var(--border-subtle)',
                borderRadius: 'var(--radius-md)',
                padding: '16px 12px',
                display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12,
                boxShadow: isToday ? '0 0 10px rgba(34,197,94,0.1)' : 'none'
              }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600 }}>{dayName}</div>
                  <div style={{ fontSize: 18, color: 'var(--text-primary)', fontWeight: 700 }}>{dayNum}</div>
                </div>
                
                {getWeatherIcon(day.conditions, 32)}
                
                <div style={{ fontSize: 11, color: 'var(--text-muted)', textAlign: 'center', height: 28, display: 'flex', alignItems: 'center' }}>
                  {day.conditions}
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14 }}>
                  <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{day.temp_max}°</span>
                  <span style={{ color: 'var(--text-muted)' }}>{day.temp_min}°</span>
                </div>
                
                <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11, color: 'var(--accent-blue)', background: 'rgba(59,130,246,0.1)', padding: '2px 8px', borderRadius: 10 }}>
                  <Droplets size={10} /> {day.rainfall}mm
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Alerts and Recommendations */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 20 }}>
        
        {/* Alerts */}
        <div style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', padding: 20 }}>
          <h3 style={{ fontSize: 16, color: 'var(--text-primary)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={18} color="var(--accent-red)" />
            Active Weather Alerts
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {alerts.length > 0 ? alerts.map((alert, idx) => (
              <div key={idx} style={{ padding: 12, background: 'rgba(239,68,68,0.1)', borderLeft: '3px solid var(--accent-red)', borderRadius: '0 var(--radius-sm) var(--radius-sm) 0' }}>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 14, marginBottom: 4 }}>{alert.type}</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.4 }}>{alert.message}</div>
                {alert.crop_impact && (
                  <div style={{ fontSize: 12, color: 'var(--accent-red)', marginTop: 8, display: 'flex', alignItems: 'center', gap: 4 }}>
                    <Sprout size={12} /> Impact: {alert.crop_impact}
                  </div>
                )}
              </div>
            )) : (
              <div style={{ padding: 16, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13, background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
                No active severe weather alerts for your area.
              </div>
            )}
          </div>
        </div>

        {/* Recommendations */}
        <div style={{ background: 'var(--bg-card)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)', padding: 20 }}>
          <h3 style={{ fontSize: 16, color: 'var(--text-primary)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <CheckCircle size={18} color="var(--accent-green)" />
            Farming Advisory
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {recommendations.length > 0 ? recommendations.map((rec, idx) => (
              <div key={idx} style={{ padding: 12, background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: 14 }}>{rec.category.toUpperCase()}</div>
                  <div style={{ fontSize: 10, padding: '2px 6px', borderRadius: 4, background: rec.priority === 'high' ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.2)', color: rec.priority === 'high' ? 'var(--accent-red)' : 'var(--accent-green)', textTransform: 'uppercase', fontWeight: 700 }}>
                    {rec.priority}
                  </div>
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.4 }}>{rec.message}</div>
              </div>
            )) : (
              <div style={{ padding: 16, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13, background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
                No specific agronomy recommendations at this time.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
