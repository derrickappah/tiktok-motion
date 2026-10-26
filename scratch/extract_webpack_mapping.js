const fs = require('fs');

const wp = fs.readFileSync('scratch/all_webpack-d95b336fb4fa2206.js', 'utf8');

// Search for the function that computes the chunk URL
// typically e.u = e => ...
const uIdx = wp.indexOf('.u=');
if (uIdx !== -1) {
  console.log('Chunk URL builder:');
  console.log(wp.substring(uIdx, uIdx + 400));
}

// Find chunk mapping table
const ids = ['314', '5154', '4239', '7850', '7989'];
ids.forEach(id => {
  const re = new RegExp(`["']?${id}["']?\\s*:\\s*["']([a-f0-9]+)["']`, 'g');
  const m = re.exec(wp);
  if (m) {
    console.log(`Chunk ${id} -> hash: ${m[1]}`);
  } else {
    console.log(`Chunk ${id} -> not found by simple regex`);
  }
});
