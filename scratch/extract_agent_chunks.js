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
  for (const page of ['/agent', '/agent/storefront', '/agent/cart', '/register']) {
    console.log(`\nFetching ${page}...`);
    const html = await fetch('https://mamscoenterprise.com' + page);
    fs.writeFileSync(`scratch/page_${page.replace(/[\/\\]/g, '_')}.html`, html);
    const chunkRegex = /static\/chunks\/[a-zA-Z0-9_\-\.\/]+\.js/g;
    const chunks = [...new Set(html.match(chunkRegex) || [])];
    console.log(`Chunks for ${page}:`, chunks);
  }
}

run().catch(console.error);
