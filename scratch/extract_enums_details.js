const fs = require('fs');
const code = fs.readFileSync('scratch/static_chunks_6400-30f6d76dc724666c.js', 'utf8');

const idx = code.indexOf('$Enums');
if (idx !== -1) {
  // Find where $Enums are defined or populated
  const matches = [...code.matchAll(/t\.\$Enums\.([A-Za-z0-9_]+)\s*=\s*({[^}]+})/g)];
  console.log('Enums count:', matches.length);
  matches.forEach(m => {
    console.log(`Enum: ${m[1]} -> ${m[2]}`);
  });
}
