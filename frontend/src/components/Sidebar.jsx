import { useState, useEffect } from 'react';
import { Home, MessageSquare, Sprout, CloudSun, ShoppingCart, BarChart2, Settings, Plus, ChevronRight, MessageCircle, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

import { TrendingUp, Bug } from 'lucide-react';

const navItems = [
  { icon: Home, label: "Dashboard", id: "dashboard" },
  { icon: MessageSquare, label: "Chat Assistant", id: "chat" },
  { icon: Sprout, label: "Crop Advisor", id: "crops" },
  { icon: TrendingUp, label: "Yield Predictor", id: "yield" },
  { icon: Bug, label: "Pest Risk", id: "pest" },
  { icon: CloudSun, label: "Weather", id: "weather" },
  { icon: ShoppingCart, label: "Market Prices", id: "market" },
];

const chatHistory = [
  "What should I plant this season...",
  "Disease in my tomato crop?",
  "Best fertilizer for wheat?",
];

export default function Sidebar({ activeTab, setActiveTab, onNewChat, activeThreadId, setActiveThreadId }) {
  const { authFetch, user, logout } = useAuth();
  const [sessions, setSessions] = useState([]);

  // Fetch chat sessions when Sidebar mounts or when active thread changes
  useEffect(() => {
    authFetch('http://localhost:8000/api/v1/chat/sessions')
      .then(res => res.json())
      .then(data => Array.isArray(data) ? setSessions(data) : setSessions([]))
      .catch(err => console.error("Failed to load chat sessions:", err));
  }, [activeTab, activeThreadId, authFetch]);

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
        {sessions.map((session) => (
          <div 
            key={session.id} 
            className={`chat-history-item ${activeThreadId === session.thread_id ? 'active' : ''}`}
            onClick={() => {
              setActiveThreadId(session.thread_id);
              setActiveTab('chat');
            }}
            title={session.title}
          >
            <MessageCircle size={14} style={{ minWidth: 14 }} />
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {session.title || "New Conversation"}
            </span>
          </div>
        ))}
        {sessions.length === 0 && (
          <div style={{ fontSize: 12, color: 'var(--text-muted)', padding: '0 12px' }}>
            No recent chats
          </div>
        )}
      </div>

      {/* User Profile */}
      <div className="sidebar-footer">
        <div className="user-avatar">
          {user?.email ? user.email.slice(0, 2).toUpperCase() : 'KM'}
        </div>
        <div className="user-info">
          <div className="user-name">{user?.email?.split('@')[0] || 'Farmer'}</div>
          <div className="user-role">{user?.email || 'Logged in'}</div>
        </div>
        <button
          onClick={logout}
          title="Logout"
          style={{ background: 'none', border: 'none', cursor: 'pointer',
            color: 'var(--text-muted)', marginLeft: 'auto', padding: 4 }}
        >
          <LogOut size={14} />
        </button>
      </div>
    </aside>
  );
}
