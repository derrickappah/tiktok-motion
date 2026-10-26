const https = require('https');

function get(path) {
  return new Promise((resolve, reject) => {
    https.get('https://mamscoenterprise.com' + path, {
      headers: { 'User-Agent': 'Mozilla/5.0' }
    }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve({ status: res.statusCode, headers: res.headers, body: data }));
    }).on('error', reject);
  });
}

async function run() {
  const cfg = await get('/api/deposit/paystack/config');
  console.log('/api/deposit/paystack/config:', cfg.status);
  console.log(cfg.body);

  const pkgs = await get('/api/packages');
  console.log('\n/api/packages:', pkgs.status);
  try {
    const json = JSON.parse(pkgs.body);
    console.log('Total packages:', json.length);
    json.forEach(p => {
      console.log(`- ${p.provider} (${p.type}, duration: ${p.duration}): ${p.bundles ? p.bundles.length : 0} bundles`);
    });
    console.log('\nSample package:', JSON.stringify(json[0], null, 2));
  } catch (e) {
    console.log(pkgs.body.slice(0, 500));
  }
}

run().catch(console.error);
