const fs = require('fs');

function searchAllChunks() {
  const dir = 'scratch';
  const files = fs.readdirSync(dir).filter(f => f.endsWith('.js') && f.startsWith('static_chunks_'));
  
  files.forEach(f => {
    const content = fs.readFileSync(`${dir}/${f}`, 'utf8');
    console.log(`\n=== ${f} (${content.length} bytes) ===`);
    
    // Look for fetch calls or axios or api endpoints
    const apis = [...content.matchAll(/["'](\/(api|v1|v2|xyz)[^"']+)["']/g)].map(m => m[1]);
    if (apis.length) console.log('  APIs:', [...new Set(apis)]);
    
    // Look for provider names or telco names
    const telcos = [...content.matchAll(/MTN|TELECEL|AIRTELTIGO|AT_GHANA|VODAFONE|SURFLINE/gi)].map(m => m[0]);
    if (telcos.length) console.log('  Telcos:', [...new Set(telcos)]);

    // Look for provider URLs or external gateways
    const urls = [...content.matchAll(/https?:\/\/[a-zA-Z0-9_\-\.:]+/g)].map(m => m[0]);
    const extUrls = urls.filter(u => !u.includes('w3.org') && !u.includes('example.com') && !u.includes('pris.ly') && !u.includes('github.com') && !u.includes('stackoverflow.com'));
    if (extUrls.length) console.log('  Ext URLs:', [...new Set(extUrls)]);
  });
}

searchAllChunks();
