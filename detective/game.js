/* globals */
var correct = 0;
var incorrect = 0;

/* game logic */

function choose_correct()
{
    return random(names.length);
}

function success()
{
    correct++;
    choose_game();
}

function failure(where)
{
    incorrect++;
    where.style.border = "1px solid red";
    update_score();
}

function choose_game()
{
    update_score();
    reset_thumbnails();
    image_game();
}

function set_thumbnail(where, what, correct)
{
    var thumb = thumbs[what][random(thumbs[what].length)];
    var html = '<img src="/imgs/' + thumb + '.jpg" alt=""';

    if (correct) {
        html += 'onclick="success();"'
    } else {
        html += 'onclick="failure(this);"'
    }
    html += '>';

    byId(where).innerHTML = html;
}

function find_similar(target, limit, required)
{
    var start = random(names.length);
    var index = start;
    var found = [];

    while (found.length < required) {

        var valid = true;
        valid &= index != target;
        valid &= !found.includes(index);

        if (valid) {
            var i = Math.max(index, target);
            var j = Math.min(index, target);
            score = similarities[i][j];

            if (score >= limit) {
                found.push(index);
            }
        }

        index = (index + 1) % names.length;
        if (index == start) {
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

function reset_thumbnails()
{
    byId('thumbnails').innerHTML = '';
}

function image_game()
{
    var correct = choose_correct();
    console.log(names[correct]);

    var difficulty = get_difficulty();
    var limit_table = [0, 15, 30, 40, 80];
    var count_table = [2, 2, 4, 6, 8];

    var limit = limit_table[difficulty];
    var count = count_table[difficulty];
    var options = find_similar(correct, limit, count - 1);

    byId('correct').innerHTML = 'Select the ' + names[correct];
    var actual = random(count - 1);

    for (i = 0, w = 0; i < count; i++) {

        var child = document.createElement('div');
        child.setAttribute('class', 'image');
        child.setAttribute('id', 'img' + i);
        byId('thumbnails').appendChild(child);

        if (i == actual) {
            set_thumbnail('img' + i, correct, true);
        } else {
            set_thumbnail('img' + i, options[w], false);
            w++;
        }
    }
}

function name_game()
{
}

/* helpers */

function update_score()
{
    var total = correct + incorrect;
    var score = 0;

    if (total != 0) {
        score = Math.floor(correct / total * 100);
    }

    byId('score').innerHTML =
        score + '% (' + correct + '/' + total + ')';
}

function get_difficulty()
{
    return parseInt(byId('difficulty').value);
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

/* utility */

function random(maximum)
{
    return Math.floor(Math.random() * 10 ** 5) % maximum
}

function byId(label)
{
    return document.getElementById(label);
}
