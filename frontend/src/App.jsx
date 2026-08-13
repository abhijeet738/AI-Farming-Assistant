import { useState } from 'react';
import { Bell, Search, Sprout, MapPin, BarChart2, CloudSun, Home, MessageSquare } from 'lucide-react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import WeatherWidget from './components/WeatherWidget';
import MarketPricesWidget from './components/MarketPricesWidget';

// ─── Placeholder views for non-chat tabs ─────────────────────────────────────
function ComingSoonView({ icon: Icon, title, description }) {
  return (
    <div style={{
      flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center',
      justifyContent: 'center', gap: 16, padding: 40, textAlign: 'center'
    }}>
      <div style={{
        width: 64, height: 64, borderRadius: 16,
        background: 'var(--accent-green-glow)',
        border: '1px solid rgba(34,197,94,0.2)',
        display: 'flex', alignItems: 'center', justifyContent: 'center'
      }}>
        <Icon size={28} color="var(--accent-green)" />
      </div>
      <div style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)' }}>{title}</div>
      <div style={{ fontSize: 14, color: 'var(--text-muted)', maxWidth: 320, lineHeight: 1.6 }}>{description}</div>
      <div style={{
        padding: '8px 20px', background: 'var(--bg-card)',
        border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-full)',
        fontSize: 12, color: 'var(--text-muted)'
      }}>
        🚧 Coming Soon
      </div>
    </div>
  );
}

// ─── Full Weather page ────────────────────────────────────────────────────────
function WeatherPage() {
  return (
    <div style={{ flex: 1, overflow: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
        🌤️ Weather Intelligence
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        <WeatherWidget />
        <div className="widget-card">
          <div className="widget-header">
            <div className="widget-title"><CloudSun size={12} />Farming Advisory</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { icon: '💧', title: 'Irrigation Needed', desc: 'Low rainfall expected. Irrigate within 2 days.' },
              { icon: '🌱', title: 'Good for Planting', desc: 'Soil moisture and temp optimal for sowing.' },
              { icon: '⚠️', title: 'Frost Warning', desc: 'Protect crops Thu night — temp drops to 4°C.' },
            ].map(item => (
              <div key={item.title} style={{
                background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)',
                padding: '10px 12px', display: 'flex', gap: 10, alignItems: 'flex-start'
              }}>
                <span style={{ fontSize: 18 }}>{item.icon}</span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{item.title}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Full Market Prices page ──────────────────────────────────────────────────
function MarketPage() {
  return (
    <div style={{ flex: 1, overflow: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
        📊 Market Prices — APMC Maharashtra
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        <MarketPricesWidget />
        <div className="widget-card">
          <div className="widget-header">
            <div className="widget-title"><BarChart2 size={12} />Price Trends</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[
              { crop: '🌾', name: 'Wheat', insight: 'Prices rising 1.2% this week. Good time to sell.' },
              { crop: '🍅', name: 'Tomato', insight: 'Oversupply in Pune APMC. Hold if possible.' },
              { crop: '🧅', name: 'Onion', insight: 'Stable prices expected for next 2 weeks.' },
            ].map(item => (
              <div key={item.name} style={{
                background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)',
                padding: '10px 12px', display: 'flex', gap: 10, alignItems: 'flex-start'
              }}>
                <span style={{ fontSize: 20 }}>{item.crop}</span>
                <div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{item.name}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item.insight}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Dashboard Overview page ──────────────────────────────────────────────────
function DashboardPage({ setActiveTab }) {
  return (
    <div style={{ flex: 1, overflow: 'auto', padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={{ fontSize: 16, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
        👋 Good Evening, Raj Singh
      </div>

      {/* Quick Action Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
        {[
          { icon: '💬', label: 'Ask AI Assistant', desc: 'Get crop advice', tab: 'chat', color: 'var(--accent-green)' },
          { icon: '🌤️', label: 'Check Weather', desc: 'Today\'s forecast', tab: 'weather', color: 'var(--accent-blue)' },
          { icon: '📊', label: 'Market Prices', desc: 'Live APMC rates', tab: 'market', color: '#f59e0b' },
          { icon: '🌿', label: 'Crop Advisor', desc: 'Planting guide', tab: 'crops', color: '#a78bfa' },
        ].map(card => (
          <button
            key={card.tab}
            onClick={() => setActiveTab(card.tab)}
            style={{
              background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-md)', padding: '16px',
              cursor: 'pointer', textAlign: 'left', transition: 'var(--transition)',
              display: 'flex', flexDirection: 'column', gap: 8,
            }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = card.color; e.currentTarget.style.background = 'var(--bg-hover)'; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--border-subtle)'; e.currentTarget.style.background = 'var(--bg-card)'; }}
          >
            <span style={{ fontSize: 28 }}>{card.icon}</span>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{card.label}</div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{card.desc}</div>
          </button>
        ))}
      </div>

      {/* Widgets Row */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <WeatherWidget />
        <MarketPricesWidget />
      </div>
    </div>
  );
}

// ─── Tab title map ────────────────────────────────────────────────────────────
const tabConfig = {
  dashboard:  { label: 'Dashboard',      icon: Home },
  chat:       { label: 'Chat Assistant', icon: MessageSquare },
  crops:      { label: 'Crop Advisor',   icon: Sprout },
  weather:    { label: 'Weather',        icon: CloudSun },
  market:     { label: 'Market Prices',  icon: BarChart2 },
  analytics:  { label: 'Analytics',      icon: BarChart2 },
  settings:   { label: 'Settings',       icon: Sprout },
};

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [chatKey, setChatKey] = useState(0);

  const handleNewChat = () => {
    setActiveTab('chat');
    setChatKey(prev => prev + 1);
  };

  const { label: tabLabel, icon: TabIcon } = tabConfig[activeTab] || tabConfig.chat;

  // Decide which main view to render
  const renderMainView = () => {
    switch (activeTab) {
      case 'dashboard': return <DashboardPage setActiveTab={setActiveTab} />;
      case 'chat':      return <ChatWindow key={chatKey} />;
      case 'weather':   return <WeatherPage />;
      case 'market':    return <MarketPage />;
      case 'crops':
        return <ComingSoonView icon={Sprout} title="Crop Advisor" description="Get AI-powered crop recommendations based on your soil type, region, and season. Coming soon!" />;
      case 'analytics':
        return <ComingSoonView icon={BarChart2} title="Analytics" description="Track your farm yield, expenses, and AI conversation history over time. Coming soon!" />;
      case 'settings':
        return <ComingSoonView icon={Sprout} title="Settings" description="Configure your farm profile, language, location, and notification preferences. Coming soon!" />;
      default:
        return <ChatWindow key={chatKey} />;
    }
  };

  // Show right panel only on chat page
  const showRightPanel = activeTab === 'chat';

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} onNewChat={handleNewChat} />

      <div className="main-content">
        {/* Top Bar */}
        <header className="topbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div className="topbar-title">
              <TabIcon size={16} color="var(--accent-green)" />
              {tabLabel}
            </div>
            {activeTab === 'chat' && (
              <div className="topbar-status">
                <span className="status-dot" />
                AI Online
              </div>
            )}
          </div>

          <div className="topbar-actions">
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text-muted)' }}>
              <MapPin size={12} />
              Pune, MH
            </div>
            <button className="icon-btn" title="Search"><Search size={15} /></button>
            <button className="icon-btn" title="Notifications"><Bell size={15} /></button>
          </div>
        </header>

        {/* Content Area */}
        <div className="content-area">
          {renderMainView()}

          {/* Right panel — only shown on chat tab */}
          {showRightPanel && (
            <aside className="right-panel">
              <WeatherWidget />
              <MarketPricesWidget />
              <div className="widget-card">
                <div className="widget-header">
                  <div className="widget-title"><Sprout size={12} />Farm Profile</div>
                </div>
                <div className="farm-stats">
                  {[
                    { label: 'Farm Size', value: '2.5 ha', sub: 'Pune District' },
                    { label: 'Current Crop', value: 'Wheat', sub: 'Rabi Season' },
                    { label: 'Soil Type', value: 'Black', sub: 'pH 6.8' },
                    { label: 'Next Harvest', value: '~42 days', sub: 'Estimated' },
                  ].map(s => (
                    <div className="farm-stat" key={s.label}>
                      <div className="farm-stat-label">{s.label}</div>
                      <div className="farm-stat-value">{s.value}</div>
                      <div className="farm-stat-sub">{s.sub}</div>
                    </div>
                  ))}
                </div>
              </div>
            </aside>
          )}
        </div>
      </div>
    </div>
  );
}
