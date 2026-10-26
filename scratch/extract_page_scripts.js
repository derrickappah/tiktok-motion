const fs = require('fs');

function checkScripts(file) {
  const html = fs.readFileSync(file, 'utf8');
  console.log(`\n=== Scripts in ${file} ===`);
  const regex = /src="([^"]+\.js)"/g;
  let m;
  while ((m = regex.exec(html)) !== null) {
    if (m[1].includes('app/')) {
      console.log('App chunk:', m[1]);
    }
  }
}

checkScripts('scratch/page__agent.html');
checkScripts('scratch/page__agent_storefront.html');
checkScripts('scratch/page__agent_cart.html');
checkScripts('scratch/page__register.html');
