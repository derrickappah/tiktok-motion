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
  for (const path of ['/signin', '/xyz', '/privacy', '/terms']) {
    console.log(`\n=== Fetching ${path} ===`);
    const res = await fetch(`https://mamscoenterprise.com${path}`);
    console.log('Status:', res.status);
    const chunkRegex = /static\/chunks\/[a-zA-Z0-9_\-\.\/]+\.js/g;
    const chunks = [...new Set(res.body.match(chunkRegex) || [])];
    console.log('Chunks:', chunks);
    
    // Check title and some text
    const title = res.body.match(/<title>([^<]+)<\/title>/);
    if (title) console.log('Title:', title[1]);

    // Save page html
    fs.writeFileSync(`scratch/mamsco_${path.replace(/\//g, '_')}.html`, res.body);
  }
}

run().catch(console.error);
