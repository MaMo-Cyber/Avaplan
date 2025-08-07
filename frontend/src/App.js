import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import StarTransferModal from "./components/StarTransferModal";
import AdminSettingsModal from "./components/AdminSettingsModal";
import { mockApi, isMockMode } from "./mockApi";

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
const ProgressBar = ({ current, total, starsInSafe, onOpenSafe, onAddToSafe, onOpenAdminSettings }) => {
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
          className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors"
          onClick={onOpenAdminSettings}
        >
          ⚙️ Verwaltung
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

// English Settings Modal Component
const EnglishSettingsModal = ({ isOpen, onClose, onComplete }) => {
  const [activeTab, setActiveTab] = useState('settings');
  const [settings, setSettings] = useState({
    problem_count: 15,
    star_tiers: {"90": 3, "80": 2, "70": 1},
    problem_types: {
      vocabulary_de_en: true,
      vocabulary_en_de: true,
      simple_sentences: true,
      basic_grammar: false,
      colors_numbers: true,
      animals_objects: true
    },
    difficulty_settings: {
      vocabulary_level: "basic",
      include_articles: false,
      sentence_complexity: "simple"
    }
  });
  const [statistics, setStatistics] = useState({
    total_attempts: 0,
    grade_2_attempts: 0,
    grade_3_attempts: 0,
    total_correct: 0,
    total_wrong: 0,
    average_score: 0.0,
    best_score: 0.0,
    total_stars_earned: 0,
    problem_type_stats: {}
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
      loadStatistics();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    try {
      const response = await axios.get(`${API}/english/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error('Fehler beim Laden der Englisch-Einstellungen:', error);
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await axios.get(`${API}/english/statistics`);
      setStatistics(response.data);
    } catch (error) {
      console.error('Fehler beim Laden der Englisch-Statistiken:', error);
    }
  };

  const updateSettings = async () => {
    setLoading(true);
    try {
      await axios.put(`${API}/english/settings`, settings);
      onComplete && onComplete();
      alert('Englisch-Einstellungen erfolgreich gespeichert!');
    } catch (error) {
      console.error('Fehler beim Speichern der Einstellungen:', error);
      alert('Fehler beim Speichern der Einstellungen!');
    }
    setLoading(false);
  };

  const resetStatistics = async () => {
    if (confirm('Bist du sicher, dass du alle Englisch-Statistiken zurücksetzen möchtest? Diese Aktion kann nicht rückgängig gemacht werden!')) {
      try {
        await axios.post(`${API}/english/statistics/reset`);
        await loadStatistics();
        alert('Englisch-Statistiken erfolgreich zurückgesetzt!');
      } catch (error) {
        console.error('Fehler beim Zurücksetzen der Statistiken:', error);
        alert('Fehler beim Zurücksetzen der Statistiken!');
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
    const percentage = prompt('Prozentsatz eingeben (z.B. 95):');
    const stars = prompt('Anzahl Sterne eingeben:');
    
    if (percentage && stars) {
      const newTiers = { ...settings.star_tiers };
      newTiers[percentage] = parseInt(stars);
      setSettings({ ...settings, star_tiers: newTiers });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-xl p-8 max-w-4xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-green-800">Englisch-Herausforderung Einstellungen</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-4 mb-6 border-b">
          <button
            onClick={() => setActiveTab('settings')}
            className={`pb-2 px-4 font-semibold ${
              activeTab === 'settings' 
                ? 'text-green-600 border-b-2 border-green-600' 
                : 'text-gray-500 hover:text-green-500'
            }`}
          >
            ⚙️ Einstellungen
          </button>
          <button
            onClick={() => setActiveTab('statistics')}
            className={`pb-2 px-4 font-semibold ${
              activeTab === 'statistics' 
                ? 'text-green-600 border-b-2 border-green-600' 
                : 'text-gray-500 hover:text-green-500'
            }`}
          >
            📊 Statistiken
          </button>
        </div>

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="space-y-6">
            {/* Problem Count */}
            <div>
              <h3 className="text-lg font-semibold text-green-800 mb-3">📝 Aufgaben-Anzahl</h3>
              <div className="flex items-center space-x-3">
                <label className="font-medium">Anzahl der Englisch-Aufgaben pro Herausforderung:</label>
                <input
                  type="number"
                  min="10"
                  max="30"
                  value={settings.problem_count}
                  onChange={(e) => setSettings({...settings, problem_count: parseInt(e.target.value)})}
                  className="w-20 p-2 border border-green-300 rounded focus:outline-none focus:border-green-500"
                />
              </div>
            </div>

            {/* Problem Types */}
            <div>
              <h3 className="text-lg font-semibold text-green-800 mb-3">🇬🇧 Aufgaben-Typen</h3>
              <p className="text-sm text-gray-600 mb-4">Wähle die Arten von Englisch-Aufgaben aus:</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(settings.problem_types).map(([type, enabled]) => {
                  const typeLabels = {
                    vocabulary_de_en: "🇩🇪→🇬🇧 Deutsch zu Englisch Vokabeln",
                    vocabulary_en_de: "🇬🇧→🇩🇪 Englisch zu Deutsch Vokabeln",
                    simple_sentences: "📝 Einfache Sätze übersetzen",
                    basic_grammar: "📐 Grundlegende Grammatik",
                    colors_numbers: "🎨 Farben und Zahlen",
                    animals_objects: "🐕 Tiere und Gegenstände"
                  };
                  
                  return (
                    <label key={type} className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={enabled}
                        onChange={(e) => setSettings({
                          ...settings,
                          problem_types: {
                            ...settings.problem_types,
                            [type]: e.target.checked
                          }
                        })}
                        className="w-4 h-4 text-green-600 rounded"
                      />
                      <span className="text-sm">{typeLabels[type] || type}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Difficulty Settings */}
            <div>
              <h3 className="text-lg font-semibold text-green-800 mb-3">⚖️ Schwierigkeitseinstellungen</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block font-medium mb-2">Vokabel-Level:</label>
                  <select
                    value={settings.difficulty_settings.vocabulary_level}
                    onChange={(e) => setSettings({
                      ...settings,
                      difficulty_settings: {
                        ...settings.difficulty_settings,
                        vocabulary_level: e.target.value
                      }
                    })}
                    className="p-2 border border-green-300 rounded focus:outline-none focus:border-green-500"
                  >
                    <option value="basic">Grundwortschatz</option>
                    <option value="intermediate">Erweitert</option>
                  </select>
                </div>
                
                <div>
                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.difficulty_settings.include_articles}
                      onChange={(e) => setSettings({
                        ...settings,
                        difficulty_settings: {
                          ...settings.difficulty_settings,
                          include_articles: e.target.checked
                        }
                      })}
                      className="w-4 h-4 text-green-600 rounded"
                    />
                    <span>Deutsche Artikel (der/die/das) mit einbeziehen</span>
                  </label>
                </div>
                
                <div>
                  <label className="block font-medium mb-2">Satz-Komplexität:</label>
                  <select
                    value={settings.difficulty_settings.sentence_complexity}
                    onChange={(e) => setSettings({
                      ...settings,
                      difficulty_settings: {
                        ...settings.difficulty_settings,
                        sentence_complexity: e.target.value
                      }
                    })}
                    className="p-2 border border-green-300 rounded focus:outline-none focus:border-green-500"
                  >
                    <option value="simple">Einfach</option>
                    <option value="medium">Mittel</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Star Rewards */}
            <div>
              <h3 className="text-lg font-semibold text-green-800 mb-3">⭐ Sternen-Belohnungs-Stufen</h3>
              <p className="text-sm text-gray-600 mb-4">Bestimme, wie viele Sterne basierend auf der Prozentscore vergeben werden</p>
              
              <div className="space-y-3">
                {Object.entries(settings.star_tiers).map(([percentage, stars]) => (
                  <div key={percentage} className="flex items-center space-x-3 bg-green-50 p-3 rounded-lg">
                    <span className="font-medium">{percentage}% oder höher:</span>
                    <input
                      type="number"
                      value={stars}
                      onChange={(e) => updateStarTier(percentage, parseInt(e.target.value))}
                      className="w-20 p-2 border border-green-300 rounded focus:outline-none focus:border-green-500"
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
                className="px-6 py-2 border border-green-300 text-green-600 rounded-lg hover:bg-green-50 transition-colors"
              >
                Abbrechen
              </button>
              <button 
                onClick={updateSettings}
                disabled={loading}
                className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50"
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
                <h3 className="text-lg font-semibold text-green-800 mb-4">📚 Klassen-Aufschlüsselung</h3>
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
                <h3 className="text-lg font-semibold text-green-800 mb-4">🎯 Antworten-Aufschlüsselung</h3>
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

            {/* Problem Type Stats */}
            {Object.keys(statistics.problem_type_stats).length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold text-green-800 mb-4">📊 Aufgaben-Typ Statistiken</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(statistics.problem_type_stats).map(([type, stats]) => {
                    const typeLabels = {
                      vocabulary_de_en: "DE→EN Vokabeln",
                      vocabulary_en_de: "EN→DE Vokabeln",
                      simple_sentences: "Einfache Sätze",
                      basic_grammar: "Grundgrammatik",
                      colors_numbers: "Farben & Zahlen",
                      animals_objects: "Tiere & Objekte"
                    };
                    
                    const accuracy = stats.total_attempts > 0 
                      ? ((stats.correct / stats.total_attempts) * 100).toFixed(1)
                      : 0;
                    
                    return (
                      <div key={type} className="bg-green-50 p-3 rounded-lg">
                        <h4 className="font-semibold text-green-800">{typeLabels[type] || type}</h4>
                        <div className="text-sm space-y-1">
                          <div>Versuche: {stats.total_attempts}</div>
                          <div className="text-green-600">Richtig: {stats.correct}</div>
                          <div className="text-red-600">Falsch: {stats.wrong}</div>
                          <div>Genauigkeit: {accuracy}%</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-4">
              <button
                onClick={resetStatistics}
                className="bg-red-500 text-white px-6 py-2 rounded-lg hover:bg-red-600 transition-colors"
              >
                Statistiken Zurücksetzen
              </button>
              <button 
                onClick={onClose}
                className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition-colors"
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

// German Settings Modal Component
const GermanSettingsModal = ({ isOpen, onClose, onComplete }) => {
  const [activeTab, setActiveTab] = useState('settings');
  const [settings, setSettings] = useState({
    problem_count: 20,
    star_tiers: {"90": 3, "80": 2, "70": 1},
    problem_types: {
      spelling: true,
      word_types: true,
      fill_blank: true,
      grammar: false,
      articles: false,
      sentence_order: false
    },
    difficulty_settings: {
      spelling_difficulty: "medium",
      word_types_include_adjectives: true,
      fill_blank_context_length: "short"
    }
  });
  const [statistics, setStatistics] = useState({
    total_attempts: 0,
    grade_2_attempts: 0,
    grade_3_attempts: 0,
    total_correct: 0,
    total_wrong: 0,
    average_score: 0.0,
    best_score: 0.0,
    total_stars_earned: 0,
    problem_type_stats: {}
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadSettings();
      loadStatistics();
    }
  }, [isOpen]);

  const loadSettings = async () => {
    try {
      const response = await axios.get(`${API}/german/settings`);
      setSettings(response.data);
    } catch (error) {
      console.error('Fehler beim Laden der Deutsch-Einstellungen:', error);
    }
  };

  const loadStatistics = async () => {
    try {
      const response = await axios.get(`${API}/german/statistics`);
      setStatistics(response.data);
    } catch (error) {
      console.error('Fehler beim Laden der Deutsch-Statistiken:', error);
    }
  };

  const updateSettings = async () => {
    setLoading(true);
    try {
      await axios.put(`${API}/german/settings`, settings);
      onComplete && onComplete();
      alert('Deutsch-Einstellungen erfolgreich gespeichert!');
    } catch (error) {
      console.error('Fehler beim Speichern der Einstellungen:', error);
      alert('Fehler beim Speichern der Einstellungen!');
    }
    setLoading(false);
  };

  const resetStatistics = async () => {
    if (confirm('Bist du sicher, dass du alle Deutsch-Statistiken zurücksetzen möchtest? Diese Aktion kann nicht rückgängig gemacht werden!')) {
      try {
        await axios.post(`${API}/german/statistics/reset`);
        await loadStatistics();
        alert('Deutsch-Statistiken erfolgreich zurückgesetzt!');
      } catch (error) {
        console.error('Fehler beim Zurücksetzen der Statistiken:', error);
        alert('Fehler beim Zurücksetzen der Statistiken!');
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
    const percentage = prompt('Prozentsatz eingeben (z.B. 95):');
    const stars = prompt('Anzahl Sterne eingeben:');
    
    if (percentage && stars) {
      const newTiers = { ...settings.star_tiers };
      newTiers[percentage] = parseInt(stars);
      setSettings({ ...settings, star_tiers: newTiers });
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-xl p-8 max-w-4xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-blue-800">Deutsch-Herausforderung Einstellungen</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-4 mb-6 border-b">
          <button
            onClick={() => setActiveTab('settings')}
            className={`pb-2 px-4 font-semibold ${
              activeTab === 'settings' 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-blue-500'
            }`}
          >
            ⚙️ Einstellungen
          </button>
          <button
            onClick={() => setActiveTab('statistics')}
            className={`pb-2 px-4 font-semibold ${
              activeTab === 'statistics' 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-blue-500'
            }`}
          >
            📊 Statistiken
          </button>
        </div>

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="space-y-6">
            {/* Problem Count */}
            <div>
              <h3 className="text-lg font-semibold text-blue-800 mb-3">📝 Aufgaben-Anzahl</h3>
              <div className="flex items-center space-x-3">
                <label className="font-medium">Anzahl der Deutsch-Aufgaben pro Herausforderung:</label>
                <input
                  type="number"
                  min="10"
                  max="50"
                  value={settings.problem_count}
                  onChange={(e) => setSettings({...settings, problem_count: parseInt(e.target.value)})}
                  className="w-20 p-2 border border-blue-300 rounded focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>

            {/* Problem Types */}
            <div>
              <h3 className="text-lg font-semibold text-blue-800 mb-3">📚 Aufgaben-Typen</h3>
              <p className="text-sm text-gray-600 mb-4">Wähle die Arten von Deutsch-Aufgaben aus:</p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(settings.problem_types).map(([type, enabled]) => {
                  const typeLabels = {
                    spelling: "✏️ Rechtschreibung",
                    word_types: "🔤 Wortarten (Nomen, Verben, Adjektive)",
                    fill_blank: "📋 Lückentexte",
                    grammar: "📐 Grammatik",
                    articles: "📄 Artikel (der, die, das)",
                    sentence_order: "🔢 Satzstellung"
                  };
                  
                  return (
                    <label key={type} className="flex items-center space-x-3">
                      <input
                        type="checkbox"
                        checked={enabled}
                        onChange={(e) => setSettings({
                          ...settings,
                          problem_types: {
                            ...settings.problem_types,
                            [type]: e.target.checked
                          }
                        })}
                        className="w-4 h-4 text-blue-600 rounded"
                      />
                      <span>{typeLabels[type] || type}</span>
                    </label>
                  );
                })}
              </div>
            </div>

            {/* Difficulty Settings */}
            <div>
              <h3 className="text-lg font-semibold text-blue-800 mb-3">⚖️ Schwierigkeitseinstellungen</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block font-medium mb-2">Rechtschreibung Schwierigkeit:</label>
                  <select
                    value={settings.difficulty_settings.spelling_difficulty}
                    onChange={(e) => setSettings({
                      ...settings,
                      difficulty_settings: {
                        ...settings.difficulty_settings,
                        spelling_difficulty: e.target.value
                      }
                    })}
                    className="p-2 border border-blue-300 rounded focus:outline-none focus:border-blue-500"
                  >
                    <option value="easy">Einfach</option>
                    <option value="medium">Mittel</option>
                    <option value="hard">Schwer</option>
                  </select>
                </div>
                
                <div>
                  <label className="flex items-center space-x-3">
                    <input
                      type="checkbox"
                      checked={settings.difficulty_settings.word_types_include_adjectives}
                      onChange={(e) => setSettings({
                        ...settings,
                        difficulty_settings: {
                          ...settings.difficulty_settings,
                          word_types_include_adjectives: e.target.checked
                        }
                      })}
                      className="w-4 h-4 text-blue-600 rounded"
                    />
                    <span>Adjektive in Wortarten-Aufgaben einschließen</span>
                  </label>
                </div>
                
                <div>
                  <label className="block font-medium mb-2">Lückentext Kontext-Länge:</label>
                  <select
                    value={settings.difficulty_settings.fill_blank_context_length}
                    onChange={(e) => setSettings({
                      ...settings,
                      difficulty_settings: {
                        ...settings.difficulty_settings,
                        fill_blank_context_length: e.target.value
                      }
                    })}
                    className="p-2 border border-blue-300 rounded focus:outline-none focus:border-blue-500"
                  >
                    <option value="short">Kurz</option>
                    <option value="medium">Mittel</option>
                    <option value="long">Lang</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Star Rewards */}
            <div>
              <h3 className="text-lg font-semibold text-blue-800 mb-3">⭐ Sternen-Belohnungs-Stufen</h3>
              <p className="text-sm text-gray-600 mb-4">Bestimme, wie viele Sterne basierend auf der Prozentscore vergeben werden</p>
              
              <div className="space-y-3">
                {Object.entries(settings.star_tiers).map(([percentage, stars]) => (
                  <div key={percentage} className="flex items-center space-x-3 bg-blue-50 p-3 rounded-lg">
                    <span className="font-medium">{percentage}% oder höher:</span>
                    <input
                      type="number"
                      value={stars}
                      onChange={(e) => updateStarTier(percentage, parseInt(e.target.value))}
                      className="w-20 p-2 border border-blue-300 rounded focus:outline-none focus:border-blue-500"
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
                className="px-6 py-2 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
              >
                Abbrechen
              </button>
              <button 
                onClick={updateSettings}
                disabled={loading}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
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
                <h3 className="text-lg font-semibold text-blue-800 mb-4">📚 Klassen-Aufschlüsselung</h3>
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
                <h3 className="text-lg font-semibold text-blue-800 mb-4">🎯 Antworten-Aufschlüsselung</h3>
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

            {/* Problem Type Stats */}
            {Object.keys(statistics.problem_type_stats).length > 0 && (
              <div className="card">
                <h3 className="text-lg font-semibold text-blue-800 mb-4">📊 Aufgaben-Typ Statistiken</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(statistics.problem_type_stats).map(([type, stats]) => {
                    const typeLabels = {
                      spelling: "Rechtschreibung",
                      word_types: "Wortarten",
                      fill_blank: "Lückentexte",
                      grammar: "Grammatik",
                      articles: "Artikel",
                      sentence_order: "Satzstellung"
                    };
                    
                    const accuracy = stats.total_attempts > 0 
                      ? ((stats.correct / stats.total_attempts) * 100).toFixed(1)
                      : 0;
                    
                    return (
                      <div key={type} className="bg-blue-50 p-3 rounded-lg">
                        <h4 className="font-semibold text-blue-800">{typeLabels[type] || type}</h4>
                        <div className="text-sm space-y-1">
                          <div>Versuche: {stats.total_attempts}</div>
                          <div className="text-green-600">Richtig: {stats.correct}</div>
                          <div className="text-red-600">Falsch: {stats.wrong}</div>
                          <div>Genauigkeit: {accuracy}%</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="flex justify-end space-x-4">
              <button
                onClick={resetStatistics}
                className="bg-red-500 text-white px-6 py-2 rounded-lg hover:bg-red-600 transition-colors"
              >
                Statistiken Zurücksetzen
              </button>
              <button 
                onClick={onClose}
                className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
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

// Enhanced English Challenge Component
const EnglishChallenge = ({ onClose, onComplete }) => {
  const [grade, setGrade] = useState(null);
  const [challenge, setChallenge] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);

  const startChallenge = async (selectedGrade) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/english/challenge/${selectedGrade}`);
      setChallenge(response.data);
      setGrade(selectedGrade);
      setAnswers({});
    } catch (error) {
      console.error('Fehler beim Erstellen der Englisch-Herausforderung:', error);
      alert('Fehler beim Erstellen der Englisch-Herausforderung. Bitte versuche es erneut.');
    }
    setLoading(false);
  };

  const submitAnswers = async () => {
    if (!challenge) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/english/challenge/${challenge.id}/submit`, answers);
      setResult(response.data);
      setShowResults(true);
    } catch (error) {
      console.error('Fehler beim Einreichen der Antworten:', error);
      alert('Fehler beim Einreichen der Antworten. Bitte versuche es erneut.');
    }
    setLoading(false);
  };

  const allAnswersProvided = challenge && 
    challenge.problems && 
    Array.isArray(challenge.problems) && 
    Object.keys(answers).length === challenge.problems.length &&
    challenge.problems.every((_, index) => answers[index] !== undefined && answers[index] !== '');

  // Results Detail Page
  if (showResults && result) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
        <div className="bg-white rounded-xl p-8 max-w-4xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
          <div className="text-center mb-6">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold text-green-800 mb-4">Excellent English Work!</h2>
            <div className="space-y-2 mb-6">
              <p>Richtige Antworten: {result.correct_answers}/{result.total_problems}</p>
              <p>Score: {result.percentage.toFixed(1)}%</p>
              <p className="text-lg font-semibold text-yellow-600">
                Verdiente Sterne: {result.stars_earned} ⭐
              </p>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-semibold text-green-800 mb-4">Überprüfe deine Englisch-Antworten:</h3>
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
                  
                  <p className="mb-2 font-medium whitespace-pre-line">{problem.question}</p>
                  
                  {/* Show options for multiple choice */}
                  {problem.options && (
                    <div className="mb-2 text-sm">
                      <p className="font-medium">Optionen:</p>
                      <div className="flex flex-wrap gap-2">
                        {problem.options.map((option, optIndex) => (
                          <span 
                            key={optIndex}
                            className={`px-2 py-1 rounded text-xs ${
                              option === problem.correct_answer 
                                ? 'bg-green-100 text-green-800' 
                                : option === problem.user_answer 
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {option}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
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
              className="bg-green-500 text-white px-8 py-3 rounded-lg hover:bg-green-600 transition-colors text-lg"
            >
              Great! Weiter
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
            <h2 className="text-2xl font-bold text-green-800 mb-4">Excellent English Work!</h2>
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
                className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition-colors"
              >
                Antworten Überprüfen
              </button>
              <button 
                onClick={() => {
                  onComplete();
                  onClose();
                }}
                className="bg-green-500 text-white px-6 py-2 rounded-lg hover:bg-green-600 transition-colors"
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
            <h2 className="text-xl font-bold text-green-800">Englisch Klasse {grade} Herausforderung</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
          </div>
          
          <div className="mb-4 text-sm text-gray-600">
            Fülle ALLE Antworten aus, um die Einreichung zu aktivieren. Antworten ausgefüllt: {Object.keys(answers).length}/{challenge.problems ? challenge.problems.length : 0}
            <br />
            <span className="text-green-600 font-medium">Insgesamt {challenge.problems ? challenge.problems.length : 0} English Aufgaben</span>
          </div>
          
          <div className="grid grid-cols-1 gap-4 mb-6">
            {challenge.problems.map((problem, index) => (
              <div key={index} className={`p-4 border-2 rounded-lg transition-colors ${
                answers[index] !== undefined && answers[index] !== '' 
                  ? 'border-green-300 bg-green-50' 
                  : 'border-green-200 bg-white'
              }`}>
                <p className="mb-3 font-medium whitespace-pre-line">{index + 1}. {problem.question}</p>
                
                {/* Multiple Choice Questions */}
                {problem.options && problem.options.length > 0 && (
                  <div className="space-y-2">
                    {problem.options.map((option, optIndex) => (
                      <label key={optIndex} className="flex items-center space-x-3 cursor-pointer hover:bg-green-50 p-2 rounded">
                        <input
                          type="radio"
                          name={`question-${index}`}
                          value={option}
                          checked={answers[index] === option}
                          onChange={(e) => {
                            setAnswers({...answers, [index]: e.target.value});
                          }}
                          className="w-4 h-4 text-green-600"
                        />
                        <span className="text-sm">{option}</span>
                      </label>
                    ))}
                  </div>
                )}
                
                {/* Text Input Questions */}
                {(!problem.options || problem.options.length === 0) && (
                  <input
                    type="text"
                    className="w-full p-2 border border-green-300 rounded focus:outline-none focus:border-green-500"
                    placeholder="Deine Antwort"
                    value={answers[index] || ''}
                    onChange={(e) => {
                      setAnswers({...answers, [index]: e.target.value});
                    }}
                  />
                )}
              </div>
            ))}
          </div>
          
          <div className="flex justify-end space-x-4">
            <button 
              onClick={onClose}
              className="px-6 py-2 border border-green-300 text-green-600 rounded-lg hover:bg-green-50 transition-colors"
            >
              Abbrechen
            </button>
            <button 
              onClick={submitAnswers}
              disabled={loading || !allAnswersProvided}
              className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Einreichen...' : `Alle Antworten Einreichen (${Object.keys(answers).length}/${challenge.problems ? challenge.problems.length : 0})`}
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
          <h2 className="text-2xl font-bold text-green-800 mb-6">Verdiene Extra-Sterne mit Englisch!</h2>
          <p className="text-gray-600 mb-6">Wähle deine Englisch-Klassenstufe:</p>
          <div className="space-y-4">
            <button 
              onClick={() => startChallenge(2)}
              disabled={loading}
              className="w-full p-4 bg-gradient-to-r from-green-400 to-teal-400 text-white rounded-xl hover:from-green-500 hover:to-teal-500 transition-all disabled:opacity-50"
            >
              🇬🇧 Englisch Klasse 2
            </button>
            <button 
              onClick={() => startChallenge(3)}
              disabled={loading}
              className="w-full p-4 bg-gradient-to-r from-emerald-400 to-green-400 text-white rounded-xl hover:from-emerald-500 hover:to-green-500 transition-all disabled:opacity-50"
            >
              🇺🇸 Englisch Klasse 3
            </button>
          </div>
          <button 
            onClick={onClose}
            className="mt-4 text-green-600 hover:text-green-800 transition-colors"
          >
            Vielleicht Später
          </button>
        </div>
      </div>
    </div>
  );
};

// Enhanced German Challenge Component
const GermanChallenge = ({ onClose, onComplete }) => {
  const [grade, setGrade] = useState(null);
  const [challenge, setChallenge] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [showResults, setShowResults] = useState(false);
  const [loading, setLoading] = useState(false);

  const startChallenge = async (selectedGrade) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/german/challenge/${selectedGrade}`);
      setChallenge(response.data);
      setGrade(selectedGrade);
      setAnswers({});
    } catch (error) {
      console.error('Fehler beim Erstellen der Deutsch-Herausforderung:', error);
      alert('Fehler beim Erstellen der Deutsch-Herausforderung. Bitte versuche es erneut.');
    }
    setLoading(false);
  };

  const submitAnswers = async () => {
    if (!challenge) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/german/challenge/${challenge.id}/submit`, answers);
      setResult(response.data);
      setShowResults(true);
    } catch (error) {
      console.error('Fehler beim Einreichen der Antworten:', error);
      alert('Fehler beim Einreichen der Antworten. Bitte versuche es erneut.');
    }
    setLoading(false);
  };

  const allAnswersProvided = challenge && 
    challenge.problems && 
    Array.isArray(challenge.problems) && 
    Object.keys(answers).length === challenge.problems.length &&
    challenge.problems.every((_, index) => answers[index] !== undefined && answers[index] !== '');

  // Results Detail Page
  if (showResults && result) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
        <div className="bg-white rounded-xl p-8 max-w-4xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
          <div className="text-center mb-6">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold text-blue-800 mb-4">Fantastische Deutsch-Arbeit!</h2>
            <div className="space-y-2 mb-6">
              <p>Richtige Antworten: {result.correct_answers}/{result.total_problems}</p>
              <p>Score: {result.percentage.toFixed(1)}%</p>
              <p className="text-lg font-semibold text-yellow-600">
                Verdiente Sterne: {result.stars_earned} ⭐
              </p>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-semibold text-blue-800 mb-4">Überprüfe deine Antworten:</h3>
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
                  
                  <p className="mb-2 font-medium whitespace-pre-line">{problem.question}</p>
                  
                  {/* Show options for multiple choice */}
                  {problem.options && (
                    <div className="mb-2 text-sm">
                      <p className="font-medium">Optionen:</p>
                      <div className="flex flex-wrap gap-2">
                        {problem.options.map((option, optIndex) => (
                          <span 
                            key={optIndex}
                            className={`px-2 py-1 rounded text-xs ${
                              option === problem.correct_answer 
                                ? 'bg-green-100 text-green-800' 
                                : option === problem.user_answer 
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {option}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                  
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
              className="bg-blue-500 text-white px-8 py-3 rounded-lg hover:bg-blue-600 transition-colors text-lg"
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
            <h2 className="text-2xl font-bold text-blue-800 mb-4">Fantastische Deutsch-Arbeit!</h2>
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
                className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
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
            <h2 className="text-xl font-bold text-blue-800">Deutsch Klasse {grade} Herausforderung</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
          </div>
          
          <div className="mb-4 text-sm text-gray-600">
            Fülle ALLE Antworten aus, um die Einreichung zu aktivieren. Antworten ausgefüllt: {Object.keys(answers).length}/{challenge.problems ? challenge.problems.length : 0}
            <br />
            <span className="text-blue-600 font-medium">Insgesamt {challenge.problems ? challenge.problems.length : 0} Aufgaben</span>
          </div>
          
          <div className="grid grid-cols-1 gap-4 mb-6">
            {challenge.problems.map((problem, index) => (
              <div key={index} className={`p-4 border-2 rounded-lg transition-colors ${
                answers[index] !== undefined && answers[index] !== '' 
                  ? 'border-green-300 bg-green-50' 
                  : 'border-blue-200 bg-white'
              }`}>
                <p className="mb-3 font-medium whitespace-pre-line">{index + 1}. {problem.question}</p>
                
                {/* Multiple Choice Questions */}
                {problem.options && problem.options.length > 0 && (
                  <div className="space-y-2">
                    {problem.options.map((option, optIndex) => (
                      <label key={optIndex} className="flex items-center space-x-3 cursor-pointer hover:bg-blue-50 p-2 rounded">
                        <input
                          type="radio"
                          name={`question-${index}`}
                          value={option}
                          checked={answers[index] === option}
                          onChange={(e) => {
                            setAnswers({...answers, [index]: e.target.value});
                          }}
                          className="w-4 h-4 text-blue-600"
                        />
                        <span className="text-sm">{option}</span>
                      </label>
                    ))}
                  </div>
                )}
                
                {/* Text Input Questions */}
                {(!problem.options || problem.options.length === 0) && (
                  <input
                    type="text"
                    className="w-full p-2 border border-blue-300 rounded focus:outline-none focus:border-blue-500"
                    placeholder="Deine Antwort"
                    value={answers[index] || ''}
                    onChange={(e) => {
                      setAnswers({...answers, [index]: e.target.value});
                    }}
                  />
                )}
              </div>
            ))}
          </div>
          
          <div className="flex justify-end space-x-4">
            <button 
              onClick={onClose}
              className="px-6 py-2 border border-blue-300 text-blue-600 rounded-lg hover:bg-blue-50 transition-colors"
            >
              Abbrechen
            </button>
            <button 
              onClick={submitAnswers}
              disabled={loading || !allAnswersProvided}
              className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Einreichen...' : `Alle Antworten Einreichen (${Object.keys(answers).length}/${challenge.problems ? challenge.problems.length : 0})`}
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
          <h2 className="text-2xl font-bold text-blue-800 mb-6">Verdiene Extra-Sterne mit Deutsch!</h2>
          <p className="text-gray-600 mb-6">Wähle deine Deutsch-Klassenstufe:</p>
          <div className="space-y-4">
            <button 
              onClick={() => startChallenge(2)}
              disabled={loading}
              className="w-full p-4 bg-gradient-to-r from-blue-400 to-cyan-400 text-white rounded-xl hover:from-blue-500 hover:to-cyan-500 transition-all disabled:opacity-50"
            >
              📖 Deutsch Klasse 2
            </button>
            <button 
              onClick={() => startChallenge(3)}
              disabled={loading}
              className="w-full p-4 bg-gradient-to-r from-indigo-400 to-blue-400 text-white rounded-xl hover:from-indigo-500 hover:to-blue-500 transition-all disabled:opacity-50"
            >
              📚 Deutsch Klasse 3
            </button>
          </div>
          <button 
            onClick={onClose}
            className="mt-4 text-blue-600 hover:text-blue-800 transition-colors"
          >
            Vielleicht Später
          </button>
        </div>
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
      
      // Handle the API response structure: { challenge: {...}, success: true }
      const challengeData = response.data.challenge || response.data;
      
      if (!challengeData.problems || !Array.isArray(challengeData.problems)) {
        throw new Error('Invalid challenge format: missing problems array');
      }
      
      setChallenge(challengeData);
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

  const allAnswersProvided = challenge && 
    challenge.problems && 
    Array.isArray(challenge.problems) && 
    Object.keys(answers).length === challenge.problems.length &&
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
            Fülle ALLE Antworten aus, um die Einreichung zu aktivieren. Antworten ausgefüllt: {Object.keys(answers).length}/{challenge.problems ? challenge.problems.length : 0}
            <br />
            <span className="text-purple-600 font-medium">Insgesamt {challenge.problems ? challenge.problems.length : 0} Aufgaben</span>
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
              {loading ? 'Einreichen...' : `Alle Antworten Einreichen (${Object.keys(answers).length}/${challenge.problems ? challenge.problems.length : 0})`}
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
  const [showGermanChallenge, setShowGermanChallenge] = useState(false);
  const [showEnglishChallenge, setShowEnglishChallenge] = useState(false);
  const [showSafe, setShowSafe] = useState(false);
  const [showStarTransfer, setShowStarTransfer] = useState(false);
  const [showMathSettings, setShowMathSettings] = useState(false);
  const [showGermanSettings, setShowGermanSettings] = useState(false);
  const [showEnglishSettings, setShowEnglishSettings] = useState(false);
  const [showAdminSettings, setShowAdminSettings] = useState(false);
  const [rewardClaimError, setRewardClaimError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      if (isMockMode()) {
        // Use mock data
        const tasks = await mockApi.getTasks();
        const progress = await mockApi.getProgress();
        const rewards = await mockApi.getRewards();
        
        setTasks(tasks);
        setWeekStars([]); // Mock empty stars data as array
        setProgress(progress);
        setRewards(rewards);
        
        console.log('📊 Demo Mode: Data loaded from mock API');
      } else {
        // Use real API
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
      }
    } catch (error) {
      console.error('Fehler beim Laden der Daten:', error);
      // Fallback to mock mode if real API fails
      if (!isMockMode()) {
        console.log('🔄 Falling back to demo mode due to API error');
        const tasks = await mockApi.getTasks();
        const progress = await mockApi.getProgress();
        const rewards = await mockApi.getRewards();
        
        setTasks(tasks);
        setWeekStars([]);
        setProgress(progress);
        setRewards(rewards);
      }
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
      if (isMockMode()) {
        // Use mock API
        await mockApi.createTask({ name: taskName });
        setNewTaskName('');
        await loadData();
        alert(`✅ Aufgabe "${taskName}" erfolgreich hinzugefügt! (Demo Mode)`);
        console.log('Aufgabe erfolgreich hinzugefügt (Mock):', taskName);
      } else {
        // Use real API
        const response = await axios.post(`${API}/tasks`, { name: taskName });
        if (response.status === 200) {
          setNewTaskName('');
          await loadData();
          console.log('Aufgabe erfolgreich hinzugefügt:', taskName);
        }
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
      await axios.post(`${API}/progress/add-to-safe`, { stars: amount });
      await axios.post(`${API}/progress/withdraw-from-safe?stars=${amount}`);
      loadData();
      alert(`✅ ${amount} Sterne erfolgreich zu verfügbaren Sternen verschoben!`);
    } catch (error) {
      console.error('Fehler beim Verschieben der Sterne:', error);
      let errorMessage = 'Fehler beim Verschieben der Sterne! Bitte versuche es erneut.';
      
      if (error.response?.data?.detail) {
        // Ensure error message is a string, not an object
        errorMessage = typeof error.response.data.detail === 'string' 
          ? error.response.data.detail 
          : JSON.stringify(error.response.data.detail);
      } else if (error.response?.data?.message) {
        errorMessage = typeof error.response.data.message === 'string'
          ? error.response.data.message
          : JSON.stringify(error.response.data.message);
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(`❌ Fehler: ${errorMessage}`);
      loadData(); // Reload in case of inconsistent state
    }
  };

  const addStarsToSafe = () => {
    setShowStarTransfer(true);
  };

  // New function to handle star transfer from the modal
  const handleStarTransfer = async (taskStarsAmount, rewardStarsAmount) => {
    try {
      // Transfer task stars if any
      if (taskStarsAmount > 0) {
        await axios.post(`${API}/progress/add-to-safe?stars=${taskStarsAmount}`);
      }

      // Transfer reward stars if any
      if (rewardStarsAmount > 0) {
        await axios.post(`${API}/progress/move-reward-to-safe?stars=${rewardStarsAmount}`);
      }

      // Reload data to reflect changes
      loadData();
    } catch (error) {
      console.error('Fehler beim Verschieben der Sterne in den Tresor:', error);
      let errorMessage = 'Fehler beim Verschieben der Sterne in den Tresor. Bitte versuche es erneut.';
      
      if (error.response?.data?.detail) {
        // Ensure error message is a string, not an object
        errorMessage = typeof error.response.data.detail === 'string' 
          ? error.response.data.detail 
          : JSON.stringify(error.response.data.detail);
      } else if (error.response?.data?.message) {
        errorMessage = typeof error.response.data.message === 'string'
          ? error.response.data.message
          : JSON.stringify(error.response.data.message);
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(`❌ Fehler: ${errorMessage}`);
      throw error; // Re-throw so modal can handle the error state
    }
  };


  const withdrawFromSafe = async (amount) => {
    try {
      await axios.post(`${API}/progress/withdraw-from-safe`, { stars: amount });
      loadData();
      setShowSafe(false);
      alert(`✅ ${amount} Sterne erfolgreich aus dem Tresor genommen!`);
    } catch (error) {
      console.error('Fehler beim Abheben aus dem Tresor:', error);
      let errorMessage = 'Fehler beim Tresor-Vorgang. Bitte versuche es erneut.';
      
      if (error.response?.data?.detail) {
        // Ensure error message is a string, not an object
        errorMessage = typeof error.response.data.detail === 'string' 
          ? error.response.data.detail 
          : JSON.stringify(error.response.data.detail);
      } else if (error.response?.data?.message) {
        errorMessage = typeof error.response.data.message === 'string'
          ? error.response.data.message
          : JSON.stringify(error.response.data.message);
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      alert(`❌ Fehler: ${errorMessage}`);
    }
  };

  const resetWeek = async () => {
    try {
      await axios.post(`${API}/progress/reset`);
      loadData();
      alert('Woche wurde zurückgesetzt. Tresor-Sterne wurden beibehalten!');
    } catch (error) {
      console.error('Fehler beim Zurücksetzen der Woche:', error);
      alert('Fehler beim Zurücksetzen der Woche!');
    }
  };

  const resetSafe = async () => {
    try {
      await axios.post(`${API}/progress/reset-safe`);
      loadData();
      alert('Tresor wurde zurückgesetzt. Alle anderen Sterne wurden beibehalten!');
    } catch (error) {
      console.error('Fehler beim Zurücksetzen des Tresors:', error);
      alert('Fehler beim Zurücksetzen des Tresors!');
    }
  };

  const resetAllStars = async () => {
    try {
      await axios.post(`${API}/progress/reset-all-stars`);
      loadData();
      alert('Alle Sterne wurden erfolgreich zurückgesetzt!');
    } catch (error) {
      console.error('Fehler beim Zurücksetzen aller Sterne:', error);
      alert('Fehler beim Zurücksetzen der Sterne!');
    }
  };

  const deleteAllRewards = async () => {
    try {
      await axios.delete(`${API}/rewards/all`);
      loadData();
      alert('Alle Belohnungen wurden erfolgreich gelöscht!');
    } catch (error) {
      console.error('Fehler beim Löschen aller Belohnungen:', error);
      alert('Fehler beim Löschen der Belohnungen!');
    }
  };

  // Export/Import Functions
  const exportData = async () => {
    try {
      const response = await axios.get(`${API}/backup/export`);
      const data = response.data;
      
      // Create filename with current date
      const now = new Date();
      const dateStr = now.toISOString().split('T')[0]; // YYYY-MM-DD
      const filename = `weekly-star-tracker-backup-${dateStr}.json`;
      
      // Create and download file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      alert(`✅ Backup erfolgreich erstellt!\n\nDatei: ${filename}\n\nDie Datei wurde in Ihre Downloads gespeichert.`);
    } catch (error) {
      console.error('Fehler beim Exportieren:', error);
      alert('❌ Fehler beim Erstellen des Backups!');
    }
  };

  const importData = async (file) => {
    try {
      const text = await file.text();
      const backupData = JSON.parse(text);
      
      // Validate backup
      if (!backupData.data || !backupData.app_version) {
        throw new Error('Ungültiges Backup-Format');
      }
      
      const response = await axios.post(`${API}/backup/import`, backupData);
      const results = response.data.results;
      
      // Show import results
      let message = '✅ Import erfolgreich!\n\n';
      message += `📝 Aufgaben: ${results.tasks}\n`;
      message += `📈 Fortschritt: ${results.progress}\n`;  
      message += `🎁 Belohnungen: ${results.rewards}\n`;
      message += `⚙️ Einstellungen: ${results.settings}\n`;
      message += `📊 Statistiken: ${results.statistics}\n`;
      
      if (results.errors.length > 0) {
        message += `\n⚠️ Fehler: ${results.errors.length}\n`;
        results.errors.forEach(error => message += `• ${error}\n`);
      }
      
      alert(message);
      loadData(); // Reload app data
    } catch (error) {
      console.error('Fehler beim Importieren:', error);
      let errorMsg = '❌ Import fehlgeschlagen!\n\n';
      if (error.message.includes('JSON')) {
        errorMsg += 'Die Datei ist keine gültige Backup-Datei.';
      } else if (error.response) {
        errorMsg += `Server-Fehler: ${error.response.data.detail || error.response.statusText}`;
      } else {
        errorMsg += `Fehler: ${error.message}`;
      }
      alert(errorMsg);
    }
  };

  const handleFileImport = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.type === 'application/json' || file.name.endsWith('.json')) {
        const confirmMsg = '⚠️ ACHTUNG: Import überschreibt alle aktuellen Daten!\n\n' +
                          'Möchten Sie zuerst ein Backup Ihrer aktuellen Daten erstellen?\n\n' +
                          'Klicken Sie "Abbrechen" um zuerst zu exportieren, oder "OK" um fortzufahren.';
        
        if (confirm(confirmMsg)) {
          importData(file);
        }
      } else {
        alert('❌ Bitte wählen Sie eine JSON-Datei aus!');
      }
    }
    // Reset file input
    event.target.value = '';
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

        {/* Challenge Buttons - Three Side by Side */}
        <div className="flex justify-center space-x-4 mb-6">
          <button 
            onClick={() => setShowMathChallenge(true)}
            className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-8 py-6 rounded-2xl text-lg font-bold hover:from-green-600 hover:to-emerald-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            🧮 Mathe-Herausforderung
          </button>
          
          <button 
            onClick={() => setShowGermanChallenge(true)}
            className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white px-8 py-6 rounded-2xl text-lg font-bold hover:from-blue-600 hover:to-indigo-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            📖 Deutsch-Herausforderung
          </button>
          
          <button 
            onClick={() => setShowEnglishChallenge(true)}
            className="bg-gradient-to-r from-purple-500 to-violet-600 text-white px-8 py-6 rounded-2xl text-lg font-bold hover:from-purple-600 hover:to-violet-700 transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            🇬🇧 Englisch-Herausforderung
          </button>
        </div>

        {/* Progress Section */}
        <ProgressBar 
          current={progress.total_stars} 
          total={progress.total_stars + progress.stars_in_safe}
          starsInSafe={progress.stars_in_safe}
          onOpenSafe={() => setShowSafe(true)}
          onAddToSafe={addStarsToSafe}
          onOpenAdminSettings={() => setShowAdminSettings(true)}
        />

        {/* Task Management */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-purple-100 task-management">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-purple-800">Meine Aufgaben</h2>
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
        <div className="bg-white rounded-xl p-6 shadow-sm border border-purple-100 rewards-section">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-purple-800">🎁 Belohnungen</h2>
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

        {showGermanChallenge && (
          <GermanChallenge 
            onClose={() => setShowGermanChallenge(false)}
            onComplete={loadData}
          />
        )}

        {showEnglishChallenge && (
          <EnglishChallenge 
            onClose={() => setShowEnglishChallenge(false)}
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

        {showStarTransfer && (
          <StarTransferModal
            isOpen={showStarTransfer}
            onClose={() => setShowStarTransfer(false)}
            progress={progress}
            onTransfer={handleStarTransfer}
          />
        )}
        
        {showMathSettings && (
          <MathSettingsModal
            isOpen={showMathSettings}
            onClose={() => setShowMathSettings(false)}
            onComplete={loadData}
          />
        )}

        {showGermanSettings && (
          <GermanSettingsModal
            isOpen={showGermanSettings}
            onClose={() => setShowGermanSettings(false)}
            onComplete={loadData}
          />
        )}

        {showEnglishSettings && (
          <EnglishSettingsModal
            isOpen={showEnglishSettings}
            onClose={() => setShowEnglishSettings(false)}
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

        {showAdminSettings && (
          <AdminSettingsModal
            isOpen={showAdminSettings}
            onClose={() => setShowAdminSettings(false)}
            onResetWeek={resetWeek}
            onResetSafe={resetSafe}
            onResetAllStars={resetAllStars}
            onDeleteAllRewards={deleteAllRewards}
            onManageTasks={() => {
              setShowAdminSettings(false);
              // Optional: Scroll zu Task-Management Sektion
              document.querySelector('.task-management')?.scrollIntoView({ behavior: 'smooth' });
            }}
            onManageRewards={() => {
              setShowAdminSettings(false);
              // Optional: Scroll zu Rewards Sektion
              document.querySelector('.rewards-section')?.scrollIntoView({ behavior: 'smooth' });
            }}
            onOpenMathSettings={() => setShowMathSettings(true)}
            onOpenGermanSettings={() => setShowGermanSettings(true)}
            onOpenEnglishSettings={() => setShowEnglishSettings(true)}
            onExportData={exportData}
            onImportData={handleFileImport}
          />
        )}
      </div>
    </div>
  );
}

export default App;