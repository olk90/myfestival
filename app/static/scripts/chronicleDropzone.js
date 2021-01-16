Dropzone.options.chronicleUpload = {
    clickable: true,
    addRemoveLinks: true,
    dictRemoveFileConfirmation: 'Sure Want To Delete',
    init: function () {
        this.on("success", function (file, responseText) {
            let filename = file.name;
            $('#form').append("<input type='hidden' data='" + filename + "' name='files[]' value='" + responseText + "'>");
        });
        this.on("complete", function (file) {
            let fileName = file.name
            let copyButton = document.createElement('input')
            copyButton.setAttribute('type', 'button')
            copyButton.style.textAlign = 'center'
            copyButton.value = 'Markdown'
            copyButton.onclick = function () {
                copyMarkdownPath(fileName)
            }
            file.previewTemplate.appendChild(copyButton)
        });
    }
}

function copyMarkdownPath(fileName) {
    navigator.clipboard.writeText(getMarkdownLink(fileName)).then(() => {
        alert('Text copied to clipboard');
    })
}

function getMarkdownLink(fileName) {
    let festival = document.getElementById('festival')
    let f_id = festival.getAttribute('value')
    let user = document.getElementById('user')
    let u_id = user.getAttribute('value')
    return `![${fileName}](/static/chronicles/${f_id}_${u_id}/${fileName})`
}