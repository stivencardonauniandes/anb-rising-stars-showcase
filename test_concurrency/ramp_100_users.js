// Ramp-Up Test: 100 users
// Ramp: 0 → 100 users in 3 minutes
// Hold: 100 users for 5 minutes

process.env.MAX_USERS = '100';
require('./ramp_test.js');

