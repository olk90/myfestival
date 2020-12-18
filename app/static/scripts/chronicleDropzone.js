Dropzone.options.chronicleUpload = {
    clickable: true,
    addRemoveLinks: true,
    dictRemoveFileConfirmation: 'Sure Want To Delete',
    init: function () {
        this.on("success", function (file, responseText) {
            var filename = file.name;
            $('#form').append("<input type='hidden' data='" + filename + "' name='files[]' value='" + responseText + "'>");
        });
        this.on("complete", function (file) {
            let fileName = file.name
            let copyButton = document.createElement('button')
            // copyButton.innerHTML = getMarkdownLink(fileName)
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
    return `![${fileName}](/static/chronicles/2_1/${fileName})`
}