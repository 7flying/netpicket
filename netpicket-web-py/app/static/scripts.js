
/* SSE for the timeline in the dashboard. */
function timelineSSE() {
    var source = new EventSource("/timeline/");
    source.onmessage = function(msg) {
        var data = JSON.parse(msg.data);
        // {'date': 20151121, 'time': 20:24, 'day': 'Wed 14 Oct',
        // 'priority': 'G', 'text': 'Hello'}
        var hour = "<td>" + data.time + "</td>";
        var desc = "<td class=\"";
        switch(data.priority) {
        case 'G': // green
            desc += "text-success\"><i class=\"fa fa-smile-o\"></i> ";
            break;
        case 'O': // orange
            desc += "text-warning\"><i class=\"fa fa-exclamation-circle\"></i> ";
            break;
        case 'R': // red
            desc += "text-danger\"><i class=\"fa fa-warning\"></i> ";
            break;
        case 'B': // blue + default
            desc += "text-info\"><i class=\"fa fa-info-circle\"></i> ";
            break;
        default:
            desc += "text-info\"><i class=\"fa fa-info-circle\"></i> ";
        }
        desc += (data.text + "</td>");
        var row = "<tr>" + hour + desc + "</tr>";
        // check if it is the first event of the day
        var table = document.getElementById(data.date + '-table');
        if (table != null) {
            table.innerHTML = row + table.innerHTML;
        } else {
            var tableini = "<dt id=\"" + data.date + "\">" + data.day + "</dt>"
            tableini += ("<dd><table class=\"table\"><tbody id=\""
                         + data.date + "-table" + "\">");
            tableini += row;
            tableini += "</tbody></table></dd>";
            var dl = document.getElementById("timeline-updates");
            dl.innerHTML = tableini + dl.innerHTML;
        }
        document.getElementById("updated-ago").innerHTML = data.time;
    }
}
