const splits = ['fish', 'coral', 'ray', 'chiton', 'snail', 'worm'];
const where = document.title.toLowerCase();
const pages = {
    'gallery': gallery_pages,
    'taxonomy': taxonomy_pages,
    'sites': sites_pages,
}[where];

const CHAR_LIMIT = 100;
var previous_stack = [];

const SEARCH_RESULTS = document.getElementById('search_results');
const SEARCH_BAR = document.getElementById('search_bar');


function expandWords(words) {
    var result = [];

    for (let word of words) {
        let found = false;
        for (let split of splits) {
            if (word.includes(split)) {

                let splitIndex = word.indexOf(split);
                let preSplit = word.slice(0, splitIndex);
                let postSplit = word.slice(splitIndex);

                if (preSplit !== '') result.push(preSplit);
                result.push(postSplit);

                found = true;
                break;
            }
        }

        // if word didn't contain any split words, keep it as is
        if (!found) {
            result.push(word);
        }
    }

    return result;
}

function shortenName(name) {
    if (where != 'taxonomy') {
        return name;
    }

    const words = name.split(' ');
    if (words.length > 4) {
        // Take the last 2 words
        return words.slice(-2).join(' ');
    }

    return name;
}

function search_inner(text, skip = 0) {
    const words = expandWords(text.replace("'", '').split(' '));

    var results = [];
    for (let i = 0; i < pages.length; i++) {
        const candidate = pages[i];
        let match = true;

        for (let j = 0; j < words.length; j++) {
            if (!candidate.toLowerCase().includes(words[j])) {
                match = false;
                break;
            }
        }

        if (!match) {
            continue;
        }

        const exact = candidate === text;
        results.push([candidate, exact]);
    }

    // sort results based on 'exact' first and then length of candidate
    results.sort(function (a, b) {
        // sort by exactness
        if (a[1] === b[1]) {
            // if exactness is same, sort by length
            return a[0].length - b[0].length;
        }
        // exact results come first
        return b[1] - a[1];
    });

    // skip `skip` number of results
    results = results.slice(skip);

    // Take 100 characters worth of results
    var truncated = false;
    var char_count = 0;
    var topResults = [];

    for (let result of results) {
        const name = shortenName(result[0]);

        if (char_count + name.length > CHAR_LIMIT) {
            truncated = true;
            break;
        }

        char_count += name.length;
        topResults.push([name, pageToUrl(result[0])]);
    }

    return [topResults, truncated];
}

function createResult(name) {
    const div = document.createElement('div')
    div.classList.add('search_result');

    const desc = document.createElement('h3');
    desc.innerHTML = name;
    div.appendChild(desc);

    return div;
}

function addNoResult() {
    const nothing = createResult('No results');
    SEARCH_RESULTS.appendChild(nothing);
}

function addPreviousResult() {
    const back = createResult('Back')
    back.onclick = function () {
        let lastLocation = previous_stack.pop();
        searcher(lastLocation);
    };
    back.classList.add('search_scroll');
    SEARCH_RESULTS.appendChild(back);
}

function addNextResult(skip, results_length) {
    const more = createResult('More');
    more.onclick = function () {
        previous_stack.push(skip);
        searcher(skip + results_length);
    };
    more.classList.add('search_scroll');
    SEARCH_RESULTS.appendChild(more);
}

function searcher(skip = 0) {
    console.log(where);

    SEARCH_RESULTS.innerHTML = '';
    SEARCH_RESULTS.classList.remove('have_results');
    const text = SEARCH_BAR.value.toLowerCase();
    if (text.length === 0) {
        return;
    }

    const [results, truncated] = search_inner(text, skip);
    console.log('search found', results, truncated);

    if (results.length === 0) {
        addNoResult();
        return;
    }

    SEARCH_RESULTS.classList.add('have_results');
    if (previous_stack.length > 0) {
        addPreviousResult();
    }

    for (let [name, url] of results) {
        const link = document.createElement('a')
        link.classList.add('search_result');
        link.classList.add(where);
        link.title = name;
        link.href = url;

        const desc = document.createElement('h3');
        desc.innerHTML = toTitleCase(name);
        link.appendChild(desc);

        SEARCH_RESULTS.appendChild(link);
    }

    if (truncated) {
        addNextResult(skip, results.length);
    }
}

function randomPage() {
    const index = Math.floor(Math.random() * pages.length);
    const page = pages[index];
    window.location.href = pageToUrl(page);
}

function pageToUrl(page) {
    const url = page.replace(/ /g, '-');
    return `/${where}/${url}.html`;
}

function toTitleCase(str) {
    if (where != 'gallery') {
        return str;
    }

    // https://stackoverflow.com/a/196991
    return str.replace(
        /\w\S*/g,
        function (txt) {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        }
    );
}

function randomSearchPlaceholder() {
    const index = Math.floor(Math.random() * pages.length);
    const name = toTitleCase(shortenName(pages[index]));
    SEARCH_BAR.placeholder = `${name}...`;
}

randomSearchPlaceholder();
