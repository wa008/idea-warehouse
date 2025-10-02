const store = require('app-store-scraper');

store.list({
    collection: store.collection.TOP_PAID_IOS,
    num: 200
})
.then(apps => console.log(JSON.stringify(apps)))
.catch(console.error);