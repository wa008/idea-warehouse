const store = require('app-store-scraper');

const num = process.argv[2] || 200;

store.list({
    collection: store.collection.TOP_PAID_IOS,
    num: parseInt(num, 10)
})
.then(apps => console.log(JSON.stringify(apps)))
.catch(console.error);
