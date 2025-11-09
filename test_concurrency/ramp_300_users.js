// Ramp-Up Test: 300 users
// Ramp: 0 → 300 users in 3 minutes
// Hold: 300 users for 5 minutes

process.env.MAX_USERS = '300';
require('./ramp_test.js');

