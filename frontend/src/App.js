import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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
          <h2 className="text-2xl font-bold text-purple-800 mb-4">Star Safe</h2>
          <div className="text-4xl font-bold text-yellow-600 mb-6">
            {starsInSafe} ⭐
          </div>
          
          {starsInSafe > 0 && (
            <div className="mb-6">
              <p className="text-purple-600 mb-3">How many stars would you like to take out?</p>
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
                  Take Out
                </button>
              </div>
            </div>
          )}
          
          <button 
            onClick={onClose}
            className="bg-purple-500 text-white px-8 py-3 rounded-lg hover:bg-purple-600 transition-colors"
          >
            Close Safe
          </button>
        </div>
      </div>
    </div>
  );
};

// Math Settings Modal Component
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
      console.error('Error loading math data:', error);
    }
  };

  const updateSettings = async () => {
    setLoading(true);
    try {
      await axios.put(`${API}/math/settings`, settings);
      onComplete();
      alert('Settings saved successfully!');
    } catch (error) {
      console.error('Error updating settings:', error);
    }
    setLoading(false);
  };

  const resetStatistics = async () => {
    if (confirm('Are you sure you want to reset all math statistics?')) {
      try {
        await axios.post(`${API}/math/statistics/reset`);
        loadData();
        alert('Statistics reset successfully!');
      } catch (error) {
        console.error('Error resetting statistics:', error);
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
    const percentage = prompt('Enter percentage threshold (e.g., 85):');
    const stars = prompt('Enter stars to award:');
    if (percentage && stars) {
      updateStarTier(percentage, parseInt(stars));
    }
  };

  if (!isOpen || !settings || !statistics) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 overflow-y-auto">
      <div className="bg-white rounded-xl p-8 max-w-4xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-purple-800">Math Challenge Settings</h2>
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
            ⚙️ Settings
          </button>
          <button
            onClick={() => setActiveTab('statistics')}
            className={`py-2 px-4 font-medium transition-colors ${
              activeTab === 'statistics'
                ? 'text-purple-600 border-b-2 border-purple-600'
                : 'text-gray-600 hover:text-purple-600'
            }`}
          >
            📊 Statistics
          </button>
        </div>

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="space-y-6">
            {/* Basic Settings */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-purple-800 mb-2">
                  Maximum Number (Addition/Subtraction)
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
                  Maximum Multiplication Table
                </label>
                <input
                  type="number"
                  value={settings.max_multiplication}
                  onChange={(e) => setSettings({...settings, max_multiplication: parseInt(e.target.value)})}
                  className="w-full p-3 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
                />
              </div>
            </div>

            {/* Star Rewards */}
            <div>
              <h3 className="text-lg font-semibold text-purple-800 mb-3">⭐ Star Reward Tiers</h3>
              <p className="text-sm text-gray-600 mb-4">Set how many stars to award based on percentage score</p>
              
              <div className="space-y-3">
                {Object.entries(settings.star_tiers).map(([percentage, stars]) => (
                  <div key={percentage} className="flex items-center space-x-3 bg-purple-50 p-3 rounded-lg">
                    <span className="font-medium">{percentage}% or higher:</span>
                    <input
                      type="number"
                      value={stars}
                      onChange={(e) => updateStarTier(percentage, parseInt(e.target.value))}
                      className="w-20 p-2 border border-purple-300 rounded focus:outline-none focus:border-purple-500"
                    />
                    <span>⭐ stars</span>
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
                + Add Tier
              </button>
            </div>

            <div className="flex justify-end space-x-4">
              <button 
                onClick={onClose}
                className="px-6 py-2 border border-purple-300 text-purple-600 rounded-lg hover:bg-purple-50 transition-colors"
              >
                Cancel
              </button>
              <button 
                onClick={updateSettings}
                disabled={loading}
                className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50"
              >
                {loading ? 'Saving...' : 'Save Settings'}
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
                <h3 className="font-semibold mb-2">Total Attempts</h3>
                <p className="text-3xl font-bold">{statistics.total_attempts}</p>
              </div>
              <div className="stats-card stats-card-completed">
                <h3 className="font-semibold mb-2">Average Score</h3>
                <p className="text-3xl font-bold">{statistics.average_score.toFixed(1)}%</p>
              </div>
              <div className="stats-card stats-card-pending">
                <h3 className="font-semibold mb-2">Best Score</h3>
                <p className="text-3xl font-bold">{statistics.best_score.toFixed(1)}%</p>
              </div>
              <div className="stats-card">
                <h3 className="font-semibold mb-2">Stars Earned</h3>
                <p className="text-3xl font-bold">{statistics.total_stars_earned} ⭐</p>
              </div>
            </div>

            {/* Detailed Stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="card">
                <h3 className="text-lg font-semibold text-purple-800 mb-4">📚 Grade Breakdown</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span>Grade 2 Attempts:</span>
                    <span className="font-semibold">{statistics.grade_2_attempts}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Grade 3 Attempts:</span>
                    <span className="font-semibold">{statistics.grade_3_attempts}</span>
                  </div>
                </div>
              </div>

              <div className="card">
                <h3 className="text-lg font-semibold text-purple-800 mb-4">🎯 Answer Breakdown</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-green-600">✅ Correct Answers:</span>
                    <span className="font-semibold text-green-600">{statistics.total_correct}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-red-600">❌ Wrong Answers:</span>
                    <span className="font-semibold text-red-600">{statistics.total_wrong}</span>
                  </div>
                  <div className="pt-2 border-t">
                    <div className="flex justify-between items-center">
                      <span>Accuracy Rate:</span>
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
                Reset Statistics
              </button>
              <button 
                onClick={onClose}
                className="bg-purple-500 text-white px-6 py-2 rounded-lg hover:bg-purple-600 transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
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
      console.error('Error creating math challenge:', error);
      alert('Error creating math challenge. Please try again.');
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
      console.error('Error submitting answers:', error);
      alert('Error submitting answers. Please try again.');
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
            <h2 className="text-2xl font-bold text-purple-800 mb-4">Great Job!</h2>
            <div className="space-y-2 mb-6">
              <p>Correct Answers: {result.correct_answers}/{result.total_problems}</p>
              <p>Score: {result.percentage.toFixed(1)}%</p>
              <p className="text-lg font-semibold text-yellow-600">
                Stars Earned: {result.stars_earned} ⭐
              </p>
            </div>
          </div>

          <div className="mb-6">
            <h3 className="text-lg font-semibold text-purple-800 mb-4">Review Your Answers:</h3>
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
                    <span className="font-medium">Problem {index + 1}</span>
                  </div>
                  <p className="mb-2 font-medium">{problem.question}</p>
                  <div className="space-y-1 text-sm">
                    <p><span className="font-medium">Your answer:</span> {problem.user_answer}</p>
                    {!problem.is_correct && (
                      <p className="text-green-600">
                        <span className="font-medium">Correct answer:</span> {problem.correct_answer}
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
              Awesome! Continue
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
            <h2 className="text-2xl font-bold text-purple-800 mb-4">Great Job!</h2>
            <div className="space-y-2 mb-6">
              <p>Correct Answers: {result.correct_answers}/{result.total_problems}</p>
              <p>Score: {result.percentage.toFixed(1)}%</p>
              <p className="text-lg font-semibold text-yellow-600">
                Stars Earned: {result.stars_earned} ⭐
              </p>
            </div>
            <div className="flex space-x-4">
              <button 
                onClick={() => setShowResults(true)}
                className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
              >
                Review Answers
              </button>
              <button 
                onClick={() => {
                  onComplete();
                  onClose();
                }}
                className="bg-purple-500 text-white px-6 py-2 rounded-lg hover:bg-purple-600 transition-colors"
              >
                Continue
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
        <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4 my-8 max-h-[90vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold text-purple-800">Math Grade {grade} Challenge</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
          </div>
          
          <div className="mb-4 text-sm text-gray-600">
            Fill in ALL answers to enable submission. Answers completed: {Object.keys(answers).length}/{challenge.problems.length}
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {challenge.problems.map((problem, index) => (
              <div key={index} className={`p-4 border-2 rounded-lg transition-colors ${
                answers[index] !== undefined && answers[index] !== '' 
                  ? 'border-green-300 bg-green-50' 
                  : 'border-purple-200 bg-white'
              }`}>
                <p className="mb-2 font-medium">{index + 1}. {problem.question}</p>
                <input
                  type="number"
                  min="0"
                  max="100"
                  className="w-full p-2 border border-purple-300 rounded focus:outline-none focus:border-purple-500"
                  placeholder="Your answer (0-100)"
                  value={answers[index] || ''}
                  onChange={(e) => {
                    const value = e.target.value;
                    // Allow empty string for clearing
                    if (value === '') {
                      setAnswers({...answers, [index]: ''});
                      return;
                    }
                    
                    // Parse the number
                    const numValue = parseInt(value);
                    
                    // Only allow valid numbers between 0 and 100
                    if (!isNaN(numValue) && numValue >= 0 && numValue <= 100) {
                      setAnswers({...answers, [index]: numValue});
                    }
                    // If invalid, don't update the state (keeps previous valid value)
                  }}
                  onKeyDown={(e) => {
                    // Prevent negative sign and other invalid characters
                    if (e.key === '-' || e.key === 'e' || e.key === 'E' || e.key === '+') {
                      e.preventDefault();
                    }
                  }}
                  onPaste={(e) => {
                    // Prevent pasting invalid values
                    e.preventDefault();
                    const pastedText = e.clipboardData.getData('text');
                    const numValue = parseInt(pastedText);
                    if (!isNaN(numValue) && numValue >= 0 && numValue <= 100) {
                      setAnswers({...answers, [index]: numValue});
                    }
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
              Cancel
            </button>
            <button 
              onClick={submitAnswers}
              disabled={loading || !allAnswersProvided}
              className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Submitting...' : `Submit All Answers (${Object.keys(answers).length}/${challenge.problems.length})`}
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
          <h2 className="text-2xl font-bold text-purple-800 mb-6">Earn Extra Stars!</h2>
          <p className="text-gray-600 mb-6">Choose your math grade level:</p>
          <div className="space-y-4">
            <button 
              onClick={() => startChallenge(2)}
              disabled={loading}
              className="w-full p-4 bg-gradient-to-r from-purple-400 to-pink-400 text-white rounded-xl hover:from-purple-500 hover:to-pink-500 transition-all disabled:opacity-50"
            >
              📚 Math Grade 2
            </button>
            <button 
              onClick={() => startChallenge(3)}
              disabled={loading}
              className="w-full p-4 bg-gradient-to-r from-indigo-400 to-purple-400 text-white rounded-xl hover:from-indigo-500 hover:to-purple-500 transition-all disabled:opacity-50"
            >
              🎓 Math Grade 3
            </button>
          </div>
          <button 
            onClick={onClose}
            className="mt-4 text-purple-600 hover:text-purple-800 transition-colors"
          >
            Maybe Later
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
  const [progress, setProgress] = useState({ total_stars: 0, stars_in_safe: 0 });
  const [rewards, setRewards] = useState([]);
  const [newTaskName, setNewTaskName] = useState('');
  const [newRewardName, setNewRewardName] = useState('');
  const [newRewardStars, setNewRewardStars] = useState('');
  const [showMathChallenge, setShowMathChallenge] = useState(false);
  const [showSafe, setShowSafe] = useState(false);
  const [showMathSettings, setShowMathSettings] = useState(false);
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
      console.error('Error loading data:', error);
    }
    setLoading(false);
  };

  const addTask = async () => {
    if (!newTaskName.trim()) return;
    
    try {
      await axios.post(`${API}/tasks`, { name: newTaskName });
      setNewTaskName('');
      loadData();
    } catch (error) {
      console.error('Error adding task:', error);
    }
  };

  const deleteTask = async (taskId) => {
    try {
      await axios.delete(`${API}/tasks/${taskId}`);
      loadData();
    } catch (error) {
      console.error('Error deleting task:', error);
    }
  };

  const handleStarClick = async (taskId, day, stars) => {
    try {
      await axios.post(`${API}/stars/${taskId}/${day}?stars=${stars}`);
      loadData();
    } catch (error) {
      console.error('Error updating stars:', error);
    }
  };

  const addReward = async () => {
    if (!newRewardName.trim() || !newRewardStars) return;
    
    try {
      await axios.post(`${API}/rewards`, { 
        name: newRewardName, 
        required_stars: parseInt(newRewardStars) 
      });
      setNewRewardName('');
      setNewRewardStars('');
      loadData();
    } catch (error) {
      console.error('Error adding reward:', error);
    }
  };

  const claimReward = async (rewardId) => {
    try {
      await axios.post(`${API}/rewards/${rewardId}/claim`);
      loadData();
    } catch (error) {
      console.error('Error claiming reward:', error);
      alert('Not enough stars in safe!');
    }
  };

  const addStarsToSafe = async () => {
    if (progress.total_stars === 0) {
      alert('No stars available to add to safe!');
      return;
    }
    
    const starsToAdd = prompt(`How many stars to add to safe? (Available: ${progress.total_stars})`);
    if (!starsToAdd) return;
    
    try {
      await axios.post(`${API}/progress/add-to-safe?stars=${parseInt(starsToAdd)}`);
      loadData();
    } catch (error) {
      console.error('Error adding stars to safe:', error);
      alert('Not enough stars available!');
    }
  };

  const withdrawFromSafe = async (amount) => {
    try {
      await axios.post(`${API}/progress/withdraw-from-safe?stars=${amount}`);
      loadData();
      setShowSafe(false);
    } catch (error) {
      console.error('Error withdrawing from safe:', error);
      alert('Error withdrawing stars!');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 flex items-center justify-center">
        <div className="text-2xl text-purple-600">Loading your Star Tracker...</div>
      </div>
    );
  }

  const days = ['Task', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 p-4">
      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header */}
        <div className="text-center py-8">
          <h1 className="text-4xl font-bold text-purple-800 mb-2">⭐ Weekly Star Tracker ⭐</h1>
          <p className="text-purple-600">Complete your tasks and earn stars for amazing rewards!</p>
        </div>

        {/* Progress Section */}
        <ProgressBar 
          current={progress.total_stars} 
          total={progress.total_stars + progress.stars_in_safe}
          starsInSafe={progress.stars_in_safe}
          onOpenSafe={() => setShowSafe(true)}
          onAddToSafe={addStarsToSafe}
        />

        {/* Task Management */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-purple-100">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-purple-800">My Tasks</h2>
            <div className="flex space-x-2">
              <button 
                onClick={() => setShowMathSettings(true)}
                className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition-colors"
              >
                ⚙️ Math Settings
              </button>
              <button 
                onClick={() => setShowMathChallenge(true)}
                className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-colors"
              >
                🧮 Math Challenge
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
              placeholder="Add new task..."
              value={newTaskName}
              onChange={(e) => setNewTaskName(e.target.value)}
              className="flex-1 p-3 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
              onKeyPress={(e) => e.key === 'Enter' && addTask()}
            />
            <button 
              onClick={addTask}
              className="bg-purple-500 text-white px-6 py-3 rounded-lg hover:bg-purple-600 transition-colors"
            >
              Add Task
            </button>
          </div>
        </div>

        {/* Rewards Section */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-purple-100">
          <h2 className="text-xl font-semibold text-purple-800 mb-4">🎁 Rewards</h2>
          
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
                      Claim!
                    </button>
                  )}
                  {reward.is_claimed && (
                    <div className="text-green-600 font-semibold">✓ Claimed</div>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          <div className="flex space-x-2">
            <input
              type="text"
              placeholder="Reward name..."
              value={newRewardName}
              onChange={(e) => setNewRewardName(e.target.value)}
              className="flex-1 p-3 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
            />
            <input
              type="number"
              placeholder="Stars required"
              value={newRewardStars}
              onChange={(e) => setNewRewardStars(e.target.value)}
              className="w-32 p-3 border border-purple-300 rounded-lg focus:outline-none focus:border-purple-500"
            />
            <button 
              onClick={addReward}
              className="bg-yellow-500 text-white px-6 py-3 rounded-lg hover:bg-yellow-600 transition-colors"
            >
              Add Reward
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
      </div>
    </div>
  );
}

export default App;