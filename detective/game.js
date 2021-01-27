/* globals */
var correct = 0;
var incorrect = 0;

/* game logic */

function choose_correct()
{
    return random(names.length);
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

function image_game()
{
    var correct = choose_correct();
    console.log(names[correct]);
}

function name_game()
{
}

/* helpers */

function score()
{
    var total = correct + incorrect;
    if (total == 0) {
        return 0;
    }
    return correct / total;
}

function difficulty()
{
    const labels = [
        "very easy",
        "easy",
        "moderate",
        "hard",
        "very hard",
    ];
    var value = parseInt(byId('difficulty').value);
    return labels[value];
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
