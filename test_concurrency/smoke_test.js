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
const API_URL = 'http://api-load-balancer-349981975.us-east-1.elb.amazonaws.com/api/videos/upload';
const AUTH_TOKEN = process.env.AUTH_TOKEN || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJwamt6em1fMTc2MzAwMzk5MjIyOEBleGFtcGxlLmNvbSIsImV4cCI6MTc2MzE2MzY5OX0.8NvbQ8uPbVHznCFMKP_F_L636ChIxlKNo7OAywJSWoU'; // Set via environment variable
const VIDEO_FILE_PATH = path.join(__dirname, '..', 'sample-video.mp4');
const DURATION_SECONDS = 60; // 1 minute
const CONCURRENT_USERS = 5;

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
  errors: []
};

// Function to upload a video
async function uploadVideo(userId, requestNumber) {
  const startTime = Date.now();
  
  try {
    // Create form data
    const formData = new FormData();
    formData.append('title', `x${userId}_${requestNumber}`);
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
    
    console.log(`✅ User ${userId} - Request ${requestNumber} - Success in ${duration}ms - Task ID: ${response.data.task_id}`);
    
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
      duration
    });
    
    console.error(`❌ User ${userId} - Request ${requestNumber} - Failed in ${duration}ms - Error: ${error.message}`);
    
    return { success: false, duration, error: error.message };
  }
}

// Function to simulate a user uploading videos continuously
async function simulateUser(userId) {
  let requestNumber = 1;
  const startTime = Date.now();
  const endTime = startTime + (DURATION_SECONDS * 1000);
  
  console.log(`👤 User ${userId} started uploading videos...`);
  
  while (Date.now() < endTime) {
    await uploadVideo(userId, requestNumber);
    requestNumber++;
    
    // Small delay between requests to avoid overwhelming the server
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  
  console.log(`👤 User ${userId} finished - Total requests: ${requestNumber - 1}`);
  return requestNumber - 1;
}

// Main function
async function runConcurrencyTest() {
  console.log('🚀 Starting concurrency test...');
  console.log(`📊 Configuration:`);
  console.log(`   - API URL: ${API_URL}`);
  console.log(`   - Duration: ${DURATION_SECONDS} seconds`);
  console.log(`   - Concurrent Users: ${CONCURRENT_USERS}`);
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
  
  // Start all users concurrently
  const userPromises = [];
  for (let i = 1; i <= CONCURRENT_USERS; i++) {
    userPromises.push(simulateUser(i));
  }
  
  // Wait for all users to finish
  await Promise.all(userPromises);
  
  const testEndTime = Date.now();
  const totalTestDuration = (testEndTime - testStartTime) / 1000;
  
  // Calculate statistics
  const avgTime = stats.totalRequests > 0 ? stats.totalTime / stats.totalRequests : 0;
  const successRate = stats.totalRequests > 0 ? (stats.successfulRequests / stats.totalRequests) * 100 : 0;
  const requestsPerSecond = stats.totalRequests / totalTestDuration;
  
  // Print results
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('📊 CONCURRENCY TEST RESULTS');
  console.log('═══════════════════════════════════════════════════════════');
  console.log(`⏱️  Total Test Duration: ${totalTestDuration.toFixed(2)} seconds`);
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
  console.log('');
  
  if (stats.errors.length > 0) {
    console.log('❌ Errors Summary:');
    stats.errors.slice(0, 10).forEach(err => {
      console.log(`   - User ${err.userId}, Request ${err.requestNumber}: ${err.error} (${err.status || 'N/A'})`);
    });
    if (stats.errors.length > 10) {
      console.log(`   ... and ${stats.errors.length - 10} more errors`);
    }
    console.log('');
  }
  
  console.log('═══════════════════════════════════════════════════════════');
}

// Run the test
runConcurrencyTest().catch(error => {
  console.error('❌ Test failed:', error);
  process.exit(1);
});
