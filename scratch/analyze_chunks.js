const fs = require('fs');

function inspectFile(filename) {
  const code = fs.readFileSync(filename, 'utf8');
  console.log(`\n=================== ${filename} ===================`);
  
  // Find regex strings
  const stringRegex = /["'`]([a-zA-Z0-9_\-\.\/\:\?\=\&\%\@\s]{3,120})["'`]/g;
  const strings = [...new Set([...code.matchAll(stringRegex)].map(m => m[1]))];
  
  const relevant = strings.filter(s => {
    const l = s.toLowerCase();
    return l.includes('api') || l.includes('order') || l.includes('pay') || 
           l.includes('bundle') || l.includes('breezy') || l.includes('telco') ||
           l.includes('provider') || l.includes('wallet') || l.includes('ghana') ||
           l.includes('network') || l.includes('mtn') || l.includes('telecel') ||
           l.includes('transaction') || l.includes('webhook') || l.includes('token') ||
           l.includes('database') || l.includes('prisma') || l.includes('afa');
  });

  console.log('Total relevant strings:', relevant.length);
  relevant.slice(0, 100).forEach(s => console.log(' - ', s));
}

inspectFile('scratch/static_chunks_6400-30f6d76dc724666c.js');
inspectFile('scratch/static_chunks_3335-7167d2550fefadb7.js');
inspectFile('scratch/static_chunks_1513-de29b4e32d8357c4.js');
