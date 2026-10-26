const fs = require('fs');
const path = require('path');

const dir = 'scratch';
const files = fs.readdirSync(dir).filter(f => f.startsWith('all_') && f.endsWith('.js'));

const results = {
  apis: new Set(),
  endpoints: new Set(),
  urls: new Set(),
  paystackKeys: new Set(),
  keywords: new Set(),
  providers: new Set(),
  emails: new Set(),
  phones: new Set()
};

const kwPattern = /hubtel|paystack|arkesel|korapay|expresspay|breezy|momo|mtn|telecel|airteltigo|superdealer|superagent|afaorder|datapackage/gi;

files.forEach(f => {
  const content = fs.readFileSync(path.join(dir, f), 'utf8');

  // Match /api/...
  const apiMatches = content.match(/["']\/api\/[a-zA-Z0-9_\-\.\/]+["']/g) || [];
  apiMatches.forEach(a => results.apis.add(a.replace(/["']/g, '')));

  // Match https?:// urls
  const urlMatches = content.match(/https?:\/\/[a-zA-Z0-9_\-\.\:\@\/\?=&#]+/g) || [];
  urlMatches.forEach(u => {
    if (!u.includes('w3.org') && !u.includes('schema.org') && !u.includes('github.com') && !u.includes('example.com') && !u.includes('stackoverflow.com') && !u.includes('pris.ly')) {
      results.urls.add(u);
    }
  });

  // Match Paystack keys
  const pkMatches = content.match(/pk_(live|test)_[a-zA-Z0-9]+/g) || [];
  pkMatches.forEach(p => results.paystackKeys.add(p));

  // Match emails
  const emailMatches = content.match(/[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+/g) || [];
  emailMatches.forEach(e => {
    if (!e.endsWith('.png') && !e.endsWith('.jpg') && !e.includes('example')) results.emails.add(e);
  });

  // Match phones
  const phoneMatches = content.match(/\b(0\d{9}|233\d{9})\b/g) || [];
  phoneMatches.forEach(p => results.phones.add(p));

  // Match keywords
  const kws = content.match(kwPattern) || [];
  kws.forEach(k => results.keywords.add(k.toLowerCase()));
});

console.log('--- APIS ---');
console.log([...results.apis]);

console.log('--- EXTERNAL URLS ---');
console.log([...results.urls]);

console.log('--- PAYSTACK KEYS ---');
console.log([...results.paystackKeys]);

console.log('--- EMAILS ---');
console.log([...results.emails]);

console.log('--- PHONES ---');
console.log([...results.phones]);

console.log('--- KEYWORDS FOUND ---');
console.log([...results.keywords]);
