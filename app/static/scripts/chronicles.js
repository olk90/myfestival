Dropzone.options.chronicleUpload = {
    clickable: true,
    dictDefaultMessage: getDefaultMessage(),
    init: function () {
        this.on('complete', function () {
            location.reload();
        });
    }
}

function getDefaultMessage() {
    let hint = document.getElementById('hint')
    return hint.getAttribute('value')
}

function copyMarkdownPath(fileName) {
    navigator.clipboard.writeText(getMarkdownLink(fileName)).then(() => {
    })
}

function getMarkdownLink(fileName) {
    let festival = document.getElementById('festival')
    let f_id = festival.getAttribute('value')
    let user = document.getElementById('user')
    let u_id = user.getAttribute('value')
    return `![${fileName}](/static/chronicles/${f_id}/${u_id}/${fileName})`
}
