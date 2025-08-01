import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Clock SVG Component
const ClockSVG = ({ hours, minutes }) => {
  // Calculate angles for clock hands
  const minuteAngle = (minutes * 6) - 90; // 6 degrees per minute
  const hourAngle = ((hours % 12) * 30) + (minutes * 0.5) - 90; // 30 degrees per hour + minute adjustment
  
  return (
    <div className="flex justify-center mb-4">
      <svg width="200" height="200" viewBox="0 0 200 200" className="border-2 border-purple-300 rounded-full">
        {/* Clock face */}
        <circle cx="100" cy="100" r="95" fill="white" stroke="#8b5cf6" strokeWidth="4"/>
        
        {/* Hour markers */}
        {[...Array(12)].map((_, i) => {
          const angle = (i * 30) - 90;
          const x1 = 100 + 80 * Math.cos(angle * Math.PI / 180);
          const y1 = 100 + 80 * Math.sin(angle * Math.PI / 180);
          const x2 = 100 + 70 * Math.cos(angle * Math.PI / 180);
          const y2 = 100 + 70 * Math.sin(angle * Math.PI / 180);
          return (
            <line 
              key={i} 
              x1={x1} y1={y1} x2={x2} y2={y2} 
              stroke="#6b7280" strokeWidth="3"
            />
          );
        })}
        
        {/* Numbers */}
        {[...Array(12)].map((_, i) => {
          const num = i === 0 ? 12 : i;
          const angle = (i * 30) - 90;
          const x = 100 + 60 * Math.cos(angle * Math.PI / 180);
          const y = 100 + 60 * Math.sin(angle * Math.PI / 180);
          return (
            <text 
              key={i} 
              x={x} y={y + 5} 
              textAnchor="middle" 
              fontSize="16" 
              fontWeight="bold" 
              fill="#4b5563"
            >
              {num}
            </text>
          );
        })}
        
        {/* Hour hand */}
        <line 
          x1="100" y1="100" 
          x2={100 + 50 * Math.cos(hourAngle * Math.PI / 180)} 
          y2={100 + 50 * Math.sin(hourAngle * Math.PI / 180)}
          stroke="#dc2626" strokeWidth="6" strokeLinecap="round"
        />
        
        {/* Minute hand */}
        <line 
          x1="100" y1="100" 
          x2={100 + 70 * Math.cos(minuteAngle * Math.PI / 180)} 
          y2={100 + 70 * Math.sin(minuteAngle * Math.PI / 180)}
          stroke="#1f2937" strokeWidth="4" strokeLinecap="round"
        />
        
        {/* Center dot */}
        <circle cx="100" cy="100" r="8" fill="#4b5563"/>
      </svg>
    </div>
  );
};

// Star Component
const StarIcon = ({ filled, onClick }) => (
  <button 
    onClick={onClick}
    className={`text-2xl transition-all duration-200 hover:scale-110 ${
      filled ? 'text-yellow-400' : 'text-gray-300'
    }`}
  >
    {filled ? '⭐' : '☆'}
  </button>
);

// Task Row Component
const TaskRow = ({ task, weekStars, onStarClick }) => {
  const days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
  
  const getStarsForDay = (day) => {
    const dayStars = weekStars.find(s => s.task_id === task.id && s.day === day);
    return dayStars ? dayStars.stars : 0;
  };

  return (
    <div className="grid grid-cols-8 gap-4 p-4 bg-white rounded-xl shadow-sm border border-purple-100 hover:shadow-md transition-shadow">
      <div className="font-medium text-purple-800 flex items-center">
        {task.name}
      </div>
      {days.map(day => {
        const currentStars = getStarsForDay(day);
        return (
          <div key={day} className="flex justify-center items-center space-x-1">
            <StarIcon 
              filled={currentStars >= 1} 
              onClick={() => onStarClick(task.id, day, currentStars >= 1 ? 0 : 1)}
            />
            <StarIcon 
              filled={currentStars >= 2} 
              onClick={() => onStarClick(task.id, day, currentStars >= 2 ? 1 : 2)}
            />
          </div>
        );
      })}
    </div>
  );
};

// Stars Summary Component
const StarsSummary = ({ taskStars, availableStars, onAddTaskStarsToAvailable }) => {
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-purple-100">
      <h3 className="text-xl font-semibold text-purple-800 mb-4 text-center">⭐ Sterne-Übersicht ⭐</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Available Stars for Rewards */}
        <div className="text-center p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 rounded-xl border-2 border-yellow-300">
          <h4 className="text-lg font-semibold text-purple-800 mb-2">Verfügbare Sterne</h4>
          <div className="text-4xl font-bold text-yellow-600 mb-2">{availableStars} ⭐</div>
          <p className="text-sm text-gray-600">Für Belohnungen</p>
        </div>

        {/* Task Stars */}
        <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl border-2 border-purple-300">
          <h4 className="text-lg font-semibold text-purple-800 mb-2">Aufgaben-Sterne</h4>
          <div className="text-4xl font-bold text-purple-600 mb-2">{taskStars} ⭐</div>
          {taskStars > 0 && (
            <button 
              onClick={onAddTaskStarsToAvailable}
              className="text-xs bg-purple-500 text-white px-3 py-1 rounded-lg hover:bg-purple-600 transition-colors"
            >
              ➡️ Zu Verfügbar
            </button>
          )}
        </div>

        {/* Total Earned */}
        <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl border-2 border-green-300">
          <h4 className="text-lg font-semibold text-purple-800 mb-2">Gesamt Verdient</h4>
          <div className="text-4xl font-bold text-green-600 mb-2">{taskStars + availableStars} ⭐</div>
          <p className="text-sm text-gray-600">Diese Woche</p>
        </div>
      </div>
      
      <div className="mt-4 text-center text-sm text-gray-500">
        💡 Tipp: Nimm Sterne aus dem Tresor heraus, um sie für Belohnungen zu verwenden!
      </div>
    </div>
  );
};

// Progress Bar Component
const ProgressBar = ({ current, total, starsInSafe, onOpenSafe, onAddToSafe, onResetWeek }) => {
  const percentage = total > 0 ? (current / total) * 100 : 0;
  
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-purple-100">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-purple-800">Wöchentlicher Fortschritt</h3>
        <div className="text-sm text-purple-600">
          {current} / {total} Sterne
        </div>
      </div>
      <div className="w-full bg-purple-100 rounded-full h-4 mb-4">
        <div 
          className="bg-gradient-to-r from-purple-500 to-indigo-600 h-4 rounded-full transition-all duration-500"
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <button 
            onClick={onOpenSafe}
            className="flex items-center bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-600 transition-colors"
          >
            💰 Tresor: {starsInSafe} ⭐
          </button>
          <button 
            onClick={onAddToSafe}
            className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
            disabled={current === 0}
          >
            ⬇️ In Tresor
          </button>
        </div>
        <button 
          className="bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition-colors"
          onClick={onResetWeek}
        >
          Woche Zurücksetzen
        </button>
      </div>
    </div>
  );
};

// Reward Claim Error Modal Component
const RewardClaimErrorModal = ({ isOpen, onClose, rewardName, requiredStars, availableStars }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-8 max-w-md w-full mx-4">
        <div className="text-center">
          <div className="text-6xl mb-4">😔</div>
          <h2 className="text-2xl font-bold text-purple-800 mb-4">Nicht genug Sterne!</h2>
          <div className="text-gray-600 mb-6">
            <p className="mb-3">Du möchtest <span className="font-semibold text-purple-800">"{rewardName}"</span> einlösen.</p>
            <div className="bg-purple-50 p-4 rounded-lg">
              <p className="mb-2">
                <span className="font-medium">Benötigt:</span> {requiredStars} ⭐
              </p>
              <p className="mb-2">
                <span className="font-medium">Verfügbar:</span> {availableStars} ⭐
              </p>
              <p className="text-red-600 font-medium">
                Du brauchst noch {requiredStars - availableStars} ⭐ mehr!
              </p>
            </div>
          </div>
          <div className="text-sm text-gray-500 mb-6">
            💡 Tipp: Sammle mehr Sterne durch Aufgaben oder nimm Sterne aus dem Tresor!
          </div>
          <button 
            onClick={onClose}
            className="bg-purple-500 text-white px-8 py-3 rounded-lg hover:bg-purple-600 transition-colors"
          >
            Verstanden
          </button>
        </div>
      </div>
    </div>
  );
};

// Safe Modal Component
const SafeModal = ({ isOpen, onClose, starsInSafe, onWithdraw }) => {
  const [withdrawAmount, setWithdrawAmount] = useState('');

  const handleWithdraw = async () => {
    const amount = parseInt(withdrawAmount);
    if (amount > 0 && amount <= starsInSafe) {
      await onWithdraw(amount);
      setWithdrawAmount('');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-8 max-w-md w-full mx-4">
        <div className="text-center">
          <div className="text-6xl mb-4">💰</div>
          <h2 className="text-2xl font-bold text-purple-800 mb-4">Sternen-Tresor</h2>
          <div className="text-4xl font-bold text-yellow-600 mb-6">
            {starsInSafe} ⭐
          </div>
          
          {starsInSafe > 0 && (
            <div className="mb-6">
              <p className="text-purple-600 mb-3">Wie viele Sterne möchtest du herausnehmen?</p>
              <div className="flex space-x-2">
                <input
                  type="number"
                  min="1"
                  max={starsInSafe}
                  value={withdrawAmount}
                  onChange={(e) => setWithdrawAmount(e.target.value)}
                  className="flex-1 p-3 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
                  placeholder={`1-${starsInSafe}`}
                />
                <button 
                  onClick={handleWithdraw}
                  disabled={!withdrawAmount || parseInt(withdrawAmount) > starsInSafe}
                  className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
                >
                  Herausnehmen
                </button>
              </div>
            </div>
          )}
          
          <button 
            onClick={onClose}
            className="bg-purple-500 text-white px-8 py-3 rounded-lg hover:bg-purple-600 transition-colors"
          >
            Tresor Schließen
          </button>
        </div>
      </div>
    </div>
  );
};

// Enhanced Math Settings Modal Component
const MathSettingsModal = ({ isOpen, onClose, onComplete }) => {
  const [settings, setSettings] = useState(null);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('settings');

  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen]);

  const loadData = async () => {
    try {
      const [settingsRes, statsRes] = await Promise.all([
        axios.get(`${API}/math/settings`),
        axios.get(`${API}/math/statistics`)
      ]);
      setSettings(settingsRes.data);
      setStatistics(statsRes.data);
    } catch (error) {
      console.error('Fehler beim Laden der Mathe-Daten:', error);
    }
  };

  const updateSettings = async () => {
    setLoading(true);
    try {
      await axios.put(`${API}/math/settings`, settings);
      onComplete();
      alert('Einstellungen erfolgreich gespeichert!');
    } catch (error) {
      console.error('Fehler beim Aktualisieren der Einstellungen:', error);
    }
    setLoading(false);
  };

  const resetStatistics = async () => {
    if (confirm('Bist du sicher, dass du alle Mathe-Statistiken zurücksetzen möchtest?')) {
      try {
        await axios.post(`${API}/math/statistics/reset`);
        loadData();
        alert('Statistiken erfolgreich zurückgesetzt!');
      } catch (error) {
        console.error('Fehler beim Zurücksetzen der Statistiken:', error);
      }
    }
  };

  const updateStarTier = (percentage, stars) => {
    const newTiers = { ...settings.star_tiers };
    newTiers[percentage] = stars;
    setSettings({ ...settings, star_tiers: newTiers });
  };

  const removeStarTier = (percentage) => {
    const newTiers = { ...settings.star_tiers };
    delete newTiers[percentage];
    setSettings({ ...settings, star_tiers: newTiers });
  };

  const addStarTier = () => {
    const percentage = prompt('Gib die Prozentschwelle ein (z.B. 85):');
    const stars = prompt('Gib die Anzahl der zu vergebenden Sterne ein:');
    if (percentage && stars) {
      updateStarTier(percentage, parseInt(stars));
    }
  };

  const updateProblemType = (type, enabled) => {
    const newTypes = { ...settings.problem_types };
    newTypes[type] = enabled;
    setSettings({ ...settings, problem_types: newTypes });
  };

  if (!isOpen || !settings || !statistics) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-xl p-8 max-w-5xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-purple-800">Mathe-Herausforderung Einstellungen</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 text-2xl">✕</button>
        </div>

        {/* Tab Navigation */}
        <div className="flex mb-6 border-b border-purple-200">
          <button
            onClick={() => setActiveTab('settings')}
            className={`py-2 px-4 font-medium transition-colors ${
              activeTab === 'settings'
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-600 hover:text-purple-600'
            }`}
          >
            ⚙️ Einstellungen
          </button>
          <button
            onClick={() => setActiveTab('statistics')}
            className={`py-2 px-4 font-medium transition-colors ${
              activeTab === 'statistics'
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-600 hover:text-purple-600'
            }`}
          >
            📊 Statistiken
          </button>
        </div>

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="space-y-6">
            {/* Problem Types */}
            <div>
              <h3 className="text-lg font-semibold text-purple-800 mb-3">🧮 Aufgaben-Typen</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(settings.problem_types || {}).map(([type, enabled]) => {
                  const typeNames = {
                    addition: "➕ Addition",
                    subtraction: "➖ Subtraktion",
                    multiplication: "✖️ Multiplikation",
                    clock_reading: "🕐 Uhrzeiten ablesen",
                    currency_math: "💰 Währungsrechnungen",
                    word_problems: "📝 Textaufgaben"
                  };
                  return (
                    <label key={type} className="flex items-center space-x-3 p-3 bg-purple-50 rounded-lg">
                      <input
                        type="checkbox"
                        checked={enabled}
                        onChange={(e) => updateProblemType(type, e.target.checked)}
                        className="w-5 h-5 text-purple-600 rounded"
                      />
                      <span className="font-medium">{typeNames[type] || type}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Basic Settings */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <label className="block text-sm font-medium text-purple-800 mb-2">
                  Anzahl Aufgaben pro Herausforderung
                </label>
                <input
                  type="number"
                  min="10"
                  max="50"
                  value={settings.problem_count}
                  onChange={(e) => setSettings({...settings, problem_count: parseInt(e.target.value)})}
                  className="w-full p-3 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
                />
                <p className="text-xs text-gray-500 mt-1">Standard: 30 Aufgaben</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-purple-800 mb-2">
                  Maximale Zahl (Addition/Subtraktion)
                </label>
                <input
                  type="number"
                  value={settings.max_number}
                  onChange={(e) => setSettings({...settings, max_number: parseInt(e.target.value)})}
                  className="w-full p-3 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-purple-800 mb-2">
                  Maximale Multiplikationstabelle
                </label>
                <input
                  type="number"
                  value={settings.max_multiplication}
                  onChange={(e) => setSettings({...settings, max_multiplication: parseInt(e.target.value)})}
                  className="w-full p-3 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
                />
              </div>
            </div>

            {/* Currency Settings */}
            {settings.problem_types?.currency_math && (
              <div className="border border-purple-200 rounded-lg p-4">
                <h4 className="text-md font-semibold text-purple-800 mb-3">💰 Währungs-Einstellungen</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-purple-800 mb-2">
                      Währungssymbol
                    </label>
                    <input
                      type="text"
                      value={settings.currency_settings?.currency_symbol || "€"}
                      onChange={(e) => setSettings({
                        ...settings,
                        currency_settings: {
                          ...settings.currency_settings,
                          currency_symbol: e.target.value
                        }
                      })}
                      className="w-full p-2 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-purple-800 mb-2">
                      Maximaler Betrag
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={settings.currency_settings?.max_amount || 20.00}
                      onChange={(e) => setSettings({
                        ...settings,
                        currency_settings: {
                          ...settings.currency_settings,
                          max_amount: parseFloat(e.target.value)
                        }
                      })}
                      className="w-full p-2 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Clock Settings */}
            {settings.problem_types?.clock_reading && (
              <div className="border border-purple-200 rounded-lg p-4">
                <h4 className="text-md font-semibold text-purple-800 mb-3">🕐 Uhrzeiten-Einstellungen</h4>
                <div className="space-y-3">
                  {Object.entries(settings.clock_settings || {}).map(([key, value]) => {
                    const settingNames = {
                      include_half_hours: "Halbe Stunden (X:30)",
                      include_quarter_hours: "Viertelstunden (X:15, X:45)",
                      include_five_minute_intervals: "5-Minuten-Schritte"
                    };
                    if (typeof value === 'boolean') {
                      return (
                        <label key={key} className="flex items-center space-x-3">
                          <input
                            type="checkbox"
                            checked={value}
                            onChange={(e) => setSettings({
                              ...settings,
                              clock_settings: {
                                ...settings.clock_settings,
                                [key]: e.target.checked
                              }
                            })}
                            className="w-4 h-4 text-purple-600 rounded"
                          />
                          <span>{settingNames[key] || key}</span>
                        </label>
                      );
                    }
                    return null;
                  })}
                </div>
              </div>
            )}

            {/* Star Rewards */}
            <div>
              <h3 className="text-lg font-semibold text-purple-800 mb-3">⭐ Sternen-Belohnungs-Stufen</h3>
              <p className="text-sm text-gray-600 mb-4">Bestimme, wie viele Sterne basierend auf der Prozentscore vergeben werden</p>
              
              <div className="space-y-3">
                {Object.entries(settings.star_tiers).map(([percentage, stars]) => (
                  <div key={percentage} className="flex items-center space-x-3 bg-purple-50 p-3 rounded-lg">
                    <span className="font-medium">{percentage}% oder höher:</span>
                    <input
                      type="number"
                      value={stars}
                      onChange={(e) => updateStarTier(percentage, parseInt(e.target.value))}
                      className="w-20 p-2 border border-purple-300 rounded focus:outline-none focus:border-purple-500"
                    />
                    <span>⭐ Sterne</span>
                    <button
                      onClick={() => removeStarTier(percentage)}
                      className="text-red-500 hover:text-red-700"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
              
              <button
                onClick={addStarTier}
                className="mt-3 bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
              >
                + Stufe Hinzufügen
              </button>
            </div>

            <div className="flex justify-end space-x-4">
              <button 
                onClick={onClose}
                className="px-6 py-2 border border-purple-300 text-purple-600 rounded-lg hover:bg-purple-50 transition-colors"
              >
                Abbrechen
              </button>
              <button 
                onClick={updateSettings}
                disabled={loading}
                className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50"
              >
                {loading ? 'Speichern...' : 'Einstellungen Speichern'}
              </button>
            </div>
          </div>
        )}

        {/* Statistics Tab */}
        {activeTab === 'statistics' && (
          <div className="space-y-6">
            {/* Overview Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="stats-card stats-card-total">
                <h3 className="font-semibold mb-2">Gesamt Versuche</h3>
                <p className="text-3xl font-bold">{statistics.total_attempts}</p>
              </div>
              <div className="stats-card stats-card-completed">
                <h3 className="font-semibold mb-2">Durchschnittsscore</h3>
                <p className="text-3xl font-bold">{statistics.average_score.toFixed(1)}%</p>
              </div>
              <div className="stats-card stats-card-pending">
                <h3 className="font-semibold mb-2">Bester Score</h3>
                <p className="text-3xl font-bold">{statistics.best_score.toFixed(1)}%</p>
              </div>
              <div className="stats-card">
                <h3 className="font-semibold mb-2">Verdiente Sterne</h3>
                <p className="text-3xl font-bold">{statistics.total_stars_earned} ⭐</p>
              </div>
            </div>

            {/* Detailed Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="card">
                <h3 className="text-lg font-semibold text-purple-800 mb-4">📚 Klassen-Aufschlüsselung</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>Klasse 2 Versuche:</span>
                    <span className="font-semibold">{statistics.grade_2_attempts}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Klasse 3 Versuche:</span>
                    <span className="font-semibold">{statistics.grade_3_attempts}</span>
                  </div>
                </div>
              </div>

              <div className="card">
                <h3 className="text-lg font-semibold text-purple-800 mb-4">🎯 Antworten-Aufschlüsselung</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-green-600">✅ Richtige Antworten:</span>
                    <span className="font-semibold text-green-600">{statistics.total_correct}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-red-600">❌ Falsche Antworten:</span>
                    <span className="font-semibold text-red-600">{statistics.total_wrong}</span>
                  </div>
                  <div className="pt-2 border-t">
                    <div className="flex justify-between items-center">
                      <span>Genauigkeitsrate:</span>
                      <span className="font-semibold">
                        {statistics.total_correct + statistics.total_wrong > 0 
                          ? ((statistics.total_correct / (statistics.total_correct + statistics.total_wrong)) * 100).toFixed(1)
                          : 0}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-4">
              <button
                onClick={resetStatistics}
                className="bg-red-500 text-white px-6 py-2 rounded-lg hover:bg-red-600 transition-colors"
              >
                Statistiken Zurücksetzen
              </button>
              <button 
                onClick={onClose}
                className="bg-purple-500 text-white px-6 py-2 rounded-lg hover:bg-purple-600 transition-colors"
              >
                Schließen
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Enhanced Math Challenge Component
const MathChallenge = ({ onClose, onComplete }) => {
  const [grade, setGrade] = useState(null);
  const [challenge, setChallenge] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);

  const startChallenge = async (selectedGrade) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/math/challenge/${selectedGrade}`);
      setChallenge(response.data);
      setGrade(selectedGrade);
      setAnswers({});
    } catch (error) {
      console.error('Fehler beim Erstellen der Mathe-Herausforderung:', error);
      alert('Fehler beim Erstellen der Mathe-Herausforderung. Bitte versuche es erneut.');
    }
    setLoading(false);
  };

  const submitAnswers = async () => {
    if (!challenge) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/math/challenge/${challenge.id}/submit`, answers);
      setResult(response.data);
      setShowResults(true);
    } catch (error) {
      console.error('Fehler beim Einreichen der Antworten:', error);
      alert('Fehler beim Einreichen der Antworten. Bitte versuche es erneut.');
    }
    setLoading(false);
  };

  const allAnswersProvided = challenge && Object.keys(answers).length === challenge.problems.length &&
    challenge.problems.every((_, index) => answers[index] !== undefined && answers[index] !== '');

  // Results Detail Page
  if (showResults && result) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
        <div className="bg-white rounded-xl p-8 max-w-4xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
          <div className="text-center mb-6">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold text-purple-800 mb-4">Großartige Arbeit!</h2>
            <div className="space-y-2 mb-6">
              <p>Richtige Antworten: {result.correct_answers}/{result.total_problems}</p>
              <p>Score: {result.percentage.toFixed(1)}%</p>
              <p className="text-lg font-semibold text-yellow-600">
                Verdiente Sterne: {result.stars_earned} ⭐
              </p>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-semibold text-purple-800 mb-4">Überprüfe deine Antworten:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.challenge.problems.map((problem, index) => (
                <div key={index} className={`p-4 rounded-lg border-2 ${
                  problem.is_correct 
                    ? 'bg-green-50 border-green-300' 
                    : 'bg-red-50 border-red-300'
                }`}>
                  <div className="flex items-center mb-2">
                    <span className="text-lg mr-2">
                      {problem.is_correct ? '✅' : '❌'}
                    </span>
                    <span className="font-medium">Aufgabe {index + 1}</span>
                  </div>
                  
                  {/* Render different problem types */}
                  {problem.question_type === 'clock' && problem.clock_data && (
                    <div className="mb-3">
                      <ClockSVG hours={problem.clock_data.hours} minutes={problem.clock_data.minutes} />
                    </div>
                  )}
                  
                  <p className="mb-2 font-medium">{problem.question}</p>
                  <div className="space-y-1 text-sm">
                    <p><span className="font-medium">Deine Antwort:</span> {problem.user_answer}</p>
                    {!problem.is_correct && (
                      <p className="text-green-600">
                        <span className="font-medium">Richtige Antwort:</span> {problem.correct_answer}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="text-center">
            <button 
              onClick={() => {
                onComplete();
                onClose();
              }}
              className="bg-purple-500 text-white px-8 py-3 rounded-lg hover:bg-purple-600 transition-colors text-lg"
            >
              Super! Weiter
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Summary Results Page (kept for quick view)
  if (result && !showResults) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-xl p-8 max-w-md w-full mx-4">
          <div className="text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold text-purple-800 mb-4">Großartige Arbeit!</h2>
            <div className="space-y-2 mb-6">
              <p>Richtige Antworten: {result.correct_answers}/{result.total_problems}</p>
              <p>Score: {result.percentage.toFixed(1)}%</p>
              <p className="text-lg font-semibold text-yellow-600">
                Verdiente Sterne: {result.stars_earned} ⭐
              </p>
            </div>
            <div className="flex space-x-4">
              <button 
                onClick={() => setShowResults(true)}
                className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
              >
                Antworten Überprüfen
              </button>
              <button 
                onClick={() => {
                  onComplete();
                  onClose();
                }}
                className="bg-purple-500 text-white px-6 py-2 rounded-lg hover:bg-purple-600 transition-colors"
              >
                Weiter
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (challenge) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
        <div className="bg-white rounded-xl p-8 max-w-3xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-purple-800">Mathe Klasse {grade} Herausforderung</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
          </div>
          
          <div className="mb-4 text-sm text-gray-600">
            Fülle ALLE Antworten aus, um die Einreichung zu aktivieren. Antworten ausgefüllt: {Object.keys(answers).length}/{challenge.problems.length}
            <br />
            <span className="text-purple-600 font-medium">Insgesamt {challenge.problems.length} Aufgaben</span>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {challenge.problems.map((problem, index) => (
              <div key={index} className={`p-4 border-2 rounded-lg transition-colors ${
                answers[index] !== undefined && answers[index] !== '' 
                  ? 'border-green-300 bg-green-50' 
                  : 'border-purple-200 bg-white'
              }`}>
                <p className="mb-2 font-medium">{index + 1}. {problem.question}</p>
                
                {/* Render clock for clock problems */}
                {problem.question_type === 'clock' && problem.clock_data && (
                  <div className="mb-3">
                    <ClockSVG hours={problem.clock_data.hours} minutes={problem.clock_data.minutes} />
                  </div>
                )}
                
                <input
                  type="text"
                  className="w-full p-2 border border-purple-300 rounded focus:outline-none focus:border-purple-500"
                  placeholder={
                    problem.question_type === 'clock' ? 'z.B. 3:30' : 
                    problem.question_type === 'currency' ? 'z.B. 5,50' : 
                    'Deine Antwort'
                  }
                  value={answers[index] || ''}
                  onChange={(e) => {
                    setAnswers({...answers, [index]: e.target.value});
                  }}
                />
              </div>
            ))}
          </div>
          
          <div className="flex justify-end space-x-4">
            <button 
              onClick={onClose}
              className="px-6 py-2 border border-purple-300 text-purple-600 rounded-lg hover:bg-purple-50 transition-colors"
            >
              Abbrechen
            </button>
            <button 
              onClick={submitAnswers}
              disabled={loading || !allAnswersProvided}
              className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Einreichen...' : `Alle Antworten Einreichen (${Object.keys(answers).length}/${challenge.problems.length})`}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-8 max-w-md w-full mx-4">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-purple-800 mb-6">Verdiene Extra-Sterne!</h2>
          <p className="text-gray-600 mb-6">Wähle deine Mathe-Klassenstufe:</p>
          <div className="space-y-4">
            <button 
              onClick={() => startChallenge(2)}
              disabled={loading}
              className="w-full p-4 bg-gradient-to-r from-purple-400 to-pink-400 text-white rounded-xl hover:from-purple-500 hover:to-pink-500 transition-all disabled:opacity-50"
            >
              📚 Mathe Klasse 2
            </button>
            <button 
              onClick={() => startChallenge(3)}
              disabled={loading}
              className="w-full p-4 bg-gradient-to-r from-indigo-400 to-purple-400 text-white rounded-xl hover:from-indigo-500 hover:to-purple-500 transition-all disabled:opacity-50"
            >
              🎓 Mathe Klasse 3
            </button>
          </div>
          <button 
            onClick={onClose}
            className="mt-4 text-purple-600 hover:text-purple-800 transition-colors"
          >
            Vielleicht Später
          </button>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [tasks, setTasks] = useState([]);
  const [weekStars, setWeekStars] = useState([]);
  const [progress, setProgress] = useState({ total_stars: 0, stars_in_safe: 0, available_stars: 0 });
  const [rewards, setRewards] = useState([]);
  const [newTaskName, setNewTaskName] = useState('');
  const [newRewardName, setNewRewardName] = useState('');
  const [newRewardStars, setNewRewardStars] = useState('');
  const [showMathChallenge, setShowMathChallenge] = useState(false);
  const [showSafe, setShowSafe] = useState(false);
  const [showMathSettings, setShowMathSettings] = useState(false);
  const [rewardClaimError, setRewardClaimError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [tasksRes, starsRes, progressRes, rewardsRes] = await Promise.all([
        axios.get(`${API}/tasks`),
        axios.get(`${API}/stars`),
        axios.get(`${API}/progress`),
        axios.get(`${API}/rewards`)
      ]);
      
      setTasks(tasksRes.data);
      setWeekStars(starsRes.data);
      setProgress(progressRes.data);
      setRewards(rewardsRes.data);
    } catch (error) {
      console.error('Fehler beim Laden der Daten:', error);
    }
    setLoading(false);
  };

  const addTask = async () => {
    const taskName = newTaskName.trim();
    if (!taskName) {
      alert('Bitte gib einen Aufgabennamen ein!');
      return;
    }
    
    try {
      const response = await axios.post(`${API}/tasks`, { name: taskName });
      if (response.status === 200) {
        setNewTaskName('');
        await loadData();
        console.log('Aufgabe erfolgreich hinzugefügt:', taskName);
      }
    } catch (error) {
      console.error('Fehler beim Hinzufügen der Aufgabe:', error);
      alert('Fehler beim Hinzufügen der Aufgabe. Bitte versuche es erneut.');
    }
  };

  const deleteTask = async (taskId) => {
    try {
      await axios.delete(`${API}/tasks/${taskId}`);
      loadData();
    } catch (error) {
      console.error('Fehler beim Löschen der Aufgabe:', error);
    }
  };

  const handleStarClick = async (taskId, day, stars) => {
    try {
      await axios.post(`${API}/stars/${taskId}/${day}?stars=${stars}`);
      loadData();
    } catch (error) {
      console.error('Fehler beim Aktualisieren der Sterne:', error);
    }
  };

  const addReward = async () => {
    const rewardName = newRewardName.trim();
    const rewardStars = parseInt(newRewardStars);
    
    if (!rewardName) {
      alert('Bitte gib einen Belohnungsnamen ein!');
      return;
    }
    
    if (!rewardStars || rewardStars < 1) {
      alert('Bitte gib eine gültige Anzahl Sterne ein (mindestens 1)!');
      return;
    }
    
    try {
      const response = await axios.post(`${API}/rewards`, { 
        name: rewardName, 
        required_stars: rewardStars
      });
      
      if (response.status === 200) {
        setNewRewardName('');
        setNewRewardStars('');
        await loadData();
        console.log('Belohnung erfolgreich hinzugefügt:', rewardName, rewardStars);
      }
    } catch (error) {
      console.error('Fehler beim Hinzufügen der Belohnung:', error);
      alert('Fehler beim Hinzufügen der Belohnung. Bitte versuche es erneut.');
    }
  };

  const claimReward = async (rewardId) => {
    const reward = rewards.find(r => r.id === rewardId);
    if (!reward) return;

    if (progress.available_stars < reward.required_stars) {
      setRewardClaimError({
        rewardName: reward.name,
        requiredStars: reward.required_stars,
        availableStars: progress.available_stars
      });
      return;
    }

    try {
      await axios.post(`${API}/rewards/${rewardId}/claim`);
      loadData();
    } catch (error) {
      console.error('Fehler beim Einlösen der Belohnung:', error);
      setRewardClaimError({
        rewardName: reward.name,
        requiredStars: reward.required_stars,
        availableStars: progress.available_stars
      });
    }
  };

  const addTaskStarsToAvailable = async () => {
    if (progress.total_stars === 0) {
      alert('Keine Aufgaben-Sterne verfügbar!');
      return;
    }

    const maxAvailable = progress.total_stars;
    const starsToAdd = prompt(`Wie viele Aufgaben-Sterne zu verfügbaren Sternen hinzufügen? (Verfügbar: ${maxAvailable})`);
    
    if (!starsToAdd) return;
    
    const amount = parseInt(starsToAdd);
    
    // Validation: Cannot add more than available
    if (amount > maxAvailable) {
      alert(`Du hast nur ${maxAvailable} Aufgaben-Sterne! Du kannst nicht mehr verschieben als du besitzt.`);
      return;
    }
    
    if (amount <= 0) {
      alert('Bitte gib eine gültige Anzahl ein!');
      return;
    }
    
    try {
      // Move stars from total_stars to available_stars by adding to safe first, then withdrawing
      await axios.post(`${API}/progress/add-to-safe?stars=${amount}`);
      await axios.post(`${API}/progress/withdraw-from-safe?stars=${amount}`);
      loadData();
    } catch (error) {
      console.error('Fehler beim Verschieben der Sterne:', error);
      alert('Fehler beim Verschieben der Sterne!');
      loadData(); // Reload in case of inconsistent state
    }
  };

  const addStarsToSafe = async () => {
    if (progress.total_stars === 0) {
      alert('Keine Sterne verfügbar, um sie in den Tresor zu legen!');
      return;
    }
    
    const maxAvailable = progress.total_stars;
    const starsToAdd = prompt(`Wie viele Sterne in den Tresor legen? (Verfügbar: ${maxAvailable})`);
    
    if (!starsToAdd) return;
    
    const amount = parseInt(starsToAdd);
    
    // Validation: Cannot add more than available
    if (amount > maxAvailable) {
      alert(`Du hast nur ${maxAvailable} Sterne verfügbar! Du kannst nicht mehr in den Tresor legen als du besitzt.`);
      return;
    }
    
    if (amount <= 0) {
      alert('Bitte gib eine gültige Anzahl ein!');
      return;
    }
    
    try {
      await axios.post(`${API}/progress/add-to-safe?stars=${amount}`);
      loadData();
    } catch (error) {
      console.error('Fehler beim Hinzufügen von Sternen zum Tresor:', error);
      if (error.response?.data?.detail) {
        alert(error.response.data.detail);
      } else {
        alert('Nicht genügend Sterne verfügbar!');
      }
      loadData(); // Reload to fix any inconsistent state
    }
  };

  const withdrawFromSafe = async (amount) => {
    try {
      await axios.post(`${API}/progress/withdraw-from-safe?stars=${amount}`);
      loadData();
      setShowSafe(false);
    } catch (error) {
      console.error('Fehler beim Abheben aus dem Tresor:', error);
      alert('Fehler beim Abheben der Sterne!');
    }
  };

  const resetWeek = async () => {
    if (confirm('Bist du sicher, dass du die Woche zurücksetzen möchtest?\n\nDies löscht:\n• Alle Aufgaben-Sterne der aktuellen Woche\n• Alle verfügbaren Sterne\n\nDer Tresor bleibt unverändert!')) {
      try {
        await axios.post(`${API}/progress/reset`);
        loadData();
        alert('Woche wurde zurückgesetzt. Tresor-Sterne wurden beibehalten!');
      } catch (error) {
        console.error('Fehler beim Zurücksetzen der Woche:', error);
        alert('Fehler beim Zurücksetzen der Woche!');
      }
    }
  };

  const resetAllStars = async () => {
    const confirmMessage = 'Bist du sicher, dass du ALLE Sterne zurücksetzen möchtest?\n\n' +
                          'Das wird löschen:\n' +
                          '• Alle Aufgaben-Sterne\n' +
                          '• Alle verfügbaren Sterne\n' +
                          '• Alle Sterne im Tresor\n' +
                          '• Alle beanspruchten Belohnungen\n\n' +
                          'Diese Aktion kann nicht rückgängig gemacht werden!';
    
    if (confirm(confirmMessage)) {
      try {
        await axios.post(`${API}/progress/reset-all-stars`);
        loadData();
        alert('Alle Sterne wurden erfolgreich zurückgesetzt!');
      } catch (error) {
        console.error('Fehler beim Zurücksetzen aller Sterne:', error);
        alert('Fehler beim Zurücksetzen der Sterne!');
      }
    }
  };

  const deleteAllRewards = async () => {
    const confirmMessage = 'Bist du sicher, dass du ALLE Belohnungen löschen möchtest?\n\n' +
                          'Diese Aktion kann nicht rückgängig gemacht werden!';
    
    if (confirm(confirmMessage)) {
      try {
        await axios.delete(`${API}/rewards/all`);
        loadData();
        alert('Alle Belohnungen wurden erfolgreich gelöscht!');
      } catch (error) {
        console.error('Fehler beim Löschen aller Belohnungen:', error);
        alert('Fehler beim Löschen der Belohnungen!');
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 flex items-center justify-center">
        <div className="text-2xl text-purple-600">Lade deinen Stern-Tracker...</div>
      </div>
    );
  }

  const days = ['Aufgabe', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="text-center py-8 relative">
          <h1 className="text-4xl font-bold text-purple-800 mb-2">⭐ Wöchentlicher Stern-Tracker ⭐</h1>
          <p className="text-purple-600">Erfülle deine Aufgaben und sammle Sterne für tolle Belohnungen!</p>
          
          {/* Reset All Stars Button - Top Right */}
          <button
            onClick={resetAllStars}
            className="absolute top-0 right-0 bg-red-500 text-white px-3 py-2 rounded-lg hover:bg-red-600 transition-colors text-sm font-medium shadow-md"
            title="Alle Sterne zurücksetzen"
          >
            🗑️ Alle Zurücksetzen
          </button>
        </div>

        {/* Stars Summary */}
        <StarsSummary 
          taskStars={progress.total_stars}
          availableStars={progress.available_stars || 0}
          onAddTaskStarsToAvailable={addTaskStarsToAvailable}
        />

        {/* Math Challenge Button - Large and Prominent */}
        <div className="flex justify-center mb-6">
          <button 
            onClick={() => setShowMathChallenge(true)}
            className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-12 py-6 rounded-2xl text-xl font-bold hover:from-green-600 hover:to-emerald-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            🧮 Mathe-Herausforderung Starten
          </button>
        </div>

        {/* Progress Section */}
        <ProgressBar 
          current={progress.total_stars} 
          total={progress.total_stars + progress.stars_in_safe}
          starsInSafe={progress.stars_in_safe}
          onOpenSafe={() => setShowSafe(true)}
          onAddToSafe={addStarsToSafe}
          onResetWeek={resetWeek}
        />

        {/* Task Management */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-purple-100">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-purple-800">Meine Aufgaben</h2>
            <div className="flex space-x-2">
              <button 
                onClick={() => setShowMathSettings(true)}
                className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
              >
                ⚙️ Mathe-Einstellungen
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-8 gap-4 p-4 bg-purple-100 rounded-xl font-semibold text-purple-800 mb-4">
            {days.map(day => (
              <div key={day} className="text-center">{day}</div>
            ))}
          </div>
          
          <div className="space-y-3">
            {tasks.map(task => (
              <div key={task.id} className="relative group">
                <TaskRow 
                  task={task} 
                  weekStars={weekStars} 
                  onStarClick={handleStarClick}
                />
                <button 
                  onClick={() => deleteTask(task.id)}
                  className="absolute -right-2 -top-2 bg-red-500 text-white rounded-full w-6 h-6 text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
          
          <div className="flex space-x-2 mt-4">
            <input
              type="text"
              placeholder="Neue Aufgabe hinzufügen..."
              value={newTaskName}
              onChange={(e) => setNewTaskName(e.target.value)}
              className="flex-1 p-3 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addTask();
                }
              }}
            />
            <button 
              onClick={(e) => {
                e.preventDefault();
                addTask();
              }}
              className="bg-purple-500 text-white px-6 py-3 rounded-lg hover:bg-purple-600 transition-colors font-medium"
              disabled={!newTaskName.trim()}
            >
              Aufgabe Hinzufügen
            </button>
          </div>
        </div>

        {/* Rewards Section */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-purple-100">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-purple-800">🎁 Belohnungen</h2>
            <button
              onClick={deleteAllRewards}
              className="bg-red-500 text-white px-3 py-2 rounded-lg hover:bg-red-600 transition-colors text-sm"
              title="Alle Belohnungen löschen"
            >
              🗑️ Alle Löschen
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            {rewards.map(reward => (
              <div key={reward.id} className={`p-4 rounded-xl border-2 transition-all ${
                reward.is_claimed 
                  ? 'bg-gray-100 border-gray-300 text-gray-500' 
                  : 'bg-gradient-to-r from-yellow-50 to-orange-50 border-yellow-300 text-purple-800'
              }`}>
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="font-semibold">{reward.name}</h3>
                    <p className="text-sm">{reward.required_stars} ⭐</p>
                  </div>
                  {!reward.is_claimed && (
                    <button 
                      onClick={() => claimReward(reward.id)}
                      className="bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-600 transition-colors text-sm"
                    >
                      Einlösen!
                    </button>
                  )}
                  {reward.is_claimed && (
                    <div className="text-green-600 font-semibold">✓ Eingelöst</div>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          <div className="flex space-x-2">
            <input
              type="text"
              placeholder="Belohnungsname..."
              value={newRewardName}
              onChange={(e) => setNewRewardName(e.target.value)}
              className="flex-1 p-3 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
            />
            <input
              type="number"
              min="1"
              placeholder="Benötigte Sterne"
              value={newRewardStars}
              onChange={(e) => setNewRewardStars(e.target.value)}
              className="w-32 p-3 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
            />
            <button 
              onClick={(e) => {
                e.preventDefault();
                addReward();
              }}
              className="bg-yellow-500 text-white px-6 py-3 rounded-lg hover:bg-yellow-600 transition-colors font-medium"
              disabled={!newRewardName.trim() || !newRewardStars || parseInt(newRewardStars) < 1}
            >
              Belohnung Hinzufügen
            </button>
          </div>
        </div>
        
        {/* Modals */}
        {showMathChallenge && (
          <MathChallenge 
            onClose={() => setShowMathChallenge(false)}
            onComplete={loadData}
          />
        )}
        
        {showSafe && (
          <SafeModal
            isOpen={showSafe}
            onClose={() => setShowSafe(false)}
            starsInSafe={progress.stars_in_safe}
            onWithdraw={withdrawFromSafe}
          />
        )}
        
        {showMathSettings && (
          <MathSettingsModal
            isOpen={showMathSettings}
            onClose={() => setShowMathSettings(false)}
            onComplete={loadData}
          />
        )}

        {rewardClaimError && (
          <RewardClaimErrorModal
            isOpen={true}
            onClose={() => setRewardClaimError(null)}
            rewardName={rewardClaimError.rewardName}
            requiredStars={rewardClaimError.requiredStars}
            availableStars={rewardClaimError.availableStars}
          />
        )}
      </div>
    </div>
  );
}

export default App;