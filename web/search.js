const splits = ['fish', 'coral', 'ray', 'chiton', 'snail', 'worm'];
const where = document.title.toLowerCase();
const pages = {
    'gallery': gallery_pages,
    'taxonomy': taxonomy_pages,
    'sites': sites_pages,
}[where];

var previous_stack = [];

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
        var match = true;

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
    const char_limit = 100;
    var truncated = false;
    var char_count = 0;
    var topResults = [];

    for (let result of results) {
        const name = shortenName(result[0]);

        if (char_count + name.length > char_limit) {
            truncated = true;
            break;
        }

        char_count += name.length;
        topResults.push([name, pageToUrl(result[0])]);
    }

    return [topResults, truncated];
}

function searcher(skip = 0) {
    console.log(where);

    document.getElementById('search_results').innerHTML = '';

    const text = document.getElementById('search_bar').value.toLowerCase();
    if (text.length === 0) {
        return;
    }

    const [results, truncated] = search_inner(text, skip);
    console.log('search found', results, truncated);

    if (results.length === 0) {
        const nothing = document.createElement('div')
        nothing.classList.add('search_result');

        const desc = document.createElement('h3');
        desc.innerHTML = 'No results';
        nothing.appendChild(desc);

        document.getElementById('search_results').appendChild(nothing);
        return;
    }

    if (previous_stack.length > 0) {
        const back = document.createElement('div')
        back.classList.add('search_result');

        back.onclick = function () {
            let lastLocation = previous_stack.pop();
            searcher(lastLocation);
        };

        const desc = document.createElement('h3');
        desc.innerHTML = 'Back...';
        back.appendChild(desc);

        document.getElementById('search_results').appendChild(back);
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

        document.getElementById('search_results').appendChild(link);
    }

    if (truncated) {
        const more = document.createElement('div')
        more.classList.add('search_result');

        more.onclick = function () {
            previous_stack.push(skip);
            searcher(skip + results.length);
        };

        const desc = document.createElement('h3');
        desc.innerHTML = 'More...';
        more.appendChild(desc);

        document.getElementById('search_results').appendChild(more);
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
    const name = shortenName(pages[index]);

    var search = document.getElementById('search_bar');
    if (search != null) {
        search.placeholder = toTitleCase(name) + "...";
    }
}
