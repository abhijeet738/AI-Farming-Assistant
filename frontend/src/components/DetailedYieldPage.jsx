import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  Sprout, 
  MapPin,
  Thermometer, 
  Wind, 
  CloudRain, 
  Loader2,
  TrendingUp,
  Map,
  Calendar,
  CheckCircle,
  BrainCircuit,
  Zap,
  Maximize
} from 'lucide-react';

export default function DetailedYieldPage({ location }) {
  const { authFetch } = useAuth();
  
  const parts = location ? location.split(',') : ['Ballia', 'Uttar Pradesh'];
  const stateName = parts.length > 1 ? parts[1].trim() : parts[0].trim();
  const districtName = parts.length > 1 ? parts[0].trim() : parts[0].trim();

  const [formData, setFormData] = useState({
    crop: 'Rice',
    state: stateName,
    district: districtName,
    season: 'Kharif',
    area_hectares: 5,
    temperature: 28,
    humidity: 75,
    rainfall: 800
  });

  const [result, setResult] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState(null);
  const [loadingWeather, setLoadingWeather] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ["crop", "state", "district", "season"].includes(name) ? value : Number(value)
    }));
  };

  const handleAutoFillWeather = async () => {
    setLoadingWeather(true);
    try {
      const res = await authFetch(`http://localhost:8000/api/v1/weather/${encodeURIComponent(stateName)}`);
      const data = await res.json();
      if (data.success) {
        setFormData(prev => ({
          ...prev,
          temperature: Math.round(data.current_temperature),
          humidity: Math.round(data.current_humidity),
          rainfall: data.forecast[0]?.rainfall ? Math.round(data.forecast[0].rainfall * 30) : 150
        }));
      }
    } catch (err) {
      console.error("Failed to auto-fill weather:", err);
    } finally {
      setLoadingWeather(false);
    }
  };

  const handleSubmit = async () => {
    setPredicting(true);
    setError(null);
    try {
      const res = await authFetch('http://localhost:8000/api/v1/yield/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (data.success) {
        setResult(data);
      } else {
        setError(data.message || "Failed to generate yield prediction");
      }
    } catch (err) {
      setError("Network error generating prediction");
    } finally {
      setPredicting(false);
    }
  };

  const StepperInput = ({ label, name, min, max, icon: Icon, unit, step = 1 }) => {
    const value = formData[name];
    const percentage = ((value - min) / (max - min)) * 100;

    const handleStep = (direction) => {
      let newValue = value + (direction * step);
      if (newValue < min) newValue = min;
      if (newValue > max) newValue = max;
      handleChange({ target: { name, value: newValue } });
    };

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
            {Icon && <Icon size={14} />} {label}
          </div>
        </div>
        
        <div style={{ 
          display: 'flex', alignItems: 'center', background: 'var(--bg-input)', 
          borderRadius: 8, padding: '4px', border: '1px solid var(--border-subtle)',
          position: 'relative', overflow: 'hidden'
        }}>
          <div style={{ 
            position: 'absolute', top: 0, left: 0, height: '100%', 
            width: `${percentage}%`, background: 'rgba(34,197,94,0.1)', 
            transition: 'width 0.2s ease', zIndex: 0 
          }} />
          
          <button 
            onClick={() => handleStep(-1)}
            style={{ 
              zIndex: 1, width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', 
              background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', cursor: 'pointer',
              borderRadius: 6, fontWeight: 700
            }}
          >
            -
          </button>
          
          <input 
            type="number"
            name={name}
            value={value}
            onChange={handleChange}
            min={min} max={max}
            style={{ 
              zIndex: 1, flex: 1, background: 'transparent', border: 'none', 
              color: 'var(--accent-green)', fontSize: 16, fontWeight: 700, 
              textAlign: 'center', outline: 'none'
            }}
          />
          
          <div style={{ zIndex: 1, fontSize: 13, color: 'var(--text-muted)', paddingRight: 12, fontWeight: 600 }}>
            {unit.trim()}
          </div>

          <button 
            onClick={() => handleStep(1)}
            style={{ 
              zIndex: 1, width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', 
              background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', cursor: 'pointer',
              borderRadius: 6, fontWeight: 700
            }}
          >
            +
          </button>
        </div>
      </div>
    );
  };

  return (
    <div style={{ flex: 1, overflow: 'auto', padding: 24, display: 'flex', flexDirection: 'column', gap: 24, minHeight: 0 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, display: 'flex', alignItems: 'center', gap: 12 }}>
          <TrendingUp size={28} color="var(--accent-green)" />
          Yield Predictor
        </h1>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)', fontSize: 13, background: 'var(--bg-input)', padding: '6px 12px', borderRadius: 20 }}>
          <MapPin size={14} /> {location}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, flex: 1, minHeight: 0 }}>
        {/* LEFT COLUMN: Input Form */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24, overflow: 'auto', paddingRight: 8 }}>
          
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16, borderBottom: '1px solid var(--border-subtle)', paddingBottom: 8 }}>
              Farm Parameters
            </h3>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Crop Type</div>
              <select name="crop" value={formData.crop} onChange={handleChange} style={{ padding: 12, borderRadius: 8, background: 'var(--bg-input)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', outline: 'none' }}>
                <option value="Rice">Rice</option>
                <option value="Wheat">Wheat</option>
                <option value="Maize">Maize</option>
                <option value="Sugarcane">Sugarcane</option>
                <option value="Cotton">Cotton</option>
              </select>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Season</div>
              <select name="season" value={formData.season} onChange={handleChange} style={{ padding: 12, borderRadius: 8, background: 'var(--bg-input)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', outline: 'none' }}>
                <option value="Kharif">Kharif (Monsoon)</option>
                <option value="Rabi">Rabi (Winter)</option>
                <option value="Summer">Summer</option>
                <option value="Whole Year">Whole Year</option>
              </select>
            </div>
            
            <StepperInput label="Area" name="area_hectares" min="0.1" max="1000" step="0.5" icon={Maximize} unit=" ha" />
          </div>

          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, borderBottom: '1px solid var(--border-subtle)', paddingBottom: 8 }}>
              <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>Climate Data</h3>
              <button 
                onClick={handleAutoFillWeather}
                disabled={loadingWeather}
                style={{ background: 'rgba(59,130,246,0.1)', color: 'var(--accent-blue)', border: '1px solid rgba(59,130,246,0.3)', padding: '4px 12px', borderRadius: 16, fontSize: 11, fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                {loadingWeather ? <Loader2 size={12} className="animate-spin" /> : <Zap size={12} />}
                Auto-fill for {stateName}
              </button>
            </div>
            
            <StepperInput label="Temperature" name="temperature" min="-10" max="55" icon={Thermometer} unit=" °C" />
            <StepperInput label="Humidity" name="humidity" min="0" max="100" icon={Wind} unit="%" />
            <StepperInput label="Rainfall (Season)" name="rainfall" min="0" max="1000" step="10" icon={CloudRain} unit=" mm" />
          </div>

          <button 
            onClick={handleSubmit}
            disabled={predicting}
            style={{
              background: 'var(--accent-green)', color: '#000', border: 'none',
              padding: '16px', borderRadius: 'var(--radius-md)', fontSize: 15, fontWeight: 700,
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              boxShadow: '0 4px 12px rgba(34,197,94,0.3)', transition: 'transform 0.1s ease'
            }}
            onMouseDown={e => e.currentTarget.style.transform = 'scale(0.98)'}
            onMouseUp={e => e.currentTarget.style.transform = 'scale(1)'}
          >
            {predicting ? (
              <><Loader2 size={18} className="animate-spin" /> Predicting Yield...</>
            ) : (
              <><TrendingUp size={18} /> Generate Prediction</>
            )}
          </button>
          {error && <div style={{ color: 'var(--accent-red)', fontSize: 13, textAlign: 'center' }}>{error}</div>}
        </div>

        {/* RIGHT COLUMN: Results */}
        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24, overflow: 'auto', paddingRight: 8 }}>
            
            <div style={{ background: 'var(--bg-card)', padding: 32, borderRadius: 'var(--radius-lg)', border: '2px solid var(--accent-green)', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: -20, right: -20, opacity: 0.05 }}><TrendingUp size={200} /></div>
              
              <div style={{ fontSize: 13, color: 'var(--accent-green)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
                Expected Yield
              </div>
              <div style={{ fontSize: 42, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>
                {result.predicted_yield_tonnes_per_hectare} <span style={{fontSize: 20, fontWeight: 600, color: 'var(--text-muted)'}}>t/ha</span>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ flex: 1, background: 'var(--bg-input)', height: 8, borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{ width: '100%', background: 'var(--accent-green)', height: '100%', borderRadius: 4 }} />
                </div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
                  Total: {result.total_production_tonnes} t
                </div>
              </div>
            </div>

            <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
              <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>Benchmark vs Averages</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{ width: 120, fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>State Average</div>
                  <div style={{ flex: 1, background: 'var(--bg-input)', height: 6, borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${Math.min(100, (result.benchmark.state_average / result.predicted_yield_tonnes_per_hectare) * 100)}%`, background: 'var(--text-muted)', height: '100%', borderRadius: 3 }} />
                  </div>
                  <div style={{ width: 60, textAlign: 'right', fontSize: 12, color: 'var(--text-muted)' }}>{result.benchmark.state_average} t/ha</div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                  <div style={{ width: 120, fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>National Avg</div>
                  <div style={{ flex: 1, background: 'var(--bg-input)', height: 6, borderRadius: 3, overflow: 'hidden' }}>
                    <div style={{ width: `${Math.min(100, (result.benchmark.national_average / result.predicted_yield_tonnes_per_hectare) * 100)}%`, background: 'var(--text-muted)', height: '100%', borderRadius: 3 }} />
                  </div>
                  <div style={{ width: 60, textAlign: 'right', fontSize: 12, color: 'var(--text-muted)' }}>{result.benchmark.national_average} t/ha</div>
                </div>
              </div>
            </div>

            {/* AI Explanation (SHAP) */}
            {result.shap_explanation && result.shap_explanation.length > 0 && (
              <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <BrainCircuit size={16} /> Impact on Predicted Yield
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {result.shap_explanation.map((shap, idx) => {
                    const isPositive = shap.importance > 0;
                    return (
                      <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <CheckCircle size={14} color={isPositive ? 'var(--accent-green)' : 'var(--text-muted)'} />
                          <span style={{ fontSize: 13, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
                            {shap.feature_name.replace('_', ' ')}
                          </span>
                          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>({Math.round(shap.value)})</span>
                        </div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: isPositive ? 'var(--accent-green)' : 'var(--accent-red)' }}>
                          {isPositive ? '+' : ''}{shap.importance.toFixed(2)} t/ha impact
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
