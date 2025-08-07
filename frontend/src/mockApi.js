// Mock Backend für Testing
const MOCK_MODE = true; // Set to true for testing without backend

let mockTasks = [
  { id: '1', name: 'Test Task', created_at: '2025-08-07T09:00:00Z' }
];

let mockProgress = {
  total_stars: 0,
  total_stars_earned: 5,
  total_stars_used: 0,
  available_stars: 0,
  stars_in_safe: 3,
};

let mockRewards = [];

export const mockApi = {
  // Tasks
  getTasks: () => Promise.resolve(mockTasks),
  createTask: (taskData) => {
    const newTask = {
      id: Date.now().toString(),
      name: taskData.name,
      created_at: new Date().toISOString()
    };
    mockTasks.push(newTask);
    return Promise.resolve(newTask);
  },
  deleteTask: (taskId) => {
    mockTasks = mockTasks.filter(t => t.id !== taskId);
    return Promise.resolve({ message: 'Task deleted' });
  },

  // Progress
  getProgress: () => Promise.resolve(mockProgress),
  addStarsToSafe: (stars) => {
    mockProgress.stars_in_safe += stars;
    mockProgress.total_stars -= stars;
    return Promise.resolve(mockProgress);
  },
  withdrawFromSafe: (stars) => {
    mockProgress.stars_in_safe -= stars;
    mockProgress.available_stars += stars;
    return Promise.resolve(mockProgress);
  },

  // Stars
  updateStars: (taskId, day, stars) => {
    mockProgress.total_stars = Math.max(0, mockProgress.total_stars + stars);
    return Promise.resolve({ message: 'Stars updated' });
  },

  // Rewards
  getRewards: () => Promise.resolve(mockRewards),
  createReward: (rewardData) => {
    const newReward = {
      id: Date.now().toString(),
      name: rewardData.name,
      stars_required: rewardData.stars_required,
      claimed: false,
      created_at: new Date().toISOString()
    };
    mockRewards.push(newReward);
    return Promise.resolve(newReward);
  }
};

export const isMockMode = () => MOCK_MODE;