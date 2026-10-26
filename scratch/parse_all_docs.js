const fs = require('fs');
const code = fs.readFileSync('scratch/chunk_7858.js', 'utf8');

// Print all endpoint documentation cards
const docCards = [...code.matchAll(/method:"([A-Z]+)",path:"([^"]+)",(?:auth:"([^"]+)",)?description:"([^"]+)"(?:,body:'([^']+)')?(?:,response:'([^']+)')?/g)];

console.log('Total doc cards:', docCards.length);
docCards.forEach((d, i) => {
  console.log(`\n--- [${i+1}] ${d[1]} ${d[2]} (${d[3] || 'Bearer Key'}) ---`);
  console.log(`Desc: ${d[4]}`);
  if (d[5]) console.log(`Body: ${d[5].replace(/\\n/g, '\n').slice(0, 200)}`);
  if (d[6]) console.log(`Response: ${d[6].replace(/\\n/g, '\n').slice(0, 200)}`);
});
