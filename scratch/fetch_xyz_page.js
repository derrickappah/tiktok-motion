const https = require('https');
const fs = require('fs');

function fetch(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

async function run() {
  const files = [
    'app/(front-end)/xyz/page-d26746c6e34c1c53.js',
    'app/(front-end)/xyz/layout-f391b0e6fe1be0e5.js',
    'app/(front-end)/error-770da1ebc4c6b704.js',
    'app/(front-end)/signin/page-8a56d76979014b18.js'
  ];

  for (const f of files) {
    console.log('Downloading ' + f);
    const data = await fetch('https://mamscoenterprise.com/_next/static/chunks/' + f);
    const fname = f.replace(/[\/\(\)]/g, '_');
    fs.writeFileSync('scratch/' + fname, data);
    console.log(`Saved ${fname}: ${data.length} bytes`);
  }
}

run().catch(console.error);
