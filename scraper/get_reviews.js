
const store = require('app-store-scraper');
const fs = require('fs');

const appId = process.argv[2];

if (!appId) {
  console.error('Please provide an app ID.');
  process.exit(1);
}

store.reviews({
  id: appId,
  sort: store.sort.RECENT,
  page: 1
})
.then(reviews => console.log(JSON.stringify(reviews)))
.catch(console.error);
