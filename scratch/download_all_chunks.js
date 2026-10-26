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

const chunks = [
  'webpack-d95b336fb4fa2206.js',
  'fd9d1056-862e7eb3d8e52716.js',
  '2117-bdda6bd430bd950a.js',
  'main-app-f82c9c5e3a67e5cf.js',
  '13b76428-e1bf383848c17260.js',
  'aaea2bcf-6a6138e32f0c4709.js',
  '244-3ac3579c763bd1a3.js',
  '3464-2d1eede2c0a11343.js',
  '7261-e2b6ca949f9b37a5.js',
  '1451-329d4759a6c09227.js',
  '605-3cd6838126ded303.js',
  '4244-b0658c79fe9a4fc9.js',
  '3145-f536935a1f6eda42.js',
  '2978-7c42d0256e9fffef.js',
  '9662-45d46694ddc0995c.js',
  '3335-7167d2550fefadb7.js',
  '3809-0d452e78e425477d.js',
  '1513-de29b4e32d8357c4.js',
  '6400-30f6d76dc724666c.js',
  '5581-23b74e592b463129.js',
  '927-8d0f4477b4a682c8.js',
  '147-e5f8f047daba0341.js',
  'app/layout-54f7aa199e8adf8a.js'
];

async function run() {
  for (const c of chunks) {
    const filename = c.replace(/[\/\\]/g, '_');
    const localPath = `scratch/all_${filename}`;
    if (!fs.existsSync(localPath)) {
      console.log(`Downloading ${c}...`);
      const body = await fetch(`https://mamscoenterprise.com/_next/static/chunks/${c}`);
      fs.writeFileSync(localPath, body);
    }
  }
  console.log('All chunks downloaded. Starting deep scan...');
}

run().catch(console.error);
