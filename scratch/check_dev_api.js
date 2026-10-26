const https = require('https');

function check(path) {
  return new Promise((resolve) => {
    https.get('https://mamscoenterprise.com' + path, {
      headers: { 'User-Agent': 'Mozilla/5.0' }
    }, res => {
      let d = '';
      res.on('data', c => d += c);
      res.on('end', () => resolve({ path, status: res.statusCode, body: d.slice(0, 300) }));
    });
  });
}

async function run() {
  const paths = [
    '/docs',
    '/api-docs',
    '/developer',
    '/api/v1',
    '/api/v1/balance',
    '/api/v1/packages',
    '/api/v1/orders',
    '/api/developer/keys',
    '/api/keys',
    '/api/settings',
    '/agent/api-keys',
    '/agent/settings'
  ];

  for (const p of paths) {
    const r = await check(p);
    console.log(`${p}: status=${r.status} ${r.body.length > 0 && !r.body.startsWith('<!DOCTYPE') ? r.body : ''}`);
  }
}

run().catch(console.error);
