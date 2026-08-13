import { Home, MessageSquare, Sprout, CloudSun, ShoppingCart, BarChart2, Settings, Plus, ChevronRight } from 'lucide-react';

const navItems = [
  { icon: Home, label: "Dashboard", id: "dashboard" },
  { icon: MessageSquare, label: "Chat Assistant", id: "chat" },
  { icon: Sprout, label: "Crop Advisor", id: "crops" },
  { icon: CloudSun, label: "Weather", id: "weather" },
  { icon: ShoppingCart, label: "Market Prices", id: "market" },
  { icon: BarChart2, label: "Analytics", id: "analytics" },
  { icon: Settings, label: "Settings", id: "settings" },
];

const chatHistory = [
  "What should I plant this season...",
  "Disease in my tomato crop?",
  "Best fertilizer for wheat?",
];

export default function Sidebar({ activeTab, setActiveTab, onNewChat }) {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-header">
        <div className="logo-icon">
          <Sprout size={18} color="white" />
        </div>
        <div>
          <div className="logo-title">Krishi Mitra</div>
          <div className="logo-subtitle">AI Farming Assistant</div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="nav-label">Main Menu</div>
        {navItems.map((item) => (
          <button
            key={item.id}
            className={`nav-item ${activeTab === item.id ? "active" : ""}`}
            onClick={() => setActiveTab(item.id)}
          >
            <item.icon size={16} />
            {item.label}
          </button>
        ))}
      </nav>

      {/* Chat history + New Chat */}
      <div className="sidebar-chat-history">
        <button className="new-chat-btn" onClick={onNewChat}>
          <Plus size={14} />
          New Chat
        </button>
        <div className="nav-label">Recent Chats</div>
        {chatHistory.map((chat, i) => (
          <div key={i} className="chat-history-item">{chat}</div>
        ))}
      </div>

      {/* User Profile */}
      <div className="sidebar-footer">
        <div className="user-avatar">RS</div>
        <div className="user-info">
          <div className="user-name">Raj Singh</div>
          <div className="user-role">Farmer · Pune</div>
        </div>
        <ChevronRight size={14} style={{ color: 'var(--text-muted)', marginLeft: 'auto' }} />
      </div>
    </aside>
  );
}
