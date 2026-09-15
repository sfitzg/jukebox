import { readFileSync } from 'node:fs';
import test from 'node:test';
import assert from 'node:assert';
import { JSDOM } from 'jsdom';

import SearchController from '../site/static/js/searchController.js';

function getTextEntries(listElement) {
    return [...listElement.children].map(item => item.textContent);
}

function getIdDataEntries(listElement) {
    return [...listElement.children].map(item => item.dataset.id);
}

function getTitleAndDurationEntries(listElement) {
    return [...listElement.children].map(item => ({
        title: item.querySelector('.results-title').textContent,
        duration: item.querySelector('.results-duration').textContent
    }));
}

class FakeSearchService {
    constructor() {
        this.autocompletions = [];
        this.searches = [];
        this.handler = e => { assert.fail('empty handler called'); };
    }

    // used by test
    addAutocompleteTransaction(expectedInput) {
        let resolve;
        const resultPromise = new Promise(r => { resolve = r; });
        this.autocompletions.push({ expectedInput, resultPromise });
        return resolve;
    }

    addSearchTransaction(expectedInput) {
        let resolve;
        const resultPromise = new Promise(r => { resolve = r; });
        this.searches.push({ expectedInput, resultPromise });
        return resolve;
    }

    // used by SUT
    autocomplete(input) {
        const transaction = this.autocompletions.shift();
        assert.strictEqual(input, transaction.expectedInput);
        return transaction.resultPromise;
    }

    search(input) {
        const transaction = this.searches.shift();
        assert.strictEqual(input, transaction.expectedInput);
        return transaction.resultPromise;
    }

    listen(handler) {
        this.handler = handler;
    }
}

const html = readFileSync('../site/templates/index.html', 'utf8');

// fixture
let service;
let sut;
let Event;
let searchBox;
let searchForm;
let suggestionList;
let resultList;

test.beforeEach(() => {
    const dom = new JSDOM(html);
    Event = dom.window.Event;
    const document = dom.window.document;
    searchBox = document.getElementById('yt-search');
    searchForm = document.getElementById('search-form');
    suggestionList = document.getElementById('suggestions');
    resultList = document.getElementById('results');

    service = new FakeSearchService();
    sut = new SearchController(document, service);
});

test('input event in search box', async () => {

    const partialTerm = 'jun';
    const suggestions = ['jungle', 'juno', 'junkyard']

    const resolve = service.addAutocompleteTransaction(partialTerm);

    searchBox.value = partialTerm;
    searchBox.dispatchEvent(new Event('input'));

    resolve(suggestions);
    await Promise.resolve();

    assert.deepStrictEqual(getTextEntries(suggestionList), suggestions);
});

test('search box becomes empty', () => {

    searchBox.value = ' ';
    searchBox.dispatchEvent(new Event('input'));

    assert.strictEqual(getTextEntries(suggestionList).length, 0);
});

test('stale suggestions ignored', async () => {

    const partialTerm0 = 'jun';
    const suggestions0 = ['jungle', 'juno', 'junkyard']

    const partialTerm1 = 'bas';
    const suggestions1 = ['bastard', 'bass guitar', 'basketry']

    const resolve0 = service.addAutocompleteTransaction(partialTerm0);
    const resolve1 = service.addAutocompleteTransaction(partialTerm1);

    searchBox.value = partialTerm0;
    searchBox.dispatchEvent(new Event('input'));

    searchBox.value = partialTerm1;
    searchBox.dispatchEvent(new Event('input'));

    // resolve out of order
    resolve1(suggestions1);
    resolve0(suggestions0);
    await Promise.resolve();

    // the older one is ignored
    assert.deepStrictEqual(getTextEntries(suggestionList), suggestions1);
});

test('search box empty races stale suggestion', async () => {

    const partialTerm = 'jun';
    const suggestions = ['jungle', 'juno', 'junkyard']

    const resolve = service.addAutocompleteTransaction(partialTerm);

    searchBox.value = partialTerm;
    searchBox.dispatchEvent(new Event('input'));

    searchBox.value = ' ';
    searchBox.dispatchEvent(new Event('input'));

    // search results arrive after box is cleared
    resolve(suggestions);
    await Promise.resolve();

    // the stale results are ignored
    assert.strictEqual(getTextEntries(suggestionList).length, 0);
});

test('search button clears suggestion list', async () => {

    suggestionList.innerHTML = '<li>foo</li><li>bar</li>';
    searchBox.value = '_';
    const resolve = service.addSearchTransaction('_');
    searchForm.dispatchEvent(new Event('submit'));
    resolve([]);
    await Promise.resolve();
    assert.strictEqual(getTextEntries(suggestionList).length, 0);
});

test('search button', async () => {

    const searchTerm = 'Walk On By';

    const id0 = '0xdeadbeef';
    const title0 = 'Walk On By - Dionne Warwick';
    const duration0 = '2:34';

    const id1 = 'abc123'
    const title1 = 'Walk On By - The Stranglers';
    const duration1 = '6:44';

    const searchResults = [
        { id: id0, title: title0, duration: duration0 },
        { id: id1, title: title1, duration: duration1 },
    ];

    const resolve = service.addSearchTransaction(searchTerm);

    searchBox.value = searchTerm;
    searchForm.dispatchEvent(new Event('submit'));

    resolve(searchResults);
    await Promise.resolve();

    assert.deepStrictEqual(getIdDataEntries(resultList), [id0, id1]);
    assert.deepStrictEqual(getTitleAndDurationEntries(resultList), [
        { title: title0, duration: duration0 },
        { title: title1, duration: duration1 },
    ]);
});

test('stale results ignored', async () => {

    const searchTerm = 'Walk On By';

    const id0 = '0xdeadbeef';
    const title0 = 'Walk On By - Dionne Warwick';
    const duration0 = '2:34';

    const id1 = 'abc123'
    const title1 = 'Walk On By - The Stranglers';
    const duration1 = '6:44';

    const searchResults = [
        { id: id0, title: title0, duration: duration0 },
        { id: id1, title: title1, duration: duration1 },
    ];

    const searchTerm_a = 'Hurdy Gurdy';

    const id0_a = 'qwert';
    const title0_a = 'Hurdy Gurdy Man - Donovan';
    const duration0_a = '4:00';

    const id1_a = 'foo123'
    const title1_a = 'Hurdy Gurdy Man - Butthole Surfers';
    const duration1_a = '3:22';

    const searchResults_a = [
        { id: id0_a, title: title0_a, duration: duration0_a },
        { id: id1_a, title: title1_a, duration: duration1_a },
    ];

    const resolve = service.addSearchTransaction(searchTerm);
    const resolve_a = service.addSearchTransaction(searchTerm_a);

    searchBox.value = searchTerm;
    searchForm.dispatchEvent(new Event('submit'));

    searchBox.value = searchTerm_a;
    searchForm.dispatchEvent(new Event('submit'));

    // resolve out of order
    resolve_a(searchResults_a);
    resolve(searchResults);
    await Promise.resolve();

    // the older one is ignored
    assert.deepStrictEqual(getIdDataEntries(resultList), [id0_a, id1_a]);
    assert.deepStrictEqual(getTitleAndDurationEntries(resultList), [
        { title: title0_a, duration: duration0_a },
        { title: title1_a, duration: duration1_a },
    ]);
});

test('ignore search of empty term', () => {

    searchBox.value = ' ';
    searchForm.dispatchEvent(new Event('submit'));
});

test('click on autocomplete suggestion', async () => {

    searchBox.value = 'ignore me';

    suggestionList.innerHTML = `
        <li>foo</li>
        <li>bar</li>
        <li>baz</li>`;

    const id0 = '0xdeadbeef';
    const title0 = 'Bargain Booze advert';
    const duration0 = '2:34';

    const id1 = 'abc123'
    const title1 = 'Barry Chuckle tribute';
    const duration1 = '6:44';

    const searchResults = [
        { id: id0, title: title0, duration: duration0 },
        { id: id1, title: title1, duration: duration1 },
    ];

    const resolve = service.addSearchTransaction('bar');
    const target = suggestionList.children[1]; // 'bar' item
    target.dispatchEvent(new Event('click', { bubbles: true }));
    resolve(searchResults);

    await Promise.resolve();

    // 1. put the selected suggestion in the search box
    assert.strictEqual(searchBox.value, 'bar');

    // 2. clear the suggestions
    assert.strictEqual(getTextEntries(suggestionList).length, 0);

    // 3. do the search
    assert.deepStrictEqual(getIdDataEntries(resultList), [id0, id1]);
    assert.deepStrictEqual(getTitleAndDurationEntries(resultList), [
        { title: title0, duration: duration0 },
        { title: title1, duration: duration1 },
    ]);
});
