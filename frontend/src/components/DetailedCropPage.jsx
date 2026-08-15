import { useState } from 'react';
import { Loader2, Sprout, Droplets, Thermometer, Wind, Beaker, CloudRain, CheckCircle, BrainCircuit, ArrowRight, Zap } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const SOIL_TYPES = ["Black", "Clayey", "Loamy", "Red", "Sandy"];

export default function DetailedCropPage({ location }) {
  const { authFetch } = useAuth();
  
  const [formData, setFormData] = useState({
    nitrogen: 50,
    phosphorus: 50,
    potassium: 50,
    ph: 6.5,
    soil_type: "Loamy",
    temperature: 25,
    humidity: 60,
    rainfall: 150
  });

  const [loadingWeather, setLoadingWeather] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const parts = location ? location.split(',') : ['Ballia', 'Uttar Pradesh'];
  const stateName = parts.length > 1 ? parts[1].trim() : parts[0].trim();
  const districtName = parts.length > 1 ? parts[0].trim() : parts[0].trim();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'soil_type' ? value : Number(value)
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
          rainfall: data.forecast[0]?.rainfall ? Math.round(data.forecast[0].rainfall * 30) : 150 // Approx monthly rainfall
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
      const res = await authFetch('http://localhost:8000/api/v1/crop/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      if (data.success || data.predictions) {
        setResult(data);
      } else {
        setError(data.detail || "Failed to generate prediction");
      }
    } catch (err) {
      setError("Network error generating prediction");
    } finally {
      setPredicting(false);
    }
  };

  // ─── Sub-component: Stepper Input ─────────────────────────────────────────────
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
          {/* Subtle background progress bar */}
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexShrink: 0 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 8 }}>
            <BrainCircuit size={24} color="var(--accent-green)" />
            Predictive Crop Advisor
          </h2>
          <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>
            AI-powered agronomy engine predicting the most profitable crops for your specific field parameters.
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: result ? '1fr 1fr' : '1fr', gap: 24 }}>
        
        {/* LEFT COLUMN: Input Form */}
        <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column', gap: 24 }}>
          
          {/* Soil Health Section */}
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16, borderBottom: '1px solid var(--border-subtle)', paddingBottom: 8 }}>
              Soil Parameters
            </h3>
            <StepperInput label="Nitrogen (N)" name="nitrogen" min="0" max="200" icon={Beaker} unit=" kg/ha" />
            <StepperInput label="Phosphorus (P)" name="phosphorus" min="0" max="200" icon={Beaker} unit=" kg/ha" />
            <StepperInput label="Potassium (K)" name="potassium" min="0" max="300" icon={Beaker} unit=" kg/ha" />
            <StepperInput label="Soil pH" name="ph" min="0" max="14" step="0.1" icon={Droplets} unit="" />
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, marginBottom: 16 }}>
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Soil Type</div>
              <select 
                name="soil_type" 
                value={formData.soil_type} 
                onChange={handleChange}
                style={{ background: 'var(--bg-input)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', padding: '10px 12px', borderRadius: 'var(--radius-md)', outline: 'none' }}
              >
                {SOIL_TYPES.map(type => <option key={type} value={type}>{type}</option>)}
              </select>
            </div>
          </div>

          {/* Climate Section */}
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

          {/* Submit Button */}
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
              <><Loader2 size={18} className="animate-spin" /> Analyzing Field Data...</>
            ) : (
              <><BrainCircuit size={18} /> Generate Recommendation</>
            )}
          </button>
          {error && <div style={{ color: 'var(--accent-red)', fontSize: 13, textAlign: 'center' }}>{error}</div>}
        </div>

        {/* RIGHT COLUMN: Results */}
        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            
            {/* Top Crop Hero */}
            <div style={{ background: 'var(--bg-card)', padding: 32, borderRadius: 'var(--radius-lg)', border: '2px solid var(--accent-green)', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: -20, right: -20, opacity: 0.05 }}><Sprout size={200} /></div>
              
              <div style={{ fontSize: 13, color: 'var(--accent-green)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
                Primary Recommendation
              </div>
              <div style={{ fontSize: 42, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>
                {result.predictions[0].crop_name}
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ flex: 1, background: 'var(--bg-input)', height: 8, borderRadius: 4, overflow: 'hidden' }}>
                  <div style={{ width: `${result.predictions[0].suitability_score}%`, background: 'var(--accent-green)', height: '100%', borderRadius: 4 }} />
                </div>
                <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)' }}>
                  {Math.round(result.predictions[0].suitability_score)}% Match
                </div>
              </div>
            </div>

            {/* Runner Ups */}
            <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
              <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16 }}>Alternative Options</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {result.predictions.slice(1, 5).map((pred, idx) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                    <div style={{ width: 80, fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>{pred.crop_name}</div>
                    <div style={{ flex: 1, background: 'var(--bg-input)', height: 6, borderRadius: 3, overflow: 'hidden' }}>
                      <div style={{ width: `${pred.suitability_score}%`, background: 'var(--text-muted)', height: '100%', borderRadius: 3 }} />
                    </div>
                    <div style={{ width: 40, textAlign: 'right', fontSize: 12, color: 'var(--text-muted)' }}>{Math.round(pred.suitability_score)}%</div>
                  </div>
                ))}
              </div>
            </div>

            {/* AI Explanation (SHAP) */}
            {result.shap_explanation && result.shap_explanation.length > 0 && (
              <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <BrainCircuit size={16} /> Why did the AI choose {result.predictions[0].crop_name}?
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {result.shap_explanation.slice(0, 3).map((shap, idx) => {
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
                          {isPositive ? '+' : ''}{Math.round(shap.importance * 100)}% impact
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Text Recommendations */}
            {result.recommendations && result.recommendations.length > 0 && (
              <div style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.5, padding: '0 8px' }}>
                <strong>Agronomy Note:</strong> {result.recommendations[0]}
              </div>
            )}

          </div>
        )}
      </div>
    </div>
  );
}
