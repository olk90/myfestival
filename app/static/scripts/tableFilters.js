function stockTableFilter() {
    input = document.getElementById("stockFilter");
    table = document.getElementById("stockTable");
    tableFilter(input, table, 1);
}

function wishlistTableFilter() {
    input = document.getElementById("wishlistFilter");
    table = document.getElementById("wishlistTable");
    tableFilter(input, table, 1);
}

function shoppingTableFilter() {
    input = document.getElementById("shoppingFilter");
    table = document.getElementById("shoppingTable");
    tableFilter(input, table, 1);
}

function utilityTableFilter() {
    input = document.getElementById("utilityFilter");
    table = document.getElementById("utilityTable");
    tableFilter(input, table, 1);
}

function replyTableFilter(postId) {
    table = document.getElementById("replyTable" + postId);
    var tr, i;
    tr = table.getElementsByTagName("tr");
    for (i = 0; i < tr.length; i++) {
        if (document.getElementById("showReplies" + postId).checked) {
            tr[i].style.display = "";
        } else {
            tr[i].style.display = "none";
        }
    }
}

function tableFilter(input, table, cellIndex) {
    // Declare variables
    var input, filter, table, tr, td, i, txtValue;
    filter = input.value.toUpperCase();
    tr = table.getElementsByTagName("tr");

    // Loop through all table rows, and hide those who don't match the search query
    for (i = 0; i < tr.length; i++) {
        td = tr[i].getElementsByTagName("td")[cellIndex];
        if (td) {
            txtValue = td.textContent || td.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                tr[i].style.display = "";
            } else {
                tr[i].style.display = "none";
            }
        }
    }
}