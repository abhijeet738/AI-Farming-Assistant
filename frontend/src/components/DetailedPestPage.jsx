import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { 
  MapPin,
  Loader2,
  Bug,
  ShieldAlert,
  Thermometer,
  Wind,
  CloudRain,
  Zap,
  Activity,
  CheckCircle,
  BrainCircuit,
  Calendar,
  CloudDrizzle
} from 'lucide-react';

export default function DetailedPestPage({ location }) {
  const { authFetch } = useAuth();
  
  const parts = location ? location.split(',') : ['Ballia', 'Uttar Pradesh'];
  const stateName = parts.length > 1 ? parts[1].trim() : parts[0].trim();
  const districtName = parts.length > 1 ? parts[0].trim() : parts[0].trim();

  const [formData, setFormData] = useState({
    crop: 'Rice',
    state: stateName,
    district: districtName,
    growth_stage: 'Vegetative',
    temperature: 28,
    humidity: 80,
    rainfall: 10,
    wind_speed: 8,
    wet_days: 2
  });

  const [result, setResult] = useState(null);
  const [predicting, setPredicting] = useState(false);
  const [error, setError] = useState(null);
  const [loadingWeather, setLoadingWeather] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ 
      ...prev, 
      [name]: ["crop", "state", "district", "growth_stage"].includes(name) ? value : Number(value) 
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
          rainfall: data.forecast[0]?.rainfall ? Math.round(data.forecast[0].rainfall) : 10,
          wind_speed: data.forecast[0]?.wind_speed ? Math.round(data.forecast[0].wind_speed) : 8
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
      const res = await authFetch('http://localhost:8000/api/v1/pest/assess', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      const data = await res.json();
      
      // Support both {success:true, ...data} and raw data models
      if (res.ok && (data.success || data.pest_risks)) {
        setResult(data);
      } else {
        setError(data.message || data.detail || "Failed to generate pest risk assessment");
      }
    } catch (err) {
      setError("Network error generating assessment");
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
          <Bug size={28} color="var(--accent-green)" />
          Pest Risk Assessment
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
              Assessment Parameters
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
              <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Growth Stage</div>
              <select name="growth_stage" value={formData.growth_stage} onChange={handleChange} style={{ padding: 12, borderRadius: 8, background: 'var(--bg-input)', border: '1px solid var(--border-subtle)', color: 'var(--text-primary)', outline: 'none' }}>
                <option value="Seedling">Seedling</option>
                <option value="Vegetative">Vegetative</option>
                <option value="Flowering">Flowering</option>
                <option value="Fruiting">Fruiting</option>
                <option value="Maturity">Maturity</option>
              </select>
            </div>
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
            <StepperInput label="Daily Rainfall" name="rainfall" min="0" max="1500" step="10" icon={CloudRain} unit=" mm" />
            <StepperInput label="Consecutive Wet Days" name="wet_days" min="0" max="30" step="1" icon={CloudDrizzle} unit=" days" />
          </div>

          {/* Submit Button */}
          <button 
            onClick={handleSubmit}
            disabled={predicting}
            style={{
              background: 'var(--accent-green)', color: '#000', border: 'none',
              padding: '16px', borderRadius: 'var(--radius-md)', fontSize: 15, fontWeight: 700,
              cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
              boxShadow: '0 4px 12px rgba(34,197,94,0.3)', transition: 'transform 0.1s ease', marginTop: 'auto'
            }}
            onMouseDown={e => e.currentTarget.style.transform = 'scale(0.98)'}
            onMouseUp={e => e.currentTarget.style.transform = 'scale(1)'}
          >
            {predicting ? (
              <><Loader2 size={18} className="animate-spin" /> Scanning Risks...</>
            ) : (
              <><Bug size={18} /> Run Risk Assessment</>
            )}
          </button>
          {error && <div style={{ color: 'var(--accent-red)', fontSize: 13, textAlign: 'center' }}>{error}</div>}
        </div>

        {/* RIGHT COLUMN: Results */}
        {result && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24, overflow: 'auto', paddingRight: 8 }}>
            
            <div style={{ background: 'var(--bg-card)', padding: 32, borderRadius: 'var(--radius-lg)', border: '2px solid var(--accent-red)', position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: -20, right: -20, opacity: 0.05 }}><ShieldAlert size={200} /></div>
              
              <div style={{ fontSize: 13, color: 'var(--accent-red)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
                Current Risk Status
              </div>
              
              {result.pest_risks && result.pest_risks.length > 0 ? (
                <>
                  <div style={{ fontSize: 32, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 8 }}>
                    {result.pest_risks[0].pest_name}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                    <div style={{ padding: '4px 12px', background: 'rgba(239, 68, 68, 0.2)', color: 'var(--accent-red)', borderRadius: 12, fontSize: 12, fontWeight: 700, textTransform: 'uppercase' }}>
                      {result.pest_risks[0].risk_level} Risk
                    </div>
                    <div style={{ padding: '4px 12px', background: 'var(--bg-input)', color: 'var(--text-primary)', borderRadius: 12, fontSize: 12, fontWeight: 700 }}>
                      Score: {result.pest_risks[0].risk_percentage}%
                    </div>
                    <div style={{ fontSize: 14, color: 'var(--text-muted)' }}>
                      Peaks on: {result.pest_risks[0].peak_risk_date}
                    </div>
                  </div>
                </>
              ) : (
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--accent-green)' }}>No Immediate Threats</div>
              )}
            </div>

            {/* AI Explanation (SHAP) */}
            {result.shap_explanation && result.shap_explanation.length > 0 && (
              <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <BrainCircuit size={16} /> Key Factors driving risk
                </h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {result.shap_explanation.map((shap, idx) => {
                    const isPositive = shap.importance > 0;
                    return (
                      <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'var(--bg-input)', borderRadius: 'var(--radius-sm)' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <Activity size={14} color={isPositive ? 'var(--accent-red)' : 'var(--accent-green)'} />
                          <span style={{ fontSize: 13, color: 'var(--text-primary)', textTransform: 'capitalize' }}>
                            {shap.feature_name.replace('_', ' ')}
                          </span>
                          <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>({Math.round(shap.value)})</span>
                        </div>
                        <div style={{ fontSize: 12, fontWeight: 600, color: isPositive ? 'var(--accent-red)' : 'var(--accent-green)' }}>
                          {isPositive ? '+' : ''}{shap.importance.toFixed(2)} risk score
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Preventive Measures */}
            {result.preventive_measures && result.preventive_measures.length > 0 && (
              <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 'var(--radius-lg)', border: '1px solid var(--border-subtle)' }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <ShieldAlert size={16} /> Recommended Action
                </h3>
                <div style={{ fontSize: 14, color: 'var(--text-primary)', lineHeight: 1.6 }}>
                  {result.preventive_measures[0].action}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
