const https = require('https');

function post(path, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = https.request('https://mamscoenterprise.com' + path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data),
        'User-Agent': 'Mozilla/5.0'
      }
    }, res => {
      let resp = '';
      res.on('data', c => resp += c);
      res.on('end', () => resolve({ status: res.statusCode, body: resp }));
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

async function run() {
  const t1 = await post('/api/orders/track', { phone: '0241234567' });
  console.log('/api/orders/track:', t1.status, t1.body);

  const t2 = await post('/api/orders/afa/track', { phone: '0241234567' });
  console.log('/api/orders/afa/track:', t2.status, t2.body);

  const t3 = await post('/api/orders/mtn/precheck', { phoneNumbers: ['0241234567'] });
  console.log('/api/orders/mtn/precheck:', t3.status, t3.body);
}

run().catch(console.error);
