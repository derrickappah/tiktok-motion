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
  const chunks = [
    'static/chunks/3335-7167d2550fefadb7.js',
    'static/chunks/1513-de29b4e32d8357c4.js',
    'static/chunks/6400-30f6d76dc724666c.js',
    'static/chunks/3809-0d452e78e425477d.js',
    'static/chunks/147-e5f8f047daba0341.js'
  ];

  for (const chunk of chunks) {
    const code = await fetch(`https://mamscoenterprise.com/_next/${chunk}`);
    console.log(`Fetched ${chunk}: ${code.length} bytes`);
    fs.writeFileSync(`scratch/${chunk.replace(/[\/\\]/g, '_')}`, code);

    // Look for API endpoints, keys, urls
    const apis = [...code.matchAll(/["'](\/(api|v1|v2)[^"']+)["']/g)].map(m => m[1]);
    const urls = [...code.matchAll(/https?:\/\/[a-zA-Z0-9_\-\.:]+/g)].map(m => m[0]);
    const paystack = [...code.matchAll(/pk_[a-zA-Z0-9_]+/g)].map(m => m[0]);
    const hubtel = [...code.matchAll(/hubtel|paystack|arkesel|korapay/gi)].map(m => m[0]);

    console.log(`--- ${chunk} ---`);
    if (apis.length) console.log('  APIs:', [...new Set(apis)]);
    if (urls.length) console.log('  URLs:', [...new Set(urls)]);
    if (paystack.length) console.log('  Paystack keys:', [...new Set(paystack)]);
    if (hubtel.length) console.log('  Payment mentions:', [...new Set(hubtel)]);
  }
}

run().catch(console.error);
