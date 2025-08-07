// Mock Backend für Testing
const MOCK_MODE = true; // Set to true for testing without backend

let mockTasks = [
  { id: '1', name: 'Test Task', created_at: '2025-08-07T09:00:00Z' }
];

let mockStars = {}; // Store star data by task/day

let mockProgress = {
  total_stars: 0,
  total_stars_earned: 0,
  total_stars_used: 0,
  available_stars: 0,
  stars_in_safe: 3,
};

let mockRewards = [];

// Helper function to calculate total stars
const calculateTotalStars = () => {
  let total = 0;
  Object.values(mockStars).forEach(taskStars => {
    Object.values(taskStars).forEach(stars => {
      total += stars;
    });
  });
  return total;
};

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
    // Remove stars for deleted task
    delete mockStars[taskId];
    return Promise.resolve({ message: 'Task deleted' });
  },

  // Stars
  getStars: () => {
    // Convert object format to array format expected by frontend
    const starArray = [];
    Object.entries(mockStars).forEach(([taskId, taskStars]) => {
      Object.entries(taskStars).forEach(([day, stars]) => {
        starArray.push({
          task_id: taskId,
          day: day,
          stars: stars
        });
      });
    });
    return Promise.resolve(starArray);
  },
  updateStars: (taskId, day, stars) => {
    if (!mockStars[taskId]) {
      mockStars[taskId] = {};
    }
    mockStars[taskId][day] = Math.max(0, stars);
    
    // Update progress based on star changes
    const totalStars = calculateTotalStars();
    mockProgress.total_stars = Math.max(0, totalStars - mockProgress.total_stars_used);
    mockProgress.total_stars_earned = totalStars;
    
    console.log(`⭐ Mock: Updated ${taskId}/${day} = ${stars} stars. Total: ${totalStars}`);
    return Promise.resolve({ message: 'Stars updated', total_stars: totalStars });
  },

  // Progress
  getProgress: () => Promise.resolve(mockProgress),
  addStarsToSafe: (stars) => {
    const available = Math.max(0, mockProgress.total_stars);
    const toSafe = Math.min(stars, available);
    mockProgress.stars_in_safe += toSafe;
    mockProgress.total_stars_used += toSafe;
    mockProgress.total_stars = Math.max(0, mockProgress.total_stars - toSafe);
    return Promise.resolve(mockProgress);
  },
  withdrawFromSafe: (stars) => {
    const available = Math.min(stars, mockProgress.stars_in_safe);
    mockProgress.stars_in_safe -= available;
    mockProgress.available_stars += available;
    return Promise.resolve(mockProgress);
  },
  moveRewardToSafe: (stars) => {
    const available = Math.min(stars, mockProgress.available_stars);
    mockProgress.available_stars -= available;
    mockProgress.stars_in_safe += available;
    return Promise.resolve(mockProgress);
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
  },
  claimReward: (rewardId) => {
    const reward = mockRewards.find(r => r.id === rewardId);
    if (reward && !reward.claimed) {
      const cost = reward.stars_required;
      const available = mockProgress.available_stars;
      
      if (available >= cost) {
        reward.claimed = true;
        mockProgress.available_stars -= cost;
        return Promise.resolve({ message: 'Reward claimed' });
      } else {
        throw new Error('Not enough stars');
      }
    }
    throw new Error('Reward not found or already claimed');
  }
};

export const isMockMode = () => MOCK_MODE;