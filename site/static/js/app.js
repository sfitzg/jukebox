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

// Set up events - TODO: service/controller/unit test
//const events = new EventSource('/events');

/*
events.addEventListener('queue-changed', (event) => {
    console.log('EVENT', event.data);
    const data = JSON.parse(event.data);
    console.log(data);
});
*/
/*
console.log('CREATING SSE');

events.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(data);
};

events.onopen = () => {
    console.log('SSE OPEN');
};

events.onerror = (event) => {
    console.log('SSE ERROR', event);
};

events.onmessage = (event) => {
    console.log('SSE MESSAGE', event.data);
};
*/
