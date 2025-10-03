Search low ratings and reviews for app store's product, show all low rating reviews in a static website.

The process of workflow
- get the top paid app list by app-store-scraper, save them into local file. process them one by one
- for each app, get latest update date and all low ratings & reviews, save into local file.
- for each review, generate tags by instructions below, save into local file.
    - no update: currect app don't update for over 6 months, the problem in currect review can be solve when it update.
    - niche demand: problem in review is a niche demand, that's why owner don't want to implement it.
    - valuable opinion: currect review provide a valuable opinion which can turn into valuable idea.
- checkpoint: we cannot get all reviews data in one executing, so, we should save the the checkpoint that we progress
    - for each app, we should get the latest N reviews
    - for each app, we should prioritize the app that have nerver processed in the past, if each one have been processed in the past, prioritize to process the oldest one that was processed in the past.
    - as a result, I should can run this project many times in github action, and the next time executing should continue the checkpoint in last time.
- list all reviews in the website. 
    - columns: platform(app store, google player...), app, review, tags
    - rows: each review is in one row.
- This project can be runned many times, for every time running, new data(products, reviews) should be append into currect files, as a result, it's allow to run many times to generate all procuts and reviews.
- app-store-scraper was used to get all app store related data
- when you finish one small feature, check whether it works well or not by logging or other methods

Other platforms except app store, we can cover them later.
- Google player
- Browser extension store(Chrome, Firfox, Safari...)
- Github repository

Tips:
- Please try don't modify content in current file as possible as you can
- Set a small app amount quota (like 10) to validate the whole process and result of website, it's enought for generate the codes, I will modify quota and execute for all apps later.
- You should test by youself as much as you can
- You should test many time to evaluate the result of checkpoint parts.
- If you meet the problems if can not solve after trying all methods, you should ask help to me rather than quit directly.
- When you need to use LLM API (generate tags for each review)
    - you can use free gemini models, the free api key is store in .env file like 'gemini_api_key="AIxxxxx"'
    - please don't uplocd keys into gemini-cli or save it in other places, it's sentitive data.
- When you start a sever by npm or python, you should use nohup to execute that because you need to capture the screenshot and analysis that when running the sever, after nohup, you should monitor contents in nohup file and wait till sever can running as expected
- Program currect project based on the instructions on READMD.md, you can ask me if you have any concerns or confustion about README.md
- To run the project from this checkpoint:
    1. Ensure all Python dependencies are installed: `pip install -r requirements.txt`
    2. Run the Python scraper to get app data, reviews and tags (from the predefined list): `python3 scraper/app_scraper.py`
    3. Start the static web server from the project root: `nohup python3 -m http.server 8000 &`
    4. Open your browser to `http://localhost:8000/index.html` to view the results.
    5. To stop the server, find its process ID (e.g., `lsof -i :8000`) and use `kill <PID>`.
