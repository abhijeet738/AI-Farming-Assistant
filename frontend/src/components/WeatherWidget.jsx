import { Leaf, MapPin, Wind, Droplets } from 'lucide-react';

const weatherData = {
  city: "Pune, Maharashtra",
  temp: "26°C",
  feelsLike: "24°C",
  condition: "Partly Cloudy",
  icon: "⛅",
  humidity: "65%",
  wind: "12 km/h",
  forecast: [
    { day: "Mon", icon: "⛅", high: "28°", low: "19°" },
    { day: "Tue", icon: "🌧️", high: "25°", low: "18°" },
    { day: "Wed", icon: "🌧️", high: "24°", low: "17°" },
    { day: "Thu", icon: "🌤️", high: "29°", low: "20°" },
  ],
};

export default function WeatherWidget() {
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
        {weatherData.city}
      </div>

      <div className="weather-main">
        <div>
          <div className="weather-temp">{weatherData.temp}</div>
          <div className="weather-desc">{weatherData.condition} · Feels {weatherData.feelsLike}</div>
        </div>
        <div className="weather-icon-wrap">{weatherData.icon}</div>
      </div>

      <div className="weather-stats">
        <div className="weather-stat">
          <div className="weather-stat-label">
            <Droplets size={10} style={{ display: 'inline', marginRight: 4 }} />
            Humidity
          </div>
          <div className="weather-stat-value">{weatherData.humidity}</div>
        </div>
        <div className="weather-stat">
          <div className="weather-stat-label">
            <Wind size={10} style={{ display: 'inline', marginRight: 4 }} />
            Wind
          </div>
          <div className="weather-stat-value">{weatherData.wind}</div>
        </div>
      </div>

      <div className="weather-forecast">
        {weatherData.forecast.map((day) => (
          <div className="forecast-day" key={day.day}>
            <div className="forecast-day-name">{day.day}</div>
            <div className="forecast-icon">{day.icon}</div>
            <div className="forecast-temp">{day.high}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
