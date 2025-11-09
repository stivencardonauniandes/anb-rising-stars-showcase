const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');

// Configuration
const API_URL = 'http://localhost:8000/api/videos/upload';
const AUTH_TOKEN = process.env.AUTH_TOKEN || 'YOUR_TOKEN_HERE';
const VIDEO_FILE_PATH = path.join(__dirname, '..', 'sample-video.mp4');

// Test parameters
const MAX_USERS = parseInt(process.env.MAX_USERS) || 100; // Default 100 users
const RAMP_UP_DURATION = 3 * 60 * 1000; // 3 minutes in milliseconds
const HOLD_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds

// Statistics
const stats = {
  totalRequests: 0,
  successfulRequests: 0,
  failedRequests: 0,
  totalTime: 0,
  minTime: Infinity,
  maxTime: 0,
  errors: [],
  requestsByUser: {},
  responseTimeHistory: []
};

// Function to upload a video
async function uploadVideo(userId, requestNumber) {
  const startTime = Date.now();
  
  try {
    // Create form data
    const formData = new FormData();
    formData.append('title', `ramp_user${userId}_req${requestNumber}`);
    formData.append('file', fs.createReadStream(VIDEO_FILE_PATH));

    // Make request
    const response = await axios.post(API_URL, formData, {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`,
        ...formData.getHeaders()
      },
      timeout: 300000 // 5 minutes timeout
    });

    const endTime = Date.now();
    const duration = endTime - startTime;
    
    // Update statistics
    stats.totalRequests++;
    stats.successfulRequests++;
    stats.totalTime += duration;
    stats.minTime = Math.min(stats.minTime, duration);
    stats.maxTime = Math.max(stats.maxTime, duration);
    stats.responseTimeHistory.push({
      timestamp: startTime,
      duration,
      userId,
      requestNumber
    });
    
    if (!stats.requestsByUser[userId]) {
      stats.requestsByUser[userId] = { total: 0, successful: 0, failed: 0 };
    }
    stats.requestsByUser[userId].total++;
    stats.requestsByUser[userId].successful++;
    
    return { success: true, duration, taskId: response.data.task_id };
    
  } catch (error) {
    const endTime = Date.now();
    const duration = endTime - startTime;
    
    // Update statistics
    stats.totalRequests++;
    stats.failedRequests++;
    stats.totalTime += duration;
    stats.minTime = Math.min(stats.minTime, duration);
    stats.maxTime = Math.max(stats.maxTime, duration);
    stats.errors.push({
      userId,
      requestNumber,
      error: error.message,
      status: error.response?.status,
      duration,
      timestamp: startTime
    });
    
    if (!stats.requestsByUser[userId]) {
      stats.requestsByUser[userId] = { total: 0, successful: 0, failed: 0 };
    }
    stats.requestsByUser[userId].total++;
    stats.requestsByUser[userId].failed++;
    
    return { success: false, duration, error: error.message };
  }
}

// Function to simulate a user uploading videos continuously
async function simulateUser(userId, startTime, endTime) {
  let requestNumber = 1;
  const userStartTime = Date.now();
  
  while (Date.now() < endTime) {
    await uploadVideo(userId, requestNumber);
    requestNumber++;
    
    // Small delay between requests
    await new Promise(resolve => setTimeout(resolve, 200));
  }
  
  return requestNumber - 1;
}

// Function to calculate ramp-up schedule
function calculateRampUpSchedule(maxUsers, rampDuration) {
  const schedule = [];
  const interval = rampDuration / maxUsers; // Time between each user start
  
  for (let i = 1; i <= maxUsers; i++) {
    const startTime = interval * (i - 1);
    schedule.push({
      userId: i,
      startTime: startTime
    });
  }
  
  return schedule;
}

// Main function
async function runRampUpTest() {
  console.log('🚀 Starting Ramp-Up Load Test...');
  console.log(`📊 Configuration:`);
  console.log(`   - API URL: ${API_URL}`);
  console.log(`   - Max Users: ${MAX_USERS}`);
  console.log(`   - Ramp-Up Duration: ${RAMP_UP_DURATION / 1000} seconds (3 minutes)`);
  console.log(`   - Hold Duration: ${HOLD_DURATION / 1000} seconds (5 minutes)`);
  console.log(`   - Video File: ${VIDEO_FILE_PATH}`);
  console.log('');
  
  // Check if video file exists
  if (!fs.existsSync(VIDEO_FILE_PATH)) {
    console.error(`❌ Video file not found: ${VIDEO_FILE_PATH}`);
    process.exit(1);
  }
  
  // Check if token is set
  if (AUTH_TOKEN === 'YOUR_TOKEN_HERE') {
    console.error('❌ AUTH_TOKEN not set. Please set it via environment variable:');
    console.error('   export AUTH_TOKEN="your-token-here"');
    process.exit(1);
  }
  
  const testStartTime = Date.now();
  const rampEndTime = testStartTime + RAMP_UP_DURATION;
  const holdEndTime = rampEndTime + HOLD_DURATION;
  
  // Calculate ramp-up schedule
  const schedule = calculateRampUpSchedule(MAX_USERS, RAMP_UP_DURATION);
  
  console.log(`📈 Phase 1: Ramp-Up (0 → ${MAX_USERS} users in 3 minutes)`);
  console.log(`   Starting users gradually...`);
  
  // Phase 1: Ramp-Up
  const userPromises = [];
  for (const userSchedule of schedule) {
    const userStartTime = testStartTime + userSchedule.startTime;
    
    // Wait until it's time for this user to start
    const waitTime = userStartTime - Date.now();
    if (waitTime > 0) {
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
    
    // Start user
    const userPromise = simulateUser(userSchedule.userId, userStartTime, holdEndTime);
    userPromises.push(userPromise);
    
    if (userSchedule.userId % 10 === 0) {
      console.log(`   ✅ Started user ${userSchedule.userId}/${MAX_USERS}`);
    }
  }
  
  console.log(`\n📊 Phase 2: Hold (${MAX_USERS} users for 5 minutes)`);
  console.log(`   All users active, maintaining load...`);
  
  // Wait for ramp-up to complete
  await new Promise(resolve => setTimeout(resolve, RAMP_UP_DURATION - (Date.now() - testStartTime)));
  
  // Phase 2: Hold - all users are now active
  const holdStartTime = Date.now();
  console.log(`   Hold phase started at ${new Date(holdStartTime).toISOString()}`);
  
  // Wait for hold duration
  await new Promise(resolve => setTimeout(resolve, HOLD_DURATION));
  
  // Wait for all users to finish their current requests
  console.log(`\n⏳ Waiting for all requests to complete...`);
  await Promise.all(userPromises);
  
  const testEndTime = Date.now();
  const totalTestDuration = (testEndTime - testStartTime) / 1000;
  
  // Calculate statistics
  const avgTime = stats.totalRequests > 0 ? stats.totalTime / stats.totalRequests : 0;
  const successRate = stats.totalRequests > 0 ? (stats.successfulRequests / stats.totalRequests) * 100 : 0;
  const requestsPerSecond = stats.totalRequests / totalTestDuration;
  
  // Calculate response time percentiles
  const sortedDurations = stats.responseTimeHistory
    .map(r => r.duration)
    .sort((a, b) => a - b);
  
  const p50 = sortedDurations[Math.floor(sortedDurations.length * 0.5)];
  const p95 = sortedDurations[Math.floor(sortedDurations.length * 0.95)];
  const p99 = sortedDurations[Math.floor(sortedDurations.length * 0.99)];
  
  // Print results
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('📊 RAMP-UP LOAD TEST RESULTS');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`⏱️  Total Test Duration: ${totalTestDuration.toFixed(2)} seconds (${(totalTestDuration / 60).toFixed(2)} minutes)`);
  console.log(`👥 Max Concurrent Users: ${MAX_USERS}`);
  console.log(`📈 Total Requests: ${stats.totalRequests}`);
  console.log(`✅ Successful Requests: ${stats.successfulRequests}`);
  console.log(`❌ Failed Requests: ${stats.failedRequests}`);
  console.log(`📊 Success Rate: ${successRate.toFixed(2)}%`);
  console.log(`⚡ Requests per Second: ${requestsPerSecond.toFixed(2)}`);
  console.log('');
  console.log('⏱️  Response Time Statistics:');
  console.log(`   - Average: ${avgTime.toFixed(2)}ms`);
  console.log(`   - Minimum: ${stats.minTime === Infinity ? 'N/A' : stats.minTime + 'ms'}`);
  console.log(`   - Maximum: ${stats.maxTime}ms`);
  console.log(`   - P50 (Median): ${p50 || 'N/A'}ms`);
  console.log(`   - P95: ${p95 || 'N/A'}ms`);
  console.log(`   - P99: ${p99 || 'N/A'}ms`);
  console.log('');
  
  // Analyze degradation
  const rampUpRequests = stats.responseTimeHistory.filter(r => r.timestamp < rampEndTime);
  const holdRequests = stats.responseTimeHistory.filter(r => r.timestamp >= rampEndTime && r.timestamp < holdStartTime + HOLD_DURATION);
  
  if (rampUpRequests.length > 0 && holdRequests.length > 0) {
    const rampUpAvg = rampUpRequests.reduce((sum, r) => sum + r.duration, 0) / rampUpRequests.length;
    const holdAvg = holdRequests.reduce((sum, r) => sum + r.duration, 0) / holdRequests.length;
    const degradation = ((holdAvg - rampUpAvg) / rampUpAvg) * 100;
    
    console.log('📉 Performance Analysis:');
    console.log(`   - Ramp-Up Avg Response Time: ${rampUpAvg.toFixed(2)}ms`);
    console.log(`   - Hold Phase Avg Response Time: ${holdAvg.toFixed(2)}ms`);
    console.log(`   - Performance Degradation: ${degradation.toFixed(2)}%`);
    
    if (degradation > 50) {
      console.log(`   ⚠️  WARNING: Significant performance degradation detected (>50%)`);
    } else if (degradation > 20) {
      console.log(`   ⚠️  CAUTION: Moderate performance degradation detected (>20%)`);
    } else {
      console.log(`   ✅ Performance is stable`);
    }
    console.log('');
  }
  
  if (stats.errors.length > 0) {
    console.log('❌ Errors Summary:');
    const errorByStatus = {};
    stats.errors.forEach(err => {
      const status = err.status || 'UNKNOWN';
      errorByStatus[status] = (errorByStatus[status] || 0) + 1;
    });
    
    Object.entries(errorByStatus).forEach(([status, count]) => {
      console.log(`   - Status ${status}: ${count} errors`);
    });
    
    if (stats.errors.length > 0) {
      console.log(`\n   First 5 errors:`);
      stats.errors.slice(0, 5).forEach(err => {
        console.log(`   - User ${err.userId}, Request ${err.requestNumber}: ${err.error} (${err.status || 'N/A'})`);
      });
    }
    console.log('');
  }
  
  console.log('═══════════════════════════════════════════════════════════');
  
  // Return exit code based on success rate
  if (successRate < 95) {
    console.log('❌ Test failed: Success rate below 95%');
    process.exit(1);
  } else {
    console.log('✅ Test passed: Success rate above 95%');
    process.exit(0);
  }
}

// Run the test
runRampUpTest().catch(error => {
  console.error('❌ Test failed:', error);
  process.exit(1);
});

