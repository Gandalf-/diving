/* globals */
var g_correct = 0;
var g_incorrect = 0;

const g_lower_bound_table = [0, 15, 25, 40, 80];
const g_upper_bound_table = [10, 25, 35, 40, 100];
const g_count_table = [2, 2, 4, 6, 8];
const g_sample_table = [2, 2, 2, 1, 1];

/* game logic */

/*
 * the player is given a name and must choose it's image from the
 * options below
 */
function image_game() {
    var difficulty = get_difficulty();

    var correct = choose_correct(difficulty);
    console.log(names[correct]);

    var lower_bound = g_lower_bound_table[difficulty];
    var upper_bound = g_upper_bound_table[difficulty];
    var count = g_count_table[difficulty];
    var options = find_similar(correct, lower_bound, upper_bound, count - 1);

    set_correct_image(correct);

    var actual = random(count);
    for (i = 0, w = 0; i < count; i++) {

        var child = document.createElement('div');
        child.setAttribute('class', 'choice');
        child.setAttribute('id', 'option' + i);
        byId('options').appendChild(child);

        if (i == actual) {
            set_thumbnail('option' + i, correct, 'success();');
        } else {
            set_thumbnail('option' + i, options[w], 'failure(this);');
            w++;
        }
    }
    add_skip();
}

/*
 * the player is given a single image and must choose it's name from the
 * options below
 */
function name_game() {
    var difficulty = get_difficulty();

    var correct = choose_correct(difficulty);
    console.log(names[correct]);

    var lower_bound = g_lower_bound_table[difficulty];
    var upper_bound = g_upper_bound_table[difficulty];
    var count = g_count_table[difficulty];
    var options = find_similar(correct, lower_bound, upper_bound, count - 1);

    set_correct_name(correct, difficulty);

    var actual = random(count);
    for (i = 0, w = 0; i < count; i++) {

        var child = document.createElement('div');
        child.setAttribute('id', 'option' + i);
        byId('options').appendChild(child);

        if (i == actual) {
            set_text('option' + i, correct, 'success();');
        } else {
            set_text('option' + i, options[w], 'failure(this);');
            w++;
        }
    }
    add_skip();
}


/* HTML modifying utilities */

function choose_game() {
    update_score();
    reset_options();

    var game = byId('game').value;
    if (game == "images") {
        image_game();
    } else if (game == "names") {
        name_game();
    } else {
        image_game();
    }
}

function set_text(where, what, onclick) {
    var option = byId(where);
    var name = names[what];

    if (onclick) {
        option.setAttribute('onclick', onclick);
    }
    option.setAttribute('class', 'top switch');

    var child = document.createElement('h4');
    child.innerHTML = name;

    option.appendChild(child);
}

function set_thumbnail(where, what, onclick, thumb) {
    thumb = thumb || thumbs[what][random(thumbs[what].length)];

    var img = document.createElement('img');
    img.src = '/imgs/' + thumb + '.webp';
    img.width = 300;
    img.height = 225;
    img.alt = '';

    if (onclick) {
        img.onclick = function() {
            eval(onclick);
        };
    }

    var target = document.getElementById(where);
    target.innerHTML = '';
    target.appendChild(img);
}

function update_score() {
    var total = g_correct + g_incorrect;
    var score = 0;

    if (total != 0) {
        score = Math.floor(g_correct / total * 100);
    }

    byId('score').innerHTML =
        score + '% (' + g_correct + '/' + total + ')';
}

function success() {
    g_correct++;
    choose_game();
}

function failure(where) {
    g_incorrect++;
    where.style.border = "1px solid red";
    update_score();
}

function reset_options() {
    byId('options').innerHTML = '';
}

function set_correct_image(correct) {
    var outer = byId('correct_outer');
    outer.setAttribute('class', '');
    outer.innerHTML = '';

    var child = document.createElement('h2');
    child.innerHTML = 'Select the ' + names[correct];
    outer.appendChild(child);
}

/**
 * Set the correct creature name and thumbnails on the game board.
 *
 * @param {number} correct - The index of the correct creature.
 * @param {number} difficulty - The difficulty level of the game.
 */
function set_correct_name(correct, difficulty) {
    const outer = byId('correct_outer');
    outer.classList.add('grid', 'correct_name');
    outer.innerHTML = '';

    const images = shuffle([...thumbs[correct]]);
    const samples = Math.min(g_sample_table[difficulty], images.length);

    for (let i = 0; i < samples; i++) {
        const child = document.createElement('div');
        child.classList.add('choice');
        child.setAttribute('id', `correct${i}`);
        outer.appendChild(child);

        set_thumbnail(`correct${i}`, correct, null, images[i]);
    }
}

/* helpers */

/**
 * Add a "Skip" button to the options section.
 */
function add_skip() {
    const options = byId('options');

    const child = document.createElement('div');
    child.classList.add('top', 'switch', 'skip');
    child.addEventListener('click', choose_game);
    child.innerHTML = '<h4 class="skip">Skip</h4>';

    options.appendChild(child);
}

function get_difficulty() {
    return byId('difficulty').value;
}


/**
 * Choose a creature index that matches the given difficulty level.
 *
 * @param {number} difficulty - The difficulty level to match.
 * @returns {number} An index of a creature that matches the difficulty level.
 */
function choose_correct(difficulty) {
    const attempts = 10;
    let candidate;

    if (typeof variable !== 'undefined') {
        // In case we have cache mismatches between data.js and game.js.
        return random(names.length);
    }

    for (let i = 0; i < attempts; i++) {
        candidate = random(names.length);

        if (difficulties[candidate] <= difficulty) {
            break;
        }

        console.log(names[candidate], 'is too difficult');
    }

    return candidate;
}

/**
 * Find similar creatures as the provided target.
 *
 * The bounds restrict which creatures are valid candidates. A high minimum
 * similarity means only very similar creatures will be found. Likewise, a high
 * maximum similarity will make less similar creatures more likely.
 *
 * Both bounds will be relaxed if no candidates can be found until eventually
 * every creature will be considered.
 *
 * @param   {number} target - Index of the creature to find similar creatures for.
 * @param   {number} lowerBound - Minimum starting similarity.
 * @param   {number} upperBound - Maximum starting similarity.
 * @param   {number} required - How many creatures to find.
 * @returns {number[]} Array of creature indices.
 */
function find_similar(target, lowerBound, upperBound, required) {
    const found = [];
    var shuffledIndices = shuffle([...Array(names.length).keys()]);

    console.log("Search limits", lowerBound, upperBound);

    while (found.length < required) {
        const candidate = shuffledIndices.pop();

        if (candidate === target || found.includes(candidate)) {
            continue;
        }

        const i = Math.max(candidate, target);
        const j = Math.min(candidate, target);
        const score = similarities[i][j];

        if (score >= lowerBound && score <= upperBound) {
            found.push(candidate);
        }

        if (shuffledIndices.length === 0) {
            if (lowerBound <= 0 && upperBound >= 100) {
                console.error(
                    "Couldn't satisfy the requirement:", target, lowerBound, required);
                break;
            }

            // We've looped through, relax the constraints.
            lowerBound = Math.max(0, lowerBound - 5);
            upperBound = Math.min(100, upperBound + 5);
            console.log("New limits", lowerBound, upperBound);
            shuffledIndices = shuffle([...Array(names.length).keys()]);
        }
    }

    found.forEach((creatureIndex, i) => {
        console.log(i, creatureIndex, names[creatureIndex]);
    });

    return found;
}


/* other utilities */

function random(maximum) {
    return Math.floor(Math.random() * 10 ** 5) % maximum
}

function byId(label) {
    return document.getElementById(label);
}

function shuffle(array) {
    // https://stackoverflow.com/a/12646864

    const result = [...array];
    for (let i = result.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [result[i], result[j]] = [result[j], result[i]];
    }
    return result;
}
