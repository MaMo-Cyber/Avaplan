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
    ⭐
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
const ProgressBar = ({ current, total, starsInSafe }) => {
  const percentage = total > 0 ? (current / total) * 100 : 0;
  
  return (
    <div className="bg-white rounded-xl p-6 shadow-sm border border-purple-100">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-purple-800">Weekly Progress</h3>
        <div className="text-sm text-purple-600">
          {current} / {total} stars
        </div>
      </div>
      <div className="w-full bg-purple-100 rounded-full h-4 mb-4">
        <div 
          className="bg-gradient-to-r from-purple-500 to-indigo-600 h-4 rounded-full transition-all duration-500"
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <div className="flex justify-between items-center">
        <div className="text-purple-600">
          💰 Stars in Safe: <span className="font-semibold">{starsInSafe}</span>
        </div>
        <button 
          className="bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition-colors"
          onClick={() => window.location.reload()} // Simple reset for now
        >
          Reset Week
        </button>
      </div>
    </div>
  );
};

// Math Challenge Component
const MathChallenge = ({ onClose, onComplete }) => {
  const [grade, setGrade] = useState(null);
  const [challenge, setChallenge] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const startChallenge = async (selectedGrade) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/math/challenge/${selectedGrade}`);
      setChallenge(response.data);
      setGrade(selectedGrade);
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
    } catch (error) {
      console.error('Error submitting answers:', error);
      alert('Error submitting answers. Please try again.');
    }
    setLoading(false);
  };

  if (result) {
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
                onClick={() => {
                  onComplete();
                  onClose();
                }}
                className="bg-purple-500 text-white px-6 py-2 rounded-lg hover:bg-purple-600 transition-colors"
              >
                Awesome!
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
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {challenge.problems.map((problem, index) => (
              <div key={index} className="p-4 border border-purple-200 rounded-lg">
                <p className="mb-2 font-medium">{index + 1}. {problem.question}</p>
                <input
                  type="number"
                  className="w-full p-2 border border-purple-300 rounded focus:outline-none focus:border-purple-500"
                  placeholder="Your answer"
                  value={answers[index] || ''}
                  onChange={(e) => setAnswers({...answers, [index]: parseInt(e.target.value) || 0})}
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
              disabled={loading || Object.keys(answers).length === 0}
              className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Submit Answers'}
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
    const starsToAdd = prompt('How many stars to add to safe?');
    if (!starsToAdd) return;
    
    try {
      await axios.post(`${API}/progress/add-to-safe?stars=${parseInt(starsToAdd)}`);
      loadData();
    } catch (error) {
      console.error('Error adding stars to safe:', error);
      alert('Not enough stars available!');
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
        />

        {/* Task Management */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-purple-100">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-purple-800">My Tasks</h2>
            <div className="flex space-x-2">
              <button 
                onClick={addStarsToSafe}
                className="bg-yellow-500 text-white px-4 py-2 rounded-lg hover:bg-yellow-600 transition-colors"
              >
                💰 Add to Safe
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
        
        {/* Math Challenge Modal */}
        {showMathChallenge && (
          <MathChallenge 
            onClose={() => setShowMathChallenge(false)}
            onComplete={loadData}
          />
        )}
      </div>
    </div>
  );
}

export default App;