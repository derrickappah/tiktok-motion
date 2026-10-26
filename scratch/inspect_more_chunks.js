const fs = require('fs');

const chunks = ['4239', '7850', '7989', '2235', '3286'];

chunks.forEach(id => {
  const file = fs.readdirSync('scratch').find(f => f.startsWith(`chunk_${id}_`));
  if (file) {
    const code = fs.readFileSync('scratch/' + file, 'utf8');
    console.log(`\n================== Chunk ${id} (${file}) ==================`);
    
    // Extract endpoints and post/get calls
    const apis = [...code.matchAll(/["'](\/(api|v1|v2)[^"']+)["']/g)].map(m => m[1]);
    console.log('APIs:', [...new Set(apis)]);

    // Extract interesting text strings
    const texts = [...code.matchAll(/["']([^"']{10,80})["']/g)].map(m => m[1]);
    const filtered = texts.filter(t => !t.includes('class') && !t.includes('stroke') && !t.includes('flex'));
    console.log('Sample texts:', filtered.slice(0, 15));
  }
});
