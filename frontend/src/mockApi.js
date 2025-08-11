// Helper function to generate clock problems based on settings
const generateClockProblem = (clockSettings) => {
  const availableMinutes = [];
  
  // Add minute options based on settings
  if (clockSettings.include_half_hours) {
    availableMinutes.push(30);
  }
  if (clockSettings.include_quarter_hours) {
    availableMinutes.push(15, 45);
  }
  if (clockSettings.include_five_minute_intervals) {
    availableMinutes.push(5, 10, 20, 25, 35, 40, 50, 55);
  }
  
  // If no specific settings, default to all common times
  if (availableMinutes.length === 0) {
    availableMinutes.push(0, 15, 30, 45);
  }
  
  // Generate random time
  const hour = Math.floor(Math.random() * 12) + 1; // 1-12
  const minute = availableMinutes[Math.floor(Math.random() * availableMinutes.length)];
  
  // Format time
  const timeString = `${hour}:${minute.toString().padStart(2, '0')}`;
  
  // Generate question variations
  const questionTypes = [
    `Wie spät ist es? ${timeString}`,
    `Welche Zeit zeigt die Uhr? ${timeString}`,
    `Die Uhr zeigt ${timeString}. Wie spät ist es?`
  ];
  
  const question = questionTypes[Math.floor(Math.random() * questionTypes.length)];
  
  return {
    question: question,
    correct_answer: timeString,
    question_type: 'clock_reading',
    clock_display: { hour, minute }
  };
};

// Mock Backend für Testing
const MOCK_MODE = true; // Set to true for testing without backend

let mockTasks = [];

let mockStars = {}; // Store star data by task/day

let mockProgress = {
  total_stars: 0,        // Currently available task stars (earned - used)
  total_stars_earned: 0, // Total stars earned from tasks
  total_stars_used: 0,   // Stars used for rewards 
  available_stars: 0,    // Available reward stars (from challenges)
  stars_in_safe: 3,      // Total stars in safe (original 3 + user added)
};

// Track stars moved to safe by user (separate from original 3)
let starsMovedToSafe = 0;

let mockRewards = [];

// Mock settings storage
let mockMathSettings = {
  max_number: 100,
  max_multiplication: 10,
  problem_count: 15, // Default problem count
  star_tiers: {"90": 3, "80": 2, "70": 1},
  problem_types: {
    addition: true,
    subtraction: true,
    multiplication: true,
    clock_reading: false,
    currency_math: false,
    word_problems: false
  },
  clock_settings: {
    include_half_hours: true,
    include_quarter_hours: true,
    include_five_minute_intervals: false
  },
  currency_settings: {
    currency_symbol: "€",
    max_amount: 20.00
  }
};

let mockGermanSettings = {
  problem_count: 20,
  star_tiers: {"90": 3, "80": 2, "70": 1},
  problem_types: {
    spelling_problems: true,
    word_type_problems: true,
    fill_blank_problems: true
  },
  difficulty_settings: {
    vocabulary_level: "basic",
    include_articles: false
  }
};

let mockEnglishSettings = {
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
};

// Helper function to calculate total stars from tasks
const calculateTotalStars = () => {
  let total = 0;
  Object.values(mockStars).forEach(taskStars => {
    Object.values(taskStars).forEach(stars => {
      total += stars;
    });
  });
  return total;
};

// Helper function to recalculate progress
const recalculateProgress = () => {
  const totalEarnedFromTasks = calculateTotalStars();
  mockProgress.total_stars_earned = totalEarnedFromTasks;
  
  // Available task stars = total earned - used for rewards - moved to safe
  mockProgress.total_stars = Math.max(0, totalEarnedFromTasks - mockProgress.total_stars_used - starsMovedToSafe);
  
  console.log(`📊 Mock Progress Recalculated:`);
  console.log(`   Earned from tasks: ${totalEarnedFromTasks}`);
  console.log(`   Used for rewards: ${mockProgress.total_stars_used}`);
  console.log(`   Moved to safe by user: ${starsMovedToSafe}`);
  console.log(`   Available task stars: ${mockProgress.total_stars}`);
  console.log(`   Available reward stars: ${mockProgress.available_stars}`);
  console.log(`   Total in safe: ${mockProgress.stars_in_safe}`);
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
    // Recalculate progress after task deletion
    recalculateProgress();
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
    
    // Store the new stars value
    const oldStars = mockStars[taskId][day] || 0;
    mockStars[taskId][day] = Math.max(0, stars);
    
    console.log(`⭐ Mock: Updated ${taskId}/${day} from ${oldStars} to ${stars} stars`);
    
    // Recalculate all progress values
    recalculateProgress();
    
    return Promise.resolve({ 
      message: 'Stars updated', 
      task_id: taskId,
      day: day,
      stars: stars,
      old_stars: oldStars,
      total_earned: mockProgress.total_stars_earned,
      available_task_stars: mockProgress.total_stars
    });
  },

  // Progress
  getProgress: () => Promise.resolve(mockProgress),
  addStarsToSafe: (stars) => {
    const taskStarsAvailable = mockProgress.total_stars;
    const toTransfer = Math.min(stars, taskStarsAvailable);
    
    if (toTransfer > 0) {
      // Track how many stars were moved by user to safe
      starsMovedToSafe += toTransfer;
      
      // Update total safe stars
      mockProgress.stars_in_safe += toTransfer;
      
      // Recalculate progress (this will reduce total_stars)
      recalculateProgress();
      
      console.log(`⭐ Mock: Moved ${toTransfer} task stars to safe (user moved total: ${starsMovedToSafe})`);
    } else {
      console.log(`❌ Mock: Cannot move ${stars} stars - only ${taskStarsAvailable} available`);
    }
    
    return Promise.resolve(mockProgress);
  },
  
  withdrawFromSafe: (stars) => {
    // Can withdraw from total safe stars (including original 3)
    const totalAvailableInSafe = mockProgress.stars_in_safe;
    const toWithdraw = Math.min(stars, totalAvailableInSafe);
    
    if (toWithdraw > 0) {
      // Reduce safe total
      mockProgress.stars_in_safe -= toWithdraw;
      
      // Update starsMovedToSafe tracking (but don't go below 0)
      starsMovedToSafe = Math.max(0, starsMovedToSafe - toWithdraw);
      
      // These become reward stars (available_stars)
      mockProgress.available_stars += toWithdraw;
      
      recalculateProgress();
      
      console.log(`⭐ Mock: Withdrew ${toWithdraw} stars from safe to reward stars (safe now: ${mockProgress.stars_in_safe})`);
    } else {
      console.log(`❌ Mock: Cannot withdraw ${stars} stars - safe is empty`);
    }
    
    return Promise.resolve(mockProgress);
  },
  
  moveRewardToSafe: (stars) => {
    const availableRewardStars = mockProgress.available_stars;
    const toTransfer = Math.min(stars, availableRewardStars);
    
    if (toTransfer > 0) {
      mockProgress.available_stars -= toTransfer;
      mockProgress.stars_in_safe += toTransfer;
    }
    
    recalculateProgress();
    
    console.log(`⭐ Mock: Moved ${toTransfer} reward stars to safe`);
    return Promise.resolve(mockProgress);
  },

  moveTaskStarsToAvailable: (stars) => {
    const taskStarsAvailable = mockProgress.total_stars;
    const toTransfer = Math.min(stars, taskStarsAvailable);
    
    if (toTransfer > 0) {
      // Increase total_stars_used which reduces available task stars
      mockProgress.total_stars_used += toTransfer;
      
      // Add to available reward stars
      mockProgress.available_stars += toTransfer;
      
      // Recalculate progress
      recalculateProgress();
      
      console.log(`⭐ Mock: Moved ${toTransfer} task stars to available reward stars`);
    } else {
      console.log(`❌ Mock: Cannot move ${stars} stars - only ${taskStarsAvailable} available`);
    }
    
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
  },

  // Reset functions
  resetWeek: () => {
    // Reset weekly stars but keep safe stars
    mockStars = {};
    mockProgress.total_stars_earned = 0;
    mockProgress.total_stars = 0; 
    mockProgress.total_stars_used = 0;
    mockProgress.available_stars = 0;
    // Keep mockProgress.stars_in_safe and starsMovedToSafe unchanged
    console.log('⭐ Mock: Week reset, safe preserved');
    return Promise.resolve({ message: 'Week reset' });
  },

  resetSafe: () => {
    // Reset safe stars to original 3 and return user stars to available task stars
    const userStarsInSafe = Math.max(0, mockProgress.stars_in_safe - 3);
    
    // Add user stars back to available task stars  
    mockProgress.total_stars += userStarsInSafe;
    
    // Reset safe to original 3
    mockProgress.stars_in_safe = 3;
    starsMovedToSafe = 0;
    
    // Recalculate progress
    recalculateProgress();
    
    console.log(`⭐ Mock: Safe reset to 3 stars, ${userStarsInSafe} stars returned to available`);
    return Promise.resolve({ message: 'Safe reset' });
  },

  resetAllStars: () => {
    // Reset everything
    mockStars = {};
    mockProgress = {
      total_stars: 0,
      total_stars_earned: 0,
      total_stars_used: 0,
      available_stars: 0,
      stars_in_safe: 3, // Keep original 3
    };
    starsMovedToSafe = 0;
    console.log('⭐ Mock: All stars reset');
    return Promise.resolve({ message: 'All stars reset' });
  },

  // Mock Challenge Functions
  createMathChallenge: (grade) => {
    console.log('🔍 DEBUG: mockMathSettings before challenge creation:', JSON.stringify(mockMathSettings, null, 2));
    const problemCount = mockMathSettings.problem_count;
    const problems = [];
    
    console.log(`🧮 Mock: Creating ${problemCount} math problems for grade ${grade}`);
    
    // Check if clock reading is enabled
    const isClockEnabled = mockMathSettings.problem_types?.clock_reading || false;
    const clockSettings = mockMathSettings.clock_settings || {};
    
    console.log('🕐 DEBUG: Clock reading enabled:', isClockEnabled);
    console.log('🕐 DEBUG: Clock settings:', JSON.stringify(clockSettings, null, 2));
    
    for (let i = 0; i < problemCount; i++) {
      // If clock reading is enabled, generate clock problems
      if (isClockEnabled && Math.random() < 0.6) { // 60% chance for clock problems when enabled
        const clockProblem = generateClockProblem(clockSettings);
        problems.push(clockProblem);
      } else {
        // Generate regular math problems
        const num1 = Math.floor(Math.random() * 20) + 1;
        const num2 = Math.floor(Math.random() * 20) + 1;
        const operators = ['+', '-', '×'];
        const operator = operators[Math.floor(Math.random() * operators.length)];
        
        let answer;
        switch (operator) {
          case '+': answer = num1 + num2; break;
          case '-': answer = Math.abs(num1 - num2); break;
          case '×': answer = num1 * num2; break;
        }
        
        problems.push({
          question: `${num1} ${operator} ${num2} = ?`,
          correct_answer: answer.toString(),
          question_type: 'basic_math'
        });
      }
    }
    
    const challenge = {
      id: Date.now().toString(),
      grade: grade,
      problems: problems,
      created_at: new Date().toISOString()
    };
    
    return Promise.resolve({ challenge: challenge, success: true });
  },

  createGermanChallenge: (grade) => {
    const problemCount = mockGermanSettings.problem_count;
    const problems = [];
    
    console.log(`📖 Mock: Creating ${problemCount} German problems for grade ${grade}`);
    
    for (let i = 0; i < problemCount; i++) {
      const words = grade === 2 
        ? ['Haus', 'Auto', 'Baum', 'Buch', 'Hund', 'Katze', 'Ball', 'Tisch']
        : ['Computer', 'Schmetterling', 'Regenbogen', 'Fahrrad', 'Elefant', 'Blume', 'Fenster', 'Schlüssel'];
      
      const word = words[Math.floor(Math.random() * words.length)];
      
      problems.push({
        question: `Wie schreibt man "${word}"?`,
        correct_answer: word,
        options: [word, word.toLowerCase(), word.toUpperCase(), word + 'e'],
        question_type: 'spelling'
      });
    }
    
    const challenge = {
      id: Date.now().toString(),
      grade: grade,
      problems: problems,
      created_at: new Date().toISOString()
    };
    
    return Promise.resolve({ challenge: challenge, success: true });
  },

  createEnglishChallenge: (grade) => {
    const problemCount = mockEnglishSettings.problem_count;
    const problems = [];
    
    console.log(`🇬🇧 Mock: Creating ${problemCount} English problems for grade ${grade}`);
    
    const vocabulary = {
      2: [
        { de: 'Haus', en: 'house' },
        { de: 'Auto', en: 'car' },
        { de: 'Hund', en: 'dog' },
        { de: 'Katze', en: 'cat' },
        { de: 'Baum', en: 'tree' }
      ],
      3: [
        { de: 'Computer', en: 'computer' },
        { de: 'Schmetterling', en: 'butterfly' },
        { de: 'Regenbogen', en: 'rainbow' },
        { de: 'Fahrrad', en: 'bicycle' },
        { de: 'Elefant', en: 'elephant' }
      ]
    };
    
    const words = vocabulary[grade] || vocabulary[2];
    
    for (let i = 0; i < problemCount; i++) {
      const word = words[i % words.length];
      
      problems.push({
        question: `Wie heißt "${word.de}" auf Englisch?`,
        correct_answer: word.en,
        options: [word.en, word.en + 's', word.de, word.en.toUpperCase()],
        question_type: 'vocabulary'
      });
    }
    
    const challenge = {
      id: Date.now().toString(),
      grade: grade,
      problems: problems,
      created_at: new Date().toISOString()
    };
    
    return Promise.resolve({ challenge: challenge, success: true });
  },

  // Settings Functions
  getMathSettings: () => Promise.resolve(mockMathSettings),
  updateMathSettings: (settings) => {
    console.log('🔍 DEBUG: Input settings object:', JSON.stringify(settings, null, 2));
    console.log('🔍 DEBUG: Before update mockMathSettings:', JSON.stringify(mockMathSettings, null, 2));
    
    mockMathSettings = { ...mockMathSettings, ...settings };
    
    console.log('🔍 DEBUG: After update mockMathSettings:', JSON.stringify(mockMathSettings, null, 2));
    console.log('🧮 Mock: Math settings updated:', mockMathSettings);
    return Promise.resolve({ message: 'Settings updated' });
  },

  getGermanSettings: () => Promise.resolve(mockGermanSettings),
  updateGermanSettings: (settings) => {
    mockGermanSettings = { ...mockGermanSettings, ...settings };
    console.log('📖 Mock: German settings updated:', mockGermanSettings);
    return Promise.resolve({ message: 'Settings updated' });
  },

  getEnglishSettings: () => Promise.resolve(mockEnglishSettings),
  updateEnglishSettings: (settings) => {
    mockEnglishSettings = { ...mockEnglishSettings, ...settings };
    console.log('🇬🇧 Mock: English settings updated:', mockEnglishSettings);
    return Promise.resolve({ message: 'Settings updated' });
  }
};

export const isMockMode = () => MOCK_MODE;