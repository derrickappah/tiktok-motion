const https = require('https');
const fs = require('fs');

function fetch(url) {
  return new Promise((resolve) => {
    https.get(url, { headers: { 'User-Agent': 'Mozilla/5.0' } }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve(d));
    });
  });
}

async function run() {
  const chunks = [
    'app/(front-end)/agent/(dashboard)/page-ed490c562cf0c385.js',
    'app/(front-end)/agent/(dashboard)/layout-47763283fca42a43.js',
    'app/(front-end)/agent/(dashboard)/storefront/page-c8f5b96542720527.js',
    'app/(front-end)/agent/(dashboard)/cart/page-56897fc181a4f7bc.js',
    'app/(front-end)/register/page-9f704782b0a23566.js'
  ];

  for (const c of chunks) {
    console.log('Fetching', c);
    const body = await fetch('https://mamscoenterprise.com/_next/static/chunks/' + c);
    const fname = 'scratch/chunk_' + c.replace(/[\/\(\)]/g, '_');
    fs.writeFileSync(fname, body);
    console.log(`Saved ${fname}: ${body.length} bytes`);
  }
}

run().catch(console.error);
