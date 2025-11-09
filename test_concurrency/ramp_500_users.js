// Ramp-Up Test: 500 users
// Ramp: 0 → 500 users in 3 minutes
// Hold: 500 users for 5 minutes

process.env.MAX_USERS = '500';
require('./ramp_test.js');

