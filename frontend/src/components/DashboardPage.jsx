import { MessageSquare, CloudSun, BarChart2, Sprout, Sparkles } from 'lucide-react';
import WeatherWidget from './WeatherWidget';
import MarketPricesWidget from './MarketPricesWidget';

export default function DashboardPage({ setActiveTab, location }) {
  // A dynamic briefing that could eventually be tied to backend logic
  const morningBriefing = "Rain expected tomorrow afternoon. Market prices for Wheat are rising. Good time to review your selling strategy.";

  const actionCards = [
    { id: 'chat', title: 'Ask AI Assistant', desc: 'Get crop advice', icon: MessageSquare, color: 'var(--accent-green)' },
    { id: 'weather', title: 'Check Weather', desc: "Today's forecast", icon: CloudSun, color: 'var(--accent-blue)' },
    { id: 'market', title: 'Market Prices', desc: 'Live APMC rates', icon: BarChart2, color: 'var(--text-primary)' },
    { id: 'crops', title: 'Crop Advisor', desc: 'Planting guide', icon: Sprout, color: 'var(--text-primary)' }
  ];

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: '24px 32px', display: 'flex', flexDirection: 'column', gap: 24 }}>
      
      {/* Header & AI Briefing */}
      <div>
        <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 10 }}>
          👋 Good Evening, Raj
        </div>
        <div style={{ 
          display: 'flex', alignItems: 'flex-start', gap: 12, padding: 16, 
          background: 'rgba(34,197,94,0.05)', border: '1px solid rgba(34,197,94,0.2)', 
          borderRadius: 'var(--radius-md)'
        }}>
          <Sparkles size={20} color="var(--accent-green)" style={{ flexShrink: 0, marginTop: 2 }} />
          <div style={{ fontSize: 14, color: 'var(--text-muted)', lineHeight: 1.5 }}>
            <span style={{ fontWeight: 600, color: 'var(--text-primary)', marginRight: 6 }}>AI Briefing:</span>
            {morningBriefing}
          </div>
        </div>
      </div>

      {/* Quick Action Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
        {actionCards.map(card => (
          <div 
            key={card.id}
            onClick={() => setActiveTab(card.id)}
            style={{
              background: 'var(--bg-card)', 
              borderRadius: 'var(--radius-md)', 
              padding: 20, 
              display: 'flex', flexDirection: 'column', gap: 12,
              border: '1px solid var(--border-subtle)',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.borderColor = card.color;
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.borderColor = 'var(--border-subtle)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div style={{ 
              width: 40, height: 40, borderRadius: '50%', background: 'var(--bg-input)', 
              display: 'flex', alignItems: 'center', justifyContent: 'center' 
            }}>
              <card.icon size={20} color={card.color} />
            </div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>{card.title}</div>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{card.desc}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Main Widgets Area */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, flex: 1, minHeight: 0 }}>
        {/* Left Side: Weather (Dominant) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <h3 style={{ fontSize: 16, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            <CloudSun size={18} color="var(--accent-blue)" /> Local Conditions
          </h3>
          <WeatherWidget location={location} />
        </div>

        {/* Right Side: Market Prices */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <h3 style={{ fontSize: 16, color: 'var(--text-primary)', margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
            <BarChart2 size={18} color="var(--accent-green)" /> Market Overview
          </h3>
          <MarketPricesWidget location={location} />
        </div>
      </div>
      
    </div>
  );
}
