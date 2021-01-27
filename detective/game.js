/* globals */
var g_correct = 0;
var g_incorrect = 0;

const g_limit_table = [0, 15, 30, 40, 80];
const g_count_table = [2, 2, 4, 6, 8];

/* game logic */

/*
 * the player is given a name and must choose it's image from the
 * options below
 */
function image_game()
{
    var correct = choose_correct();
    console.log(names[correct]);

    var difficulty = get_difficulty();
    var limit = g_limit_table[difficulty];
    var count = g_count_table[difficulty];
    var options = find_similar(correct, limit, count - 1);

    byId('correct_outer').setAttribute('class', '');
    byId('correct').setAttribute('class', '');
    byId('correct').innerHTML = 'Select the ' + names[correct];

    var actual = random(count);
    for (i = 0, w = 0; i < count; i++) {

        var child = document.createElement('div');
        child.setAttribute('class', 'image');
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
function name_game()
{
    var correct = choose_correct();
    console.log(names[correct]);

    var difficulty = get_difficulty();
    var limit = g_limit_table[difficulty];
    var count = g_count_table[difficulty];
    var options = find_similar(correct, limit, count - 1);

    byId('correct_outer').setAttribute('class', 'grid correct_name');
    byId('correct').setAttribute('class', 'image');
    set_thumbnail('correct', correct, null);

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

function choose_game()
{
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

function set_text(where, what, onclick)
{
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

function set_thumbnail(where, what, onclick)
{
    var thumb = thumbs[what][random(thumbs[what].length)];
    var html = '<img src="/imgs/' + thumb + '.jpg" alt=""';

    if (onclick) {
        html += 'onclick="' + onclick + '"';
    }
    html += '>';

    byId(where).innerHTML = html;
}

function update_score()
{
    var total = g_correct + g_incorrect;
    var score = 0;

    if (total != 0) {
        score = Math.floor(g_correct / total * 100);
    }

    byId('score').innerHTML =
        score + '% (' + g_correct + '/' + total + ')';
}

function update_difficulty()
{
    const labels = [
        "Very Easy",
        "Easy",
        "Moderate",
        "Hard",
        "Very Hard",
    ];
    byId("difficulty_label").innerHTML = labels[get_difficulty()];
}

function success()
{
    g_correct++;
    choose_game();
}

function failure(where)
{
    g_incorrect++;
    where.style.border = "1px solid red";
    update_score();
}

function reset_options()
{
    byId('options').innerHTML = '';
}


/* helpers */

function add_skip()
{
    var options = byId('options');

    var child = document.createElement('div');
    child.setAttribute('class', 'top switch skip');
    child.setAttribute('onclick', 'choose_game();');
    child.innerHTML = '<h4 class="skip">Skip</h4>';

    options.appendChild(child);
}

function get_difficulty()
{
    return parseInt(byId('difficulty').value);
}

function choose_correct()
{
    return random(names.length);
}

function find_similar(target, limit, required)
{
    var index = 0;
    var found = [];

    var indicies = [];
    for (i = 0; i < names.length; i++) {
        indicies[i] = i;
    }
    shuffle(indicies);

    while (found.length < required) {

        var candidate = indicies[index];
        var valid = true;
        valid &= candidate != target;
        valid &= !found.includes(candidate);

        if (valid) {

            var i = Math.max(candidate, target);
            var j = Math.min(candidate, target);
            score = similarities[i][j];

            if (score >= limit) {
                found.push(candidate);
            }
        }

        index = (index + 1) % names.length;
        if (index == 0) {
            if (limit < 0) {
                console.log(
                    "error: couldn't satisfy the requirement",
                    target, limit, required);
                break;
            }

            // we've looped through
            limit -= 10;
            console.log("new limit", limit);
        }
    }

    for (i = 0; i < found.length; i++) {
        console.log(i, found[i], names[found[i]]);
    }

    return found;
}


/* other utilities */

function random(maximum)
{
    return Math.floor(Math.random() * 10 ** 5) % maximum
}

function byId(label)
{
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
