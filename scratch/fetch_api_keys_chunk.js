const https = require('https');
const fs = require('fs');

https.get('https://mamscoenterprise.com/_next/static/chunks/app/(front-end)/agent/(dashboard)/api-keys/page-3e4051c5bf85677d.js', {
  headers: { 'User-Agent': 'Mozilla/5.0' }
}, res => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    fs.writeFileSync('scratch/page_agent_api_keys.js', d);
    console.log('Saved page_agent_api_keys.js:', d.length, 'bytes');
  });
});
