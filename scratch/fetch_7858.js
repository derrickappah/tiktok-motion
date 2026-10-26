const https = require('https');
const fs = require('fs');

https.get('https://mamscoenterprise.com/_next/static/chunks/7858-9307cefea03e61ad.js', {
  headers: { 'User-Agent': 'Mozilla/5.0' }
}, res => {
  let d = '';
  res.on('data', c => d += c);
  res.on('end', () => {
    fs.writeFileSync('scratch/chunk_7858.js', d);
    console.log('Saved chunk_7858.js:', d.length, 'bytes');
  });
});
