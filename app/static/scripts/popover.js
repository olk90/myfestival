var POPOVER = POPOVER || (function () {

    var _args = {};

    return {
        init: function (Args) {
            _args = Args;
        },
        getPopover: function () {
            let element = $(`${_args[0]}`)
            element.popover({
                html: true,
                content: buildPopoverContent(_args[0])
            })
        }
    }
}())

function buildPopoverContent(filename) {
    let copy = document.getElementById('copyLabel')
    let copyLabel = copy.getAttribute('value')
    let del = document.getElementById('deleteLabel')
    let deleteLabel = del.getAttribute('value')
    return [
        `<div><a onclick="copyMarkdownPath('${filename}')" href="#">${copyLabel}</a></div>`,
        `<div><a href="#">${deleteLabel}</a></div>`
    ].join('')
}
