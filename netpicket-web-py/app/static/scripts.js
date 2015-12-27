
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

function changeClassButtonIcon() {
    if ($('#icon-collapse-pa').hasClass('fa-plus-square')) {
        $('#icon-collapse-pa').removeClass(
            "fa-plus-square").addClass("fa-minus-square");
    } else {
        if($('#icon-collapse-pa').hasClass('fa-minus-square')) {
            $('#icon-collapse-pa').removeClass(
                "fa-minus-square").addClass("fa-plus-square");
        }
    }
}

function deleteNetwork(netId) {
    $.ajax({
        type: 'DELETE',
        url: '/dashboard/networks/' + netId,
        success: function(data) {
            $('#net-' + netId).remove();
        },
        error: function(data) {
        }
    }); 
}

/*********
 * Stats *
 *********/

function updateStats(days, nets, nids, tday, nday, tweek, nweek) {
    /*@brand-info:    #5bc0de;
      @brand-warning: #f0ad4e;
      @brand-danger:  #d9534f;
    */
    window.console.log(nweek);
    window.console.log(nids);
    window.console.log(nets);
    
    var colors = {'R': '#d9534f', 'O': '#f0ad4e', 'B': '#5bc0de'};
    var labels = {'R': 'Alert', 'O': 'Warning', 'B': 'Info'};
    var event_types = ['R', 'O', 'B'];
    // Weekly events by type
    var data_tweek = [];
    for (var i = 0; i < event_types.length; i++) {
        data_tweek.push({value: tweek[event_types[i]],
                         color: colors[event_types[i]],
                         highlight: colors[event_types[i]],
                         label: labels[event_types[i]]});
    }
    var tweek_context = document.getElementById('can-tweek').getContext('2d');
    var options = { legendTemplate :
                    "<ul class=\"<%=name.toLowerCase()%>-legend\"><% for (var i=0; i<segments.length; i++){%><li><span style=\"background-color:<%=segments[i].fillColor%>\"></span><%if(segments[i].label){%><%=segments[i].label%><%}%></li><%}%></ul>"};
    var tweek_chart = new Chart(tweek_context).Doughnut(data_tweek, options);
    document.getElementById('tweek-legend').innerHTML = tweek_chart.generateLegend();
    document.getElementById('loading-tweek').style.display = "none";
    // Weekly events by network
    var netcolors = {1: '#0C7367', 2: '#0C1873', 3: '#670C73', 4: '#18E2CB',
                     5: '#12AB99', 6: '#AB1224', 7: '#E2182F', 8: '#340C73',
                     9: '#73340C', 0: '#73670C'};
    var upTo = nids.length;
    if (nids.length > 10)
        upTo = 10;
    var data_nweek = [];
    for (var i = 0; i < upTo; i++) {
        data_nweek.push({value: nweek[nids[i]],
                         color: netcolors[i],
                         highlight: netcolors[i],
                         label: nets[nids[i]]});
    }
    var nweek_context = document.getElementById('can-nweek').getContext('2d');
    var nweek_chart = new Chart(nweek_context).Doughnut(data_nweek, options);
    document.getElementById('nweek-legend').innerHTML = nweek_chart.generateLegend();
    document.getElementById('loading-nweek').style.display = "none";
    // Daily events by type
    var optionsLine = {legendTemplate : "<ul class=\"<%=name.toLowerCase()%>-legend\"><% for (var i=0; i<datasets.length; i++){%><li><span style=\"background-color:<%=datasets[i].strokeColor%>\"></span><%if(datasets[i].label){%><%=datasets[i].label%><%}%></li><%}%></ul>"};
    var data_tday = { labels: days, datasets: []};
    var temp_tday = {};
    for (var i = 0; i < event_types.length; i++) {
        temp_tday[event_types[i]] = {label: labels[event_types[i]],
                                     fillColor: colors[event_types[i]],
                                     strokeColor: colors[event_types[i]],
                                     pointColor: colors[event_types[i]],
                                     pointStrokeColor: "#fff",
                                     pointHighlightFill: "#fff",
                                     pointHighlightStroke: colors[event_types[i]],
                                     data: []};
    }
    window.console.log(tday);
    for (var i = 0; i < days.length; i++) {
        for (var j = 0; j < event_types.length; j++) {
            temp_tday[event_types[j]].data.push(tday[days[i]][event_types[j]]);
        }
    }
    data_tday.datasets.push(temp_tday);
    var tday_context = document.getElementById('can-tday').getContext('2d');
    var tday_chart = new Chart(tday_context).Line(data_tday, optionsLine);
    document.getElementById('loading-tday').style.display = "none";
    
}

function getStats() {
    var days = nets = nids = type_day = net_day = type_week = net_week = 0;
    $.get('/checkstats', function(res) {
        if (res.status === 200) {
            window.console.log(res);
            days = res.days;
            nets = res.nets;
            nids = res.net_ids;
            type_day = res.type_day;
            type_week = res.type_week;
            net_day = res.net_day;
            net_week = res.net_week;
            updateStats(days, nets, nids, type_day, net_day, type_week, net_week);
        }
    });
}

$(document).ready(function() {
    if (window.location.href.indexOf('dashboard') > -1) {
        // if (document.getElementById('updated-ago') != null)
        //     timelineSSE();
        if (window.location.href.indexOf('stats') > -1) {
            getStats();
        }
    }
    
    $('#button-add-entry').on('click', function() {
        changeClassButtonIcon(); 
    });
    $('#button-add-net').on('click', function() {
        changeClassButtonIcon(); 
    });
    
    if (document.getElementById('neterrors') != null) {
        $("#button-add-net").click();
    }
    if (document.getElementById('entryerrors') != null) {
        $("#button-add-entry").click();
    }
    $("[rel='tooltip']").tooltip();
    $('.selectpicker').selectpicker();
});
