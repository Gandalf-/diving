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
    if (!thumb) {
        thumb = thumbs[what][random(thumbs[what].length)];
    }
    var html = '<img src="/imgs/' + thumb + '.jpg" width=300 alt=""';

    if (onclick) {
        html += 'onclick="' + onclick + '"';
    }
    html += '>';

    byId(where).innerHTML = html;
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

function set_correct_name(correct, difficulty) {
    var outer = byId('correct_outer');
    outer.setAttribute('class', 'grid correct_name');
    outer.innerHTML = '';

    var images = thumbs[correct].slice();
    shuffle(images);

    var samples = g_sample_table[difficulty];
    samples = Math.min(samples, images.length);

    for (i = 0; i < samples; i++) {
        var child = document.createElement('div');
        child.setAttribute('class', 'choice');
        child.setAttribute('id', 'correct' + i);
        outer.appendChild(child);

        set_thumbnail('correct' + i, correct, null, images[i]);
    }
}


/* helpers */

function add_skip() {
    var options = byId('options');

    var child = document.createElement('div');
    child.setAttribute('class', 'top switch skip');
    child.setAttribute('onclick', 'choose_game();');
    child.innerHTML = '<h4 class="skip">Skip</h4>';

    options.appendChild(child);
}

function get_difficulty() {
    return byId('difficulty').value;
}

function choose_correct(difficulty) {
    const attempts = 10;
    var candidate = random(names.length);

    if (typeof variable !== 'undefined') {
        // in case we have cache mismatches between data.js and game.js
        return candidate;
    }

    for (i = 0; i < attempts; i++) {
        candidate = random(names.length);
        if (difficulties[candidate] <= difficulty) {
            break;
        }
        console.log(names[candidate], 'too difficult')
    }
    return candidate;
}

/**
 * Find similar creatures as the provided target
 *
 * The bounds restrict which creatures are valid candidates. A high minimum
 * simliarity means only very similar creatures will be found. Likewise, a high
 * maximum similiarity will make less similar creatures more likely
 *
 * Both bounds will be relaxed if no candidates can be found until eventually
 * every creature will be considered
 *
 * @param   target          index of the creature to find similar creatures for
 * @param   lower_bound     minimum starting similarity
 * @param   upper_bound     maximum starting similarity
 * @param   required        how many creatures to find
 * @returns                 array of creature indicies
 */
function find_similar(target, lower_bound, upper_bound, required) {
    var index = 0;
    var found = [];

    /* create a mirror of the names array; we shuffle the indices so we can
     * leave the actual names array alone
     */
    var indicies = [];
    for (i = 0; i < names.length; i++) {
        indicies[i] = i;
    }
    shuffle(indicies);
    console.log("search limits", lower_bound, upper_bound);

    while (found.length < required) {

        /* a candidate is valid if it's not what we're looking for and hasn't
         * already been chosen
         */
        var candidate = indicies[index];
        var valid = true;
        valid &= candidate != target;
        valid &= !found.includes(candidate);

        if (valid) {
            var i = Math.max(candidate, target);
            var j = Math.min(candidate, target);
            score = similarities[i][j];

            if (score >= lower_bound && score <= upper_bound) {
                found.push(candidate);
            }
        }

        index = (index + 1) % names.length;
        if (index == 0) {
            if (lower_bound <= 0 && upper_bound >= 100) {
                console.log(
                    "error: couldn't satisfy the requirement",
                    target, lower_bound, required);
                break;
            }

            // we've looped through, relax the constraints
            lower_bound = Math.max(0, lower_bound - 5);
            upper_bound = Math.min(100, upper_bound + 5);
            console.log("new limits", lower_bound, upper_bound);
        }
    }

    for (i = 0; i < found.length; i++) {
        console.log(i, found[i], names[found[i]]);
    }

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

    for (var i = array.length - 1; i > 0; i--) {
        var j = Math.floor(Math.random() * (i + 1));
        var temp = array[i];
        array[i] = array[j];
        array[j] = temp;
    }
}
