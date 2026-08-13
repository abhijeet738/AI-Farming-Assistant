import { TrendingUp, TrendingDown, Minus, BarChart2 } from 'lucide-react';

const marketData = [
  { crop: "🌾", name: "Wheat", unit: "per quintal", price: "₹2,450", change: "+1.2%", trend: "up" },
  { crop: "🍅", name: "Tomato", unit: "per kg", price: "₹45", change: "-0.8%", trend: "down" },
  { crop: "🌽", name: "Maize", unit: "per quintal", price: "₹2,180", change: "+0.5%", trend: "up" },
  { crop: "🧅", name: "Onion", unit: "per kg", price: "₹32", change: "Stable", trend: "stable" },
  { crop: "🌿", name: "Soybean", unit: "per quintal", price: "₹5,380", change: "+2.3%", trend: "up" },
];

export default function MarketPricesWidget() {
  return (
    <div className="widget-card">
      <div className="widget-header">
        <div className="widget-title">
          <BarChart2 size={12} />
          Market Prices
        </div>
        <span className="widget-action">APMC</span>
      </div>

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
    </div>
  );
}
