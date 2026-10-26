const fs = require('fs');

const html = fs.readFileSync('scratch/mamsco_home.html', 'utf8');

// Find all push calls with RSC tree
const rscLines = [...html.matchAll(/self\.__next_f\.push\(\[1,"([^"\\]*(?:\\.[^"\\]*)*)"\]\)/g)].map(m => m[1]);

console.log('RSC lines found:', rscLines.length);

// Join and unescape
const fullRsc = rscLines.join('').replace(/\\"/g, '"').replace(/\\\\/g, '\\').replace(/\\n/g, '\n');

// Find all routes or page names mentioned
const routeRegex = /"(children|page|layout)":\["([^"]+)"/g;
let m;
while ((m = routeRegex.exec(fullRsc)) !== null) {
  console.log(`Route part: ${m[1]} -> ${m[2]}`);
}

// Find all static/chunks mentioned
const chunks = [...new Set([...fullRsc.matchAll(/static\/chunks\/[a-zA-Z0-9_\-\.\/]+\.js/g)].map(x => x[0]))];
console.log('All chunks mentioned in RSC:', chunks);
