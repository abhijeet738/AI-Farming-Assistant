import { useState, useEffect } from 'react';
import { Leaf, MapPin, Wind, Droplets } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const conditionToIcon = (condition) => {
  const lower = condition?.toLowerCase() || '';
  if (lower.includes('rain') || lower.includes('shower')) return '🌧️';
  if (lower.includes('cloud')) return '⛅';
  if (lower.includes('clear') || lower.includes('sun')) return '☀️';
  if (lower.includes('storm')) return '⛈️';
  return '🌤️';
};

const getDayName = (dateStr) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { weekday: 'short' });
};

export default function WeatherWidget({ location }) {
  const { authFetch } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!location) return;
    setLoading(true);
    authFetch(`http://localhost:8000/api/v1/weather/${encodeURIComponent(location)}`)
      .then(res => res.json())
      .then(json => {
        if (json.success) setData(json);
      })
      .catch(err => console.error("Weather fetch failed:", err))
      .finally(() => setLoading(false));
  }, [location, authFetch]);

  if (loading) {
    return (
      <div className="widget-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 250 }}>
        <div style={{ color: 'var(--text-muted)' }}>Loading weather...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="widget-card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 250 }}>
        <div style={{ color: 'var(--text-muted)' }}>Failed to load weather</div>
      </div>
    );
  }

  const currentIcon = conditionToIcon(data.current_conditions);
  const displayLocation = data.location.split(',').slice(0, 2).join(',');

  return (
    <div className="widget-card">
      <div className="widget-header">
        <div className="widget-title">
          <Leaf size={12} />
          Weather Update
        </div>
        <span className="widget-action">Details</span>
      </div>

      <div className="weather-location">
        <MapPin size={11} />
        {displayLocation}
      </div>

      <div className="weather-main">
        <div>
          <div className="weather-temp">{Math.round(data.current_temperature)}°C</div>
          <div className="weather-desc">{data.current_conditions}</div>
        </div>
        <div className="weather-icon-wrap">{currentIcon}</div>
      </div>

      <div className="weather-stats">
        <div className="weather-stat">
          <div className="weather-stat-label">
            <Droplets size={10} style={{ display: 'inline', marginRight: 4 }} />
            Humidity
          </div>
          <div className="weather-stat-value">{data.current_humidity}%</div>
        </div>
        <div className="weather-stat">
          <div className="weather-stat-label">
            <Wind size={10} style={{ display: 'inline', marginRight: 4 }} />
            Wind
          </div>
          <div className="weather-stat-value">{Math.round(data.forecast[0]?.wind_speed || 0)} km/h</div>
        </div>
      </div>

      <div className="weather-forecast">
        {data.forecast.slice(1, 5).map((day) => (
          <div className="forecast-day" key={day.date}>
            <div className="forecast-day-name">{getDayName(day.date)}</div>
            <div className="forecast-icon">{conditionToIcon(day.conditions)}</div>
            <div className="forecast-temp">{Math.round(day.temp_max)}°</div>
          </div>
        ))}
      </div>
    </div>
  );
}
