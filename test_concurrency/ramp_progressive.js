// Progressive Ramp-Up Test
// Runs multiple ramp-up tests with increasing user counts
// 100 → 200 → 300 → 500 users
// Stops when degradation is detected

const { spawn } = require('child_process');
const path = require('path');

const USER_LEVELS = [100, 200, 300, 500];
const AUTH_TOKEN = process.env.AUTH_TOKEN || 'YOUR_TOKEN_HERE';

async function runRampTest(userCount) {
  return new Promise((resolve, reject) => {
    console.log(`\n${'='.repeat(60)}`);
    console.log(`🚀 Starting Ramp-Up Test with ${userCount} users`);
    console.log(`${'='.repeat(60)}\n`);
    
    const testProcess = spawn('node', [
      path.join(__dirname, 'ramp_test.js')
    ], {
      env: {
        ...process.env,
        MAX_USERS: userCount.toString(),
        AUTH_TOKEN: AUTH_TOKEN
      },
      stdio: 'inherit'
    });
    
    testProcess.on('close', (code) => {
      if (code === 0) {
        console.log(`\n✅ Test with ${userCount} users completed successfully`);
        resolve({ success: true, userCount, code });
      } else {
        console.log(`\n❌ Test with ${userCount} users failed or showed degradation`);
        resolve({ success: false, userCount, code });
      }
    });
    
    testProcess.on('error', (error) => {
      console.error(`❌ Error running test with ${userCount} users:`, error);
      reject(error);
    });
  });
}

async function runProgressiveTests() {
  console.log('🚀 Starting Progressive Ramp-Up Load Tests');
  console.log(`📊 Will test with: ${USER_LEVELS.join(' → ')} users`);
  console.log(`⏱️  Each test: 3 min ramp-up + 5 min hold = 8 minutes`);
  console.log(`⏱️  Total estimated time: ${(USER_LEVELS.length * 8)} minutes\n`);
  
  if (AUTH_TOKEN === 'YOUR_TOKEN_HERE') {
    console.error('❌ AUTH_TOKEN not set. Please set it via environment variable:');
    console.error('   export AUTH_TOKEN="your-token-here"');
    process.exit(1);
  }
  
  const results = [];
  let degradationDetected = false;
  
  for (const userCount of USER_LEVELS) {
    if (degradationDetected) {
      console.log(`\n⚠️  Degradation detected in previous test. Stopping progressive tests.`);
      break;
    }
    
    const result = await runRampTest(userCount);
    results.push(result);
    
    if (!result.success) {
      degradationDetected = true;
      console.log(`\n⚠️  Degradation detected at ${userCount} users.`);
      console.log(`   Previous level (${USER_LEVELS[USER_LEVELS.indexOf(userCount) - 1]} users) was stable.`);
    }
    
    // Wait between tests
    if (userCount !== USER_LEVELS[USER_LEVELS.length - 1]) {
      console.log(`\n⏳ Waiting 30 seconds before next test...\n`);
      await new Promise(resolve => setTimeout(resolve, 30000));
    }
  }
  
  // Print summary
  console.log(`\n${'='.repeat(60)}`);
  console.log('📊 PROGRESSIVE RAMP-UP TEST SUMMARY');
  console.log(`${'='.repeat(60)}`);
  
  results.forEach((result, index) => {
    const status = result.success ? '✅ PASSED' : '❌ FAILED/DEGRADATION';
    console.log(`${status} - ${USER_LEVELS[index]} users`);
  });
  
  console.log(`\n${'='.repeat(60)}`);
  
  if (degradationDetected) {
    const lastSuccessful = results.findLast(r => r.success);
    if (lastSuccessful) {
      console.log(`\n✅ Maximum stable load: ${lastSuccessful.userCount} users`);
    }
    console.log(`⚠️  System shows degradation beyond this point.`);
  } else {
    console.log(`\n✅ All tests passed. System can handle up to ${USER_LEVELS[USER_LEVELS.length - 1]} users.`);
  }
  
  console.log(`${'='.repeat(60)}\n`);
}

// Run progressive tests
runProgressiveTests().catch(error => {
  console.error('❌ Progressive tests failed:', error);
  process.exit(1);
});

