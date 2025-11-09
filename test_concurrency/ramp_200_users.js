// Ramp-Up Test: 200 users
// Ramp: 0 → 200 users in 3 minutes
// Hold: 200 users for 5 minutes

process.env.MAX_USERS = '200';
require('./ramp_test.js');

