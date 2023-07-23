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
    document.getElementById('search_results').innerHTML = '';

    const text = document.getElementById('search').value.toLowerCase();
    if (text.length === 0) {
        return;
    }

    const [results, truncated] = searcher(text, skip);
    console.log(results, truncated);

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

function toTitleCase(str) {
    // https://stackoverflow.com/a/196991
    return str.replace(
        /\w\S*/g,
        function (txt) {
            return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
        }
    );
}

function randomGallerySearchPlaceholder() {
    const index = Math.floor(Math.random() * gallery_pages.length);
    const name = gallery_pages[index];

    var search = document.getElementById('search');
    if (search != null) {
        search.placeholder = toTitleCase(name) + "...";
    }
}
