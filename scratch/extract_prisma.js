const fs = require('fs');

const code = fs.readFileSync('scratch/static_chunks_6400-30f6d76dc724666c.js', 'utf8');

// Look for Prisma model declarations or exports
// Prisma generated client usually defines Prisma.ModelName = { ... }
const prismaModels = [...code.matchAll(/exports\.Prisma\.([A-Za-z0-9_]+)ScalarFieldEnum\s*=\s*({[^}]+})/g)];
console.log('ScalarFieldEnums found:', prismaModels.length);
prismaModels.forEach(m => {
  console.log(`\nModel Enum: ${m[1]}`);
  console.log(m[2]);
});

// Also look for Enums
const enums = [...code.matchAll(/exports\.([A-Za-z0-9_]+)\s*=\s*exports\.\1\s*\|\|\s*\((exports\.\1\s*=\s*{[^}]+}\))/g)];
console.log('Enums found:', enums.length);
enums.forEach(e => console.log(e[0].slice(0, 200)));

// Or general exports
const allExports = [...code.matchAll(/exports\.([A-Za-z0-9_]+)\s*=/g)].map(m => m[1]);
console.log('All exports:', [...new Set(allExports)]);
