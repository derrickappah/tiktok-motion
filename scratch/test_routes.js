const https = require('https');

function fetch(path) {
  return new Promise((resolve) => {
    https.get('https://mamscoenterprise.com' + path, {
      headers: { 'User-Agent': 'Mozilla/5.0' }
    }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve({ path, status: res.statusCode, headers: res.headers, length: data.length, body: data }));
    }).on('error', err => resolve({ path, error: err.message }));
  });
}

async function run() {
  const routes = [
    '/register',
    '/agent',
    '/agent/storefront',
    '/agent/cart',
    '/admin',
    '/api/orders',
    '/api/orders/storefront',
    '/api/orders/retail',
    '/api/packages',
    '/api/auth/providers'
  ];

  for (const r of routes) {
    const res = await fetch(r);
    console.log(`${r}: status=${res.status}, location=${res.headers ? res.headers.location : ''}`);
    if (r === '/api/auth/providers') {
      console.log('Providers:', res.body);
    }
  }
}

run().catch(console.error);
