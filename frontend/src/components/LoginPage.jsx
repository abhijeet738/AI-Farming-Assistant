import { useState } from 'react';
import { Sprout, Mail, Lock, User, ArrowRight, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
  const { login, register, loading, error } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [notice, setNotice] = useState(null); // { type: 'success'|'error', msg }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setNotice(null);

    if (mode === 'login') {
      const res = await login(email, password);
      if (!res.success) setNotice({ type: 'error', msg: res.error });
    } else {
      const res = await register(email, password, name);
      if (res.success && res.requiresConfirmation) {
        setNotice({ type: 'success', msg: 'Check your email for a confirmation link before logging in.' });
        setMode('login');
      } else if (!res.success) {
        setNotice({ type: 'error', msg: res.error });
      }
    }
  };

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center',
      background: 'var(--bg-primary)', padding: 24,
    }}>
      {/* Background glow */}
      <div style={{
        position: 'fixed', top: '20%', left: '50%', transform: 'translateX(-50%)',
        width: 600, height: 600, borderRadius: '50%',
        background: 'radial-gradient(circle, rgba(34,197,94,0.08) 0%, transparent 70%)',
        pointerEvents: 'none', zIndex: 0,
      }} />

      <div style={{
        position: 'relative', zIndex: 1, width: '100%', maxWidth: 420,
        background: 'var(--bg-card)', border: '1px solid var(--border-subtle)',
        borderRadius: 20, padding: 40, boxShadow: '0 24px 64px rgba(0,0,0,0.4)',
      }}>
        {/* Logo */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, marginBottom: 36 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 16, display: 'flex', alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #16a34a, #22c55e)',
            boxShadow: '0 8px 24px rgba(34,197,94,0.35)',
          }}>
            <Sprout size={28} color="white" />
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 22, fontWeight: 800, color: 'var(--text-primary)', letterSpacing: '-0.5px' }}>
              Krishi Mitra
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>
              AI Farming Assistant
            </div>
          </div>
        </div>

        {/* Mode Tabs */}
        <div style={{
          display: 'flex', background: 'var(--bg-input)', borderRadius: 10,
          padding: 4, marginBottom: 28, gap: 4,
        }}>
          {['login', 'register'].map(m => (
            <button key={m} onClick={() => { setMode(m); setNotice(null); }} style={{
              flex: 1, padding: '9px 0', borderRadius: 8, border: 'none', cursor: 'pointer',
              fontSize: 13, fontWeight: 600, transition: 'all 0.2s',
              background: mode === m ? 'var(--bg-card)' : 'transparent',
              color: mode === m ? 'var(--accent-green)' : 'var(--text-muted)',
              boxShadow: mode === m ? '0 2px 8px rgba(0,0,0,0.2)' : 'none',
            }}>
              {m === 'login' ? 'Sign In' : 'Sign Up'}
            </button>
          ))}
        </div>

        {/* Notice */}
        {notice && (
          <div style={{
            display: 'flex', alignItems: 'flex-start', gap: 10, padding: '12px 14px',
            borderRadius: 10, marginBottom: 20,
            background: notice.type === 'error' ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)',
            border: `1px solid ${notice.type === 'error' ? 'rgba(239,68,68,0.3)' : 'rgba(34,197,94,0.3)'}`,
          }}>
            {notice.type === 'error'
              ? <AlertCircle size={16} color="#ef4444" style={{ marginTop: 1, flexShrink: 0 }} />
              : <CheckCircle size={16} color="#22c55e" style={{ marginTop: 1, flexShrink: 0 }} />}
            <span style={{ fontSize: 13, color: notice.type === 'error' ? '#ef4444' : '#22c55e', lineHeight: 1.4 }}>
              {notice.msg}
            </span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {mode === 'register' && (
            <InputField
              icon={User} label="Full Name" type="text" value={name}
              onChange={e => setName(e.target.value)} placeholder="Rajesh Kumar" required={false}
            />
          )}
          <InputField
            icon={Mail} label="Email Address" type="email" value={email}
            onChange={e => setEmail(e.target.value)} placeholder="you@example.com"
          />
          <InputField
            icon={Lock} label="Password" type="password" value={password}
            onChange={e => setPassword(e.target.value)} placeholder="••••••••"
          />

          <button type="submit" disabled={loading} style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
            width: '100%', padding: '13px 0', borderRadius: 12, border: 'none',
            marginTop: 8, cursor: loading ? 'not-allowed' : 'pointer', fontWeight: 700,
            fontSize: 15, transition: 'all 0.2s',
            background: loading
              ? 'rgba(34,197,94,0.5)'
              : 'linear-gradient(135deg, #16a34a, #22c55e)',
            color: 'white', boxShadow: loading ? 'none' : '0 4px 16px rgba(34,197,94,0.4)',
          }}>
            {loading
              ? <><Loader2 size={17} style={{ animation: 'spin 1s linear infinite' }} /> Please wait...</>
              : <>{mode === 'login' ? 'Sign In' : 'Create Account'} <ArrowRight size={17} /></>}
          </button>
        </form>

        <p style={{ textAlign: 'center', fontSize: 12, color: 'var(--text-muted)', marginTop: 24 }}>
          By continuing, you agree to our{' '}
          <span style={{ color: 'var(--accent-green)', cursor: 'pointer' }}>Terms of Service</span>
        </p>
      </div>

      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  );
}

function InputField({ icon: Icon, label, type, value, onChange, placeholder, required = true }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
        {label}
      </label>
      <div style={{ position: 'relative' }}>
        <Icon size={15} style={{
          position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
          color: 'var(--text-muted)',
        }} />
        <input
          type={type} value={value} onChange={onChange}
          placeholder={placeholder} required={required}
          style={{
            width: '100%', boxSizing: 'border-box',
            padding: '11px 14px 11px 40px', borderRadius: 10,
            background: 'var(--bg-input)', border: '1px solid var(--border-subtle)',
            color: 'var(--text-primary)', fontSize: 14, outline: 'none',
            transition: 'border-color 0.2s',
          }}
          onFocus={e => e.target.style.borderColor = 'var(--accent-green)'}
          onBlur={e => e.target.style.borderColor = 'var(--border-subtle)'}
        />
      </div>
    </div>
  );
}
