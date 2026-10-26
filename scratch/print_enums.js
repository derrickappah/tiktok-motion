const fs = require('fs');
const code = fs.readFileSync('scratch/static_chunks_6400-30f6d76dc724666c.js', 'utf8');

const idx = code.indexOf('t.$Enums=');
if (idx !== -1) {
  console.log(code.substring(idx, idx + 8000));
}
