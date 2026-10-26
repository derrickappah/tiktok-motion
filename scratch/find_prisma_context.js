const fs = require('fs');
const code = fs.readFileSync('scratch/static_chunks_6400-30f6d76dc724666c.js', 'utf8');

const idx = code.indexOf('PrismaClient');
if (idx !== -1) {
  console.log('Context around PrismaClient:');
  console.log(code.substring(Math.max(0, idx - 200), Math.min(code.length, idx + 1500)));
} else {
  console.log('PrismaClient not found directly');
}
