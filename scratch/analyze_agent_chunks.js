const fs = require('fs');

const files = [
  'scratch/chunk_app__front-end__agent__dashboard__page-ed490c562cf0c385.js',
  'scratch/chunk_app__front-end__agent__dashboard__layout-47763283fca42a43.js',
  'scratch/chunk_app__front-end__agent__dashboard__storefront_page-c8f5b96542720527.js',
  'scratch/chunk_app__front-end__agent__dashboard__cart_page-56897fc181a4f7bc.js',
  'scratch/chunk_app__front-end__register_page-9f704782b0a23566.js'
];

files.forEach(f => {
  const code = fs.readFileSync(f, 'utf8');
  console.log(`\n=================== ${f} ===================`);
  
  // Extract all API paths
  const apis = [...code.matchAll(/["'](\/(api|v1|v2)[^"']+)["']/g)].map(m => m[1]);
  console.log('APIs:', [...new Set(apis)]);

  // Extract all axios or fetch calls
  const methods = [...code.matchAll(/\.(get|post|put|delete|patch)\(["']([^"']+)["']/g)].map(m => `${m[1].toUpperCase()} ${m[2]}`);
  console.log('HTTP calls:', [...new Set(methods)]);

  // Search for interesting keywords
  const kws = [...code.matchAll(/([a-zA-Z0-9_\-\.]{3,40}(?:provider|wallet|balance|deposit|loan|storefront|cart|order|bundle|discount|rate)[a-zA-Z0-9_\-\.]*)/gi)].map(m => m[0]);
  console.log('Sample domain terms:', [...new Set(kws)].slice(0, 30));
});
