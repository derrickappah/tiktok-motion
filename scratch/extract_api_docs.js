const fs = require('fs');

const code = fs.readFileSync('scratch/chunk_7858.js', 'utf8');

// Find all endpoints, code snippets, documentation texts
const endpoints = [...code.matchAll(/["'](\/(api|v1)[^"']*)["']/g)].map(m => m[1]);
console.log('Endpoints in docs:', [...new Set(endpoints)]);

// Search for curl, Authorization, Bearer, etc.
const authHeaders = [...code.matchAll(/Bearer [^"'\`]+/g)].map(m => m[0]);
console.log('Auth headers:', authHeaders);

// Search for JSON examples
const jsonMatches = [...code.matchAll(/\{[\s\S]*?\}/g)].map(m => m[0]).filter(j => j.includes('recipient') || j.includes('package') || j.includes('bundle') || j.includes('network'));
console.log('JSON payloads found:', jsonMatches.slice(0, 5));
