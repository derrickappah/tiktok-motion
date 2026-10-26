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

const chunksToFetch = {
  '314': '314.a9313da0a405b3c8.js',
  '2235': '2235.e807fca4d488837e.js',
  '3286': '3286.66de34a18b2bad79.js',
  '4239': '4239.b1794e442cbb6bc5.js',
  '5154': '5154.ca46102363a0a51f.js',
  '7850': '7850.b2b57aed24936855.js',
  '7989': '7989.432680a828bfdb45.js'
};

async function run() {
  for (const [id, file] of Object.entries(chunksToFetch)) {
    const url = `https://mamscoenterprise.com/_next/static/chunks/${file}`;
    console.log(`Fetching chunk ${id} (${file})...`);
    const data = await fetch(url);
    fs.writeFileSync(`scratch/chunk_${id}_${file}`, data);
    console.log(`Saved chunk ${id}: ${data.length} bytes`);
  }
}

run().catch(console.error);
