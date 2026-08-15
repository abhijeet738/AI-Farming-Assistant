import { useState } from 'react';
import { Bell, Search, Sprout, MapPin, BarChart2, CloudSun, Home, MessageSquare, LogOut } from 'lucide-react';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import WeatherWidget from './components/WeatherWidget';
import MarketPricesWidget from './components/MarketPricesWidget';
import DetailedMarketPage from './components/DetailedMarketPage';
import DetailedWeatherPage from './components/DetailedWeatherPage';
import DetailedCropPage from './components/DetailedCropPage';
import DetailedYieldPage from './components/DetailedYieldPage';
import DetailedPestPage from './components/DetailedPestPage';
import DashboardPage from './components/DashboardPage';
import LoginPage from './components/LoginPage';
import { AuthProvider, useAuth } from './context/AuthContext';

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

const LOCATIONS = [
  "Pune, Maharashtra",
  "Ballia, Uttar Pradesh",
  "Ludhiana, Punjab",
  "Patna, Bihar",
  "Nasik, Maharashtra",
];

// ─── Main App (inner — needs AuthContext) ────────────────────────────────────
function AppInner() {
  const { isAuthenticated, user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  const [activeThreadId, setActiveThreadId] = useState(null);
  const [chatKey, setChatKey] = useState(0);
  const [selectedLocation, setSelectedLocation] = useState("Ballia, Uttar Pradesh");
  const [locationInput, setLocationInput] = useState(selectedLocation);

  if (!isAuthenticated) return <LoginPage />;

  const handleNewChat = () => {
    setActiveTab('chat');
    setActiveThreadId(null);
    setChatKey(prev => prev + 1);
  };

  const { label: tabLabel, icon: TabIcon } = tabConfig[activeTab] || tabConfig.chat;

  // Decide which main view to render
  const renderMainView = () => {
    switch (activeTab) {
      case 'dashboard': return <DashboardPage setActiveTab={setActiveTab} location={selectedLocation} />;
      case 'chat':      return <ChatWindow key={chatKey} activeThreadId={activeThreadId} setActiveThreadId={setActiveThreadId} />;
      case 'weather':   return <DetailedWeatherPage location={selectedLocation} />;
      case 'market':    return <DetailedMarketPage location={selectedLocation} />;
      case 'crops':     return <DetailedCropPage location={selectedLocation} />;
      case 'yield':     return <DetailedYieldPage location={selectedLocation} />;
      case 'pest':      return <DetailedPestPage location={selectedLocation} />;
      default:
        return <ChatWindow key={chatKey} activeThreadId={activeThreadId} setActiveThreadId={setActiveThreadId} />;
    }
  };

  // Show right panel only on chat page
  const showRightPanel = activeTab === 'chat';

  return (
    <div className="app-layout">
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        onNewChat={handleNewChat}
        activeThreadId={activeThreadId}
        setActiveThreadId={setActiveThreadId}
      />

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
              <input 
                type="text"
                value={locationInput}
                onChange={e => setLocationInput(e.target.value)}
                onBlur={() => setSelectedLocation(locationInput)}
                onKeyDown={e => {
                  if (e.key === 'Enter') {
                    setSelectedLocation(locationInput);
                    e.target.blur();
                  }
                }}
                style={{ background: 'transparent', border: 'none', color: 'inherit', outline: 'none', cursor: 'text', width: 140 }}
                placeholder="City, State"
              />
            </div>
            {user?.email && (
              <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: '4px 10px',
                background: 'var(--bg-input)', borderRadius: 'var(--radius-full)', border: '1px solid var(--border-subtle)' }}>
                {user.email}
              </div>
            )}
            <button className="icon-btn" title="Search"><Search size={15} /></button>
            <button className="icon-btn" title="Notifications"><Bell size={15} /></button>
            <button
              className="icon-btn"
              title="Logout"
              onClick={logout}
              style={{ color: 'var(--text-muted)' }}
            >
              <LogOut size={15} />
            </button>
          </div>
        </header>

        {/* Content Area */}
        <div className="content-area">
          {renderMainView()}

          {/* Right panel — only shown on chat tab */}
          {showRightPanel && (
            <aside className="right-panel">
              <WeatherWidget location={selectedLocation} />
              <MarketPricesWidget location={selectedLocation} />
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

// ─── Root export wrapped in AuthProvider ─────────────────────────────────────
export default function App() {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
}
