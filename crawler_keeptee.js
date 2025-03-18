const puppeteer = require('puppeteer');
const cloudscraper = require('cloudscraper');
const slugify = require('slugify');
const { PromisePool } = require('@supercharge/promise-pool');
const XLSX = require('xlsx');
const fs = require('fs');

function readExcelData(fileName) {
    if (fs.existsSync(fileName)) {
        const wb = XLSX.readFile(fileName);
        const ws = wb.Sheets[wb.SheetNames[0]];
        return XLSX.utils.sheet_to_json(ws);
    }
    return [];
}

function isSlugExists(data, slug) {
    return data.some(item => item.slug === slug);
}

function appendToExcel(data, fileName) {
    let existingData = readExcelData(fileName);

    const newData = data.filter(item => !isSlugExists(existingData, item.slug));
    existingData = existingData.concat(newData);

    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(existingData);
    XLSX.utils.book_append_sheet(wb, ws, 'Crawled Data');
    XLSX.writeFile(wb, fileName);
}

function parseHTML(html) {
    const cheerio = require('cheerio');
    const $ = cheerio.load(html);
    const title = $('h1').text();
    return { title };
}

async function crawlPage(object_id) {
    const browser = await puppeteer.launch({ 
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-gpu']
     });
    const page = await browser.newPage();
    await page.setRequestInterception(true);
    page.on('request', request => {
        const resourceType = request.resourceType();
        if (['image', 'stylesheet', 'font', 'media'].includes(resourceType)) {
            request.abort();
        } else {
            request.continue();
        }
    });
    const url = `https://keeptee.com/?attachment_id=${object_id}`;

    try {
        //await page.goto(url);
        //await page.waitForSelector('h1');

        //const data = await page.evaluate(() => {
        //    const title = document.querySelector('h1').innerText;
        //    return { title };
        //});
	
	//if(data.title == 'keeptee.com'){
	//	const data = await page.evaluate(() => {
        //    		const title = document.getElementsByClassName('product-title').innerText;
        //    		return { title };
        //	});
	//}

	const response = await cloudscraper.get(url);
        const data = await parseHTML(response)

        const slug = slugify(data.title, { lower: true, strict: true });
        const result = { store: 'keeptee.com', title: data.title, link: `https://keeptee.com/product/${slug}`, slug: slug, object_id: object_id, object_name: 'product' };
        console.log(result);

        appendToExcel([result], "crawled_keeptee_data.xlsx");

        await browser.close();
        return result;
    } catch (error) {
        console.error(`Error crawling page ${object_id} ${url}:`, error);
        await browser.close();
        return null;
    }
}

async function main() {
    // const start = 123900;
    const start = 1736764;
    // const end = 123930;
    const end = 1736768;
    const pageNumbers = [];

    for (let i = start; i <= end; i++) {
        pageNumbers.push(i);
    }

    const { results, errors } = await PromisePool
        .withConcurrency(30) 
        .for(pageNumbers)
        .process(async (pageNumber) => {
            return await crawlPage(pageNumber);
        });

        console.log('Crawling completed!');
        console.log('Results:', results);
        console.log('Errors:', errors);
}

main();
