Dropzone.options.chronicleUpload = {
    clickable: true,
    dictDefaultMessage: getDefaultMessage(),
    init: function () {
        this.on("complete", function () {
            location.reload()
        });
    }
}

function getDefaultMessage() {
    let hint = document.getElementById("hint")
    return hint.getAttribute("value")
}

function deleteImage(fileName) {
    let festival = document.getElementById("festival")
    let f_id = festival.getAttribute("value")
    let user = document.getElementById("user")
    let u_id = user.getAttribute("value")

    // POST
    fetch("/chronicle/delete_image", {
        // Declare what type of data we're sending
        headers: {
            "Content-Type": "application/json"
        },
        // Specify the method
        method: "POST",

        body: JSON.stringify({
            "fileName": fileName,
            "festival": f_id,
            "user": u_id
        })
    })
        .then(function (response) {
            return response.text();
        })
        .then(function (text) {
            location.reload()
            console.log("POST response: ")
            // Should be "OK" if everything was successful
            console.log(text)
        });
}

function copyMarkdownPath(fileName) {
    navigator.clipboard.writeText(getMarkdownLink(fileName)).then(() => {
    })
}

function getMarkdownLink(fileName) {
    let festival = document.getElementById("festival")
    let f_id = festival.getAttribute("value")
    let user = document.getElementById("user")
    let u_id = user.getAttribute("value")

    // direct markdown link (no scaling possible, so go with img tag)
    // return `![${fileName}](/static/chronicles/${f_id}/${u_id}/${fileName})`

    let path = `${f_id}/${u_id}/${fileName}`
    let style = `"max-width: 90%; display: block; margin-left: auto; margin-right: auto;"`
    return `<img alt="${fileName}" src="/static/chronicles/${path}" style=${style}>`
}
