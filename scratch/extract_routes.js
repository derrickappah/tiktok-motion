const fs = require('fs');

const code = fs.readFileSync('scratch/all_main-app-f82c9c5e3a67e5cf.js', 'utf8');

// Find all route strings like /(front-end)/..., /agent/..., /admin/...
const routeMatches = [...code.matchAll(/["'](\/(?:app|api|agent|admin|front-end|\([^\)]+\))[a-zA-Z0-9_\-\.\/]*)["']/g)].map(m => m[1]);
console.log('Routes in main-app:', [...new Set(routeMatches)]);

// Check for any chunks defined in main-app or layout
const chunkMatches = [...code.matchAll(/static\/chunks\/[a-zA-Z0-9_\-\.\/]+\.js/g)].map(m => m[0]);
console.log('Chunks in main-app:', [...new Set(chunkMatches)]);
