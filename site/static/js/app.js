// Set up tab navigation
console.log('APP.JS LOADED');
const tabs = document.querySelectorAll('.tabs li');
const panels = [
    document.querySelector('#search-panel'),
    document.querySelector('#queue-panel')
];

tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('is-active'));
        tab.classList.add('is-active');

        panels.forEach((panel, j) => {
            panel.hidden = i !== j;
        });
    });
});

import SearchService from './searchService.js';
import SearchController from './searchController.js';

const searchService = new SearchService();
const searchController = new SearchController(document, searchService);
