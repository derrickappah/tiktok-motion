const https = require('https');
const fs = require('fs');

function fetch(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' } }, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
    }).on('error', reject);
  });
}

async function run() {
  const res = await fetch('https://mamscoenterprise.com/');
  console.log('Status:', res.status);
  console.log('Headers:', res.headers);
  fs.writeFileSync('scratch/mamsco_home.html', res.body);
  
  const chunkRegex = /static\/chunks\/[a-zA-Z0-9_\-\.\/]+\.js/g;
  const chunks = [...new Set(res.body.match(chunkRegex) || [])];
  console.log('Found chunks:', chunks);

  // Look for any links or routes
  const hrefs = [...new Set([...res.body.matchAll(/href="([^"]+)"/g)].map(m => m[1]))];
  console.log('Hrefs:', hrefs);
}

run().catch(console.error);
