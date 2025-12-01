// Stability Test: Execute 5 minutes at 80% of X (best previous level without degradation)
// This test confirms system stability at a sustainable load level
//
// Configuration:
// - BASE_LEVEL: The best previous level without degradation (default: 200)
// - Calculates 80% of BASE_LEVEL automatically
// - Ramp-up: 60 seconds
// - Hold duration: 5 minutes

const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');
const path = require('path');
const http = require('http');
const https = require('https');

// Handle EPIPE errors when output is redirected (e.g., node script.js >> output.txt)
// This prevents the process from crashing when the pipe is closed
process.stdout.on('error', (err) => {
  if (err.code === 'EPIPE') {
    // Silently ignore EPIPE errors when stdout is closed
    process.exit(0);
  }
});

process.stderr.on('error', (err) => {
  if (err.code === 'EPIPE') {
    // Silently ignore EPIPE errors when stderr is closed
    process.exit(0);
  }
});

// Configuration
const API_URL = 'http://api-load-balancer-349981975.us-east-1.elb.amazonaws.com:8000/api/videos/upload';
const AUTH_TOKEN = process.env.AUTH_TOKEN || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwamt6em1fMTc2MzAwMzk5MjIyOEBleGFtcGxlLmNvbSIsImV4cCI6MTc2NDEyNzgzMH0.FVlQmTBXF2-rKpsvAwMoDc0vNcb_Q3RSp2P9x01VRqc'
const VIDEO_FILE_PATH = path.join(__dirname, '..', 'sample-video.mp4');

// Test parameters
const BASE_LEVEL = parseInt(process.env.BASE_LEVEL) || 200; // Best previous level without degradation
const STABILITY_LEVEL = Math.floor(BASE_LEVEL * 0.8); // 80% of base level
const RAMP_UP_DURATION = 60 * 1000; // 60 seconds in milliseconds
const HOLD_DURATION = 5 * 60 * 1000; // 5 minutes in milliseconds

// Get video file size in bytes
let VIDEO_FILE_SIZE_BYTES = 0;
try {
  const videoStats = fs.statSync(VIDEO_FILE_PATH);
  VIDEO_FILE_SIZE_BYTES = videoStats.size;
} catch (error) {
  console.warn(`⚠️  Warning: Could not get video file size: ${error.message}`);
}

// Create HTTP agents with keep-alive to reuse connections and prevent socket closures
// This significantly improves performance and prevents "socket closed" errors
const httpAgent = new http.Agent({
  keepAlive: true,
  keepAliveMsecs: 1000,
  maxSockets: 50, // Maximum number of sockets per host
  maxFreeSockets: 10, // Maximum number of free sockets to keep open
  timeout: 60000, // Socket timeout
  scheduling: 'fifo' // First in, first out scheduling
});

const httpsAgent = new https.Agent({
  keepAlive: true,
  keepAliveMsecs: 1000,
  maxSockets: 50,
  maxFreeSockets: 10,
  timeout: 60000,
  scheduling: 'fifo'
});

// Configure axios to use the agents
const axiosInstance = axios.create({
  httpAgent: httpAgent,
  httpsAgent: httpsAgent,
  timeout: 300000, // 5 minutes timeout
  maxContentLength: Infinity,
  maxBodyLength: Infinity
});

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
    formData.append('title', `stability_user${userId}_req${requestNumber}`);
    formData.append('file', fs.createReadStream(VIDEO_FILE_PATH));

    // Make request using the configured axios instance with keep-alive
    const response = await axiosInstance.post(API_URL, formData, {
      headers: {
        'Authorization': `Bearer ${AUTH_TOKEN}`,
        ...formData.getHeaders()
      }
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
async function runStabilityTest() {
  const start = Date.now();
  console.log(`🚀 Starting Stability Test at ${new Date(start).toISOString()}`);
  console.log(`📊 Configuration:`);
  console.log(`   - API URL: ${API_URL}`);
  console.log(`   - Base Level (X): ${BASE_LEVEL} users`);
  console.log(`   - Stability Level (80% of X): ${STABILITY_LEVEL} users`);
  console.log(`   - Ramp-Up Duration: ${RAMP_UP_DURATION / 1000} seconds (60 seconds)`);
  console.log(`   - Hold Duration: ${HOLD_DURATION / 1000} seconds (5 minutes)`);
  console.log(`   - Video File: ${VIDEO_FILE_PATH}`);
  console.log(`   - Video File Size: ${(VIDEO_FILE_SIZE_BYTES / (1024 * 1024)).toFixed(2)} MB`);
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
  const schedule = calculateRampUpSchedule(STABILITY_LEVEL, RAMP_UP_DURATION);
  
  console.log(`📈 Phase 1: Ramp-Up (0 → ${STABILITY_LEVEL} users in 60 seconds)`);
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
    
    if (userSchedule.userId % 20 === 0 || userSchedule.userId === STABILITY_LEVEL) {
      console.log(`   ✅ Started user ${userSchedule.userId}/${STABILITY_LEVEL}`);
    }
  }
  
  console.log(`\n📊 Phase 2: Stability Hold (${STABILITY_LEVEL} users for 5 minutes)`);
  console.log(`   All users active, maintaining stable load at 80% of base level...`);
  
  // Wait for ramp-up to complete
  await new Promise(resolve => setTimeout(resolve, RAMP_UP_DURATION - (Date.now() - testStartTime)));
  
  // Phase 2: Hold - all users are now active
  const holdStartTime = Date.now();
  console.log(`   Stability phase started at ${new Date(holdStartTime).toISOString()}`);
  
  // Wait for hold duration (5 minutes)
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
  
  // Calculate throughput in MB/min and MB/s (based on successful uploads)
  const totalMBUploaded = (stats.successfulRequests * VIDEO_FILE_SIZE_BYTES) / (1024 * 1024); // Convert bytes to MB
  const mbPerMinute = totalMBUploaded / (totalTestDuration / 60);
  const mbPerSecond = totalMBUploaded / totalTestDuration;
  
  // Calculate response time percentiles and variability metrics
  const sortedDurations = stats.responseTimeHistory
    .map(r => r.duration)
    .sort((a, b) => a - b);
  
  const p50 = sortedDurations.length > 0 ? sortedDurations[Math.floor(sortedDurations.length * 0.5)] : null;
  const p95 = sortedDurations.length > 0 ? sortedDurations[Math.floor(sortedDurations.length * 0.95)] : null;
  const p99 = sortedDurations.length > 0 ? sortedDurations[Math.floor(sortedDurations.length * 0.99)] : null;
  
  // Calculate standard deviation of processing time
  let stdDev = 0;
  if (sortedDurations.length > 0) {
    const mean = avgTime;
    const variance = sortedDurations.reduce((sum, d) => sum + Math.pow(d - mean, 2), 0) / sortedDurations.length;
    stdDev = Math.sqrt(variance);
  }
  
  // Print results
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('📊 STABILITY TEST RESULTS');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`⏱️  Total Test Duration: ${totalTestDuration.toFixed(2)} seconds (${(totalTestDuration / 60).toFixed(2)} minutes)`);
  console.log(`👥 Stability Level: ${STABILITY_LEVEL} users (80% of ${BASE_LEVEL})`);
  console.log(`📈 Total Requests: ${stats.totalRequests}`);
  console.log(`✅ Successful Requests: ${stats.successfulRequests}`);
  console.log(`❌ Failed Requests: ${stats.failedRequests}`);
  console.log(`📊 Success Rate: ${successRate.toFixed(2)}%`);
  console.log('');
  console.log('📊 Throughput Metrics (Comparable across scenarios):');
  console.log(`   - MB/min: ${mbPerMinute.toFixed(2)}`);
  console.log(`   - MB/s: ${mbPerSecond.toFixed(2)}`);
  console.log(`   - Total MB Uploaded: ${totalMBUploaded.toFixed(2)}`);
  console.log(`   - Video File Size: ${(VIDEO_FILE_SIZE_BYTES / (1024 * 1024)).toFixed(2)} MB`);
  console.log('');
  console.log('⏱️  Latency Statistics (per video):');
  console.log(`   - Average: ${avgTime.toFixed(2)}ms`);
  console.log(`   - Minimum: ${stats.minTime === Infinity ? 'N/A' : stats.minTime + 'ms'}`);
  console.log(`   - Maximum: ${stats.maxTime}ms`);
  console.log(`   - Standard Deviation: ${stdDev.toFixed(2)}ms`);
  console.log(`   - P50 (Median): ${p50 ? p50.toFixed(2) + 'ms' : 'N/A'}`);
  console.log(`   - P95: ${p95 ? p95.toFixed(2) + 'ms' : 'N/A'}`);
  console.log(`   - P99: ${p99 ? p99.toFixed(2) + 'ms' : 'N/A'}`);
  console.log('');
  
  // Analyze stability during hold phase
  const rampUpRequests = stats.responseTimeHistory.filter(r => r.timestamp < rampEndTime);
  const holdRequests = stats.responseTimeHistory.filter(r => r.timestamp >= rampEndTime && r.timestamp < holdStartTime + HOLD_DURATION);
  
  if (rampUpRequests.length > 0 && holdRequests.length > 0) {
    const rampUpAvg = rampUpRequests.reduce((sum, r) => sum + r.duration, 0) / rampUpRequests.length;
    const holdAvg = holdRequests.reduce((sum, r) => sum + r.duration, 0) / holdRequests.length;
    const degradation = ((holdAvg - rampUpAvg) / rampUpAvg) * 100;
    
    // Calculate variability metrics for hold phase
    const holdDurations = holdRequests.map(r => r.duration).sort((a, b) => a - b);
    const holdMean = holdAvg;
    const holdVariance = holdDurations.reduce((sum, d) => sum + Math.pow(d - holdMean, 2), 0) / holdDurations.length;
    const holdStdDev = Math.sqrt(holdVariance);
    const coefficientOfVariation = (holdStdDev / holdMean) * 100;
    
    // Calculate percentiles for hold phase
    const holdP50 = holdDurations[Math.floor(holdDurations.length * 0.5)];
    const holdP95 = holdDurations[Math.floor(holdDurations.length * 0.95)];
    const holdP99 = holdDurations[Math.floor(holdDurations.length * 0.99)];
    
    console.log('📉 Variability Analysis (Hold Phase):');
    console.log(`   - Average Processing Time: ${holdAvg.toFixed(2)}ms`);
    console.log(`   - Standard Deviation: ${holdStdDev.toFixed(2)}ms`);
    console.log(`   - Coefficient of Variation: ${coefficientOfVariation.toFixed(2)}%`);
    console.log(`   - P50 (Median): ${holdP50 ? holdP50.toFixed(2) + 'ms' : 'N/A'}`);
    console.log(`   - P95: ${holdP95 ? holdP95.toFixed(2) + 'ms' : 'N/A'}`);
    console.log(`   - P99: ${holdP99 ? holdP99.toFixed(2) + 'ms' : 'N/A'}`);
    console.log('');
    console.log('📊 Performance Comparison (Ramp-Up vs Hold):');
    console.log(`   - Ramp-Up Avg Response Time: ${rampUpAvg.toFixed(2)}ms`);
    console.log(`   - Hold Phase Avg Response Time: ${holdAvg.toFixed(2)}ms`);
    console.log(`   - Performance Change: ${degradation > 0 ? '+' : ''}${degradation.toFixed(2)}%`);
    
    if (degradation > 50) {
      console.log(`   ⚠️  WARNING: Significant performance degradation detected (>50%)`);
    } else if (degradation > 20) {
      console.log(`   ⚠️  CAUTION: Moderate performance degradation detected (>20%)`);
    } else if (degradation < -20) {
      console.log(`   ✅ Performance improved during hold phase`);
    } else {
      console.log(`   ✅ Performance is stable`);
    }
    
    if (coefficientOfVariation < 30) {
      console.log(`   ✅ Response times are stable (low variation)`);
    } else if (coefficientOfVariation < 50) {
      console.log(`   ⚠️  Response times show moderate variation`);
    } else {
      console.log(`   ⚠️  WARNING: Response times show high variation (unstable)`);
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
  
  const end = Date.now();
  const duration = end - start;
  console.log(`🏁 Test completed at ${new Date(end).toISOString()}`);
  console.log(`🕒 Total test duration: ${duration / 1000} seconds (${(duration / 1000 / 60).toFixed(2)} minutes)`);
  console.log('═══════════════════════════════════════════════════════════');
  
  // Return exit code based on success rate and stability
  if (successRate < 95) {
    console.log('❌ Test failed: Success rate below 95%');
    process.exit(1);
  } else {
    console.log('✅ Test passed: Success rate above 95%');
    process.exit(0);
  }
}

// Run the test
runStabilityTest().catch(error => {
  console.error('❌ Test failed:', error);
  process.exit(1);
});

