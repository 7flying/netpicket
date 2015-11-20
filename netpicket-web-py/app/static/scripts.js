function initSSE() {
    var source = new EventSource("/stream/");
    source.onmessage = function(msg) {
        window.console.log(msg);
        var target = document.getElementById("timeline-updates");
        if (target != null) {
            target.innerHTML = "<dt>" + msg.data + "</dt>";
        }
    }
}
