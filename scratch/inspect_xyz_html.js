const fs = require('fs');

const html = fs.readFileSync('scratch/mamsco__xyz.html', 'utf8');

const scriptRegex = /<script\b[^>]*>([\s\S]*?)<\/script>/gi;
let match;
let count = 0;

while ((match = scriptRegex.exec(html)) !== null) {
  count++;
  const fullTag = match[0];
  const inner = match[1];
  const srcMatch = fullTag.match(/src="([^"]+)"/);
  if (srcMatch) {
    console.log(`Script ${count} (src): ${srcMatch[1]}`);
  } else {
    console.log(`Script ${count} (inline): ${inner.length} chars`);
    if (inner.includes('self.__next_f.push') || inner.includes('Track Afa Order') || inner.includes('paystack') || inner.includes('price')) {
      console.log(`  Preview: ${inner.slice(0, 300)}...`);
    }
  }
}
