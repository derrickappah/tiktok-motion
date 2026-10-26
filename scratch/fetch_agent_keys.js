const https = require('https');
const fs = require('fs');

https.get('https://mamscoenterprise.com/agent/api-keys', {
  headers: { 'User-Agent': 'Mozilla/5.0' }
}, res => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    fs.writeFileSync('scratch/page_agent_api_keys.html', d);
    console.log('Saved page_agent_api_keys.html:', d.length, 'bytes');
    const scripts = [...d.matchAll(/src="([^"]+\.js)"/g)].map(m => m[1]);
    console.log('Scripts:', scripts.filter(s => s.includes('app/')));
  });
});
