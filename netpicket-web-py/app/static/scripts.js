
function saveTimelineEventStorage(id, dt, dd) {
    // <dt id="20151122">Sun 22 Nov</dt>
    // <dd id="20151122-dd"> ....</dd>
    // override old value
    sessionStorage['netpicket-' + id ] = JSON.stringify({'dt': dt.to, 'dd': dd});
    // set timeline ordering
    var netOrder = sessionStorage['netpicket-order'];
    if (typeof netOrder === 'undefined') {
        sessionStorage['netpicket-order'] = JSON.stringify({'order' : []});
    }
    var j = JSON.parse(netOrder);
    if (j.order.indexOf(id) == -1)
        j.order.push(id);
    sessionStorage['netpicket-order'] = JSON.stringify(j);
}

function loadTimeline() {
    var timeorder = sessionStorage['netpicket-order'];
    if (typeof timeorder !== 'undefined') {
        var j = JSON.parse(timeorder);
        for (var id in j) {
            var dtdd = sessionStorage['netpicket-' + id];
            if (typeof dtdd !== 'undefined') {
                var dl = document.getElementById("timeline-updates");
                dl.innerHTML = dtdd.dd + dl.innerHTML;
                dl.innerHTML = dtdd.dt + dl.innerHTML;
            }
        }
    }
}

/* SSE for the timeline in the dashboard. */
function timelineSSE() {
    var source = new EventSource("/timeline/");
    source.onmessage = function(msg) {
        var data = JSON.parse(msg.data);
        if (typeof data.date !== 'undefined') {
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
                var tableini = "<dt id=\"" + data.date + "\">" + data.day + "</dt>";
                tableini += ("<dd id=\"" + data.date +"-dd\"><table class=\"table\"><tbody id=\""
                             + data.date + "-table" + "\">");
                tableini += row;
                tableini += "</tbody></table></dd>";
                var dl = document.getElementById("timeline-updates");
                dl.innerHTML = tableini + dl.innerHTML;
            }
            document.getElementById("updated-ago").innerHTML = (data.date + " "
                                                                + data.time);
        }
    }
}

$(document).ready(function() {
    if (window.location.href.indexOf('dashboard') > -1) {
        // if (document.getElementById('updated-ago') != null)
        //     timelineSSE();
    }
    
    $('#button-add-net').on('click', function() {
        if ($('#icon-collapse-pa').hasClass('fa-plus-square')) {
            $('#icon-collapse-pa').removeClass(
                "fa-plus-square").addClass("fa-minus-square");
        } else {
            if($('#icon-collapse-pa').hasClass('fa-minus-square')) {
                $('#icon-collapse-pa').removeClass(
                    "fa-minus-square").addClass("fa-plus-square");
            }
        } 
    });
    if (document.getElementById('neterrors') != null) {
        $("#button-add-net").click();
    }
    $("[rel='tooltip']").tooltip();
});
