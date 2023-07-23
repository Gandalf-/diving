const splits = ['fish', 'coral', 'ray', 'chiton', 'snail', 'worm'];

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
        if (!found) result.push(word);
    }

    return result;
}

function searcher(text, skip = 0) {
    const words = expandWords(text.split(' '));
    if (words.length === 0) {
        return [[], false];
    }

    var results = [];
    for (let i = 0; i < gallery_pages.length; i++) {
        const candidate = gallery_pages[i];
        var match = true;

        for (let j = 0; j < words.length; j++) {
            if (!candidate.includes(words[j])) {
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
        const name = result[0];
        if (char_count + name.length > char_limit) {
            truncated = true;
            break;
        }

        char_count += name.length;
        topResults.push(name);
    }

    return [topResults, truncated];
}

function gallerySearch(skip = 0) {
    const text = document.getElementById('search').value.toLowerCase();
    const [results, truncated] = searcher(text, skip);
    console.log(results, truncated);

    document.getElementById('search_results').innerHTML = '';
    if (results.length === 0) {
        const nothing = document.createElement('div')
        nothing.classList.add('search_result');

        const desc = document.createElement('h3');
        desc.innerHTML = 'No results';
        nothing.appendChild(desc);

        document.getElementById('search_results').appendChild(nothing);
        return;
    }

    for (let result of results) {
        const link = document.createElement('a')
        link.classList.add('search_result');
        link.classList.add('gallery');
        link.title = result;

        const url = result.replace(/ /g, '-');
        link.href = `/gallery/${url}.html`;

        const desc = document.createElement('h3');
        desc.innerHTML = result;
        link.appendChild(desc);

        document.getElementById('search_results').appendChild(link);
    }

    if (truncated) {
        const more = document.createElement('div')
        more.classList.add('search_result');
        more.onclick = function () {
            gallerySearch(skip + results.length);
        };

        const desc = document.createElement('h3');
        desc.innerHTML = 'More...';
        more.appendChild(desc);

        document.getElementById('search_results').appendChild(more);
    }
}
