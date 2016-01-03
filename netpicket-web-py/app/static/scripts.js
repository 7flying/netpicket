
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
            desc += (data.text
                     + "</td><td><a href=\"/dashboard/networks/default#net-"
                     + data.netid + "\">" + data.netname + "</a></td>");
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

/***********
 * Deletes *
 ***********/

function deleteNetwork(netId) {
    $.ajax({
        type: 'DELETE',
        url: '/dashboard/networks/' + netId,
        success: function(data) {
            $('#net-' + netId).remove();
            var nets = document.getElementById(
                "accordion-nets").getElementsByTagName("div").length;
            if (nets === 0) {
                $("#div-accordion-hosts").remove();
                document.getElementById("display-no-nets").style.display = "";
            }
        },
        error: function(data) {
        }
    }); 
}

function deleteHost(hostId) {
    $.ajax({
        type: 'DELETE',
        url: '/dashboard/alerts/' + hostId,
        success: function(data) {
            $('#host-' + hostId).remove();
            var rows = document.getElementById(
                'table-hosts').getElementsByTagName(
                    "tbody")[0].getElementsByTagName("tr").length;
            if (rows === 0) {
                $("#div-table-hosts").remove();
                document.getElementById("display-no-hosts").style.display = "";
            }
        },
        error: function(data) {
        }
    }); 
}

function deleteEntry(entryId) {
    $.ajax({
        type: 'DELETE',
        url: '/dashboard/wblists/' + entryId,
        success: function(data) {
            $('#entry-' + entryId).remove();
            var rows = document.getElementById(
                'table-w-list');
            if (rows != null) {
                rows = rows.getElementsByTagName(
                    "tbody")[0].getElementsByTagName("tr").length;
            }
            if (rows != null && rows === 0) {
                $('#div-table-w').remove();
                document.getElementById('display-no-w-list').style.display = "";
            } else {
                var rows = document.getElementById(
                    'table-b-list');
                if (rows != null) {
                    rows = rows.getElementsByTagName(
                        "tbody")[0].getElementsByTagName("tr").length;
                }
                if (rows === 0) {
                    $('#div-table-b').remove();
                    document.getElementById('display-no-b-list').style.display = "";
                }
            }
        },
        error: function(data) {}
    })
}

/***********************************
 * API key generation and deletion *
 ***********************************/

function generateAPIKey(apiId) {
    $.ajax({
        type: 'POST',
        url: '/apikey/' + apiId,
        success: function(data) {
            if (data.status === 200)
                window.location.reload();
        },
        error: function(data) {
            
        }
    });
}

function deleteAPIKey(apiId) {
    $.ajax({
        type: 'DELETE',
        url: '/apikey/' + apiId,
        success: function(data) {
            if (data.status === 200)
                window.location.reload();
        }
    });
}

/*******************
 * Buoy management *
 *******************/

function stopBuoy(buoId) {
    $.ajax({
        type: 'PUT',
        url: '/buoy/' + buoId + '/stop',
        success: function(data) {
            if (data.status === 200)
                window.location.reload();
        }
    });
}

function launchBuoy(buoId) {
    $.ajax({
        type: 'PUT',
        url: '/buoy/' + buoId + '/launch',
        success: function(data) {
            if (data.status === 200)
                window.location.reload();
        }
    });
}

/*********
 * Stats *
 *********/

function updateStats(days, nets, nids, tday, nday, tweek, nweek) {
    var colors = {'R': '#d9534f', 'O': '#f0ad4e', 'B': '#5bc0de'};
    var colors_high = {'R': '#e7908e', 'O': '#f6ce95', 'B': '#9bd8eb'};
    var colors_rgb = {'R': 'rgba(217,83,79, ', 'O': 'rgba(240,173,78, ',
                      'B': 'rgba(91,192,222, '};
    var labels = {'R': 'Alert', 'O': 'Warning', 'B': 'Info'};
    var event_types = ['R', 'O', 'B'];
    // Weekly events by type
    var data_tweek = [];
    for (var i = 0; i < event_types.length; i++) {
        data_tweek.push({value: tweek[event_types[i]],
                         color: colors[event_types[i]],
                         highlight: colors_high[event_types[i]],
                         label: labels[event_types[i]]});
    }
    var tweek_context = document.getElementById('can-tweek').getContext('2d');
    var options = { legendTemplate :
                    "<ul class=\"<%=name.toLowerCase()%>-legend\"><% for (var i=0; i<segments.length; i++){%><li><span style=\"background-color:<%=segments[i].fillColor%>\"></span><%if(segments[i].label){%><%=segments[i].label%><%}%></li><%}%></ul>"};
    var tweek_chart = new Chart(tweek_context).Doughnut(data_tweek, options);
    document.getElementById('tweek-legend').innerHTML = tweek_chart.generateLegend();
    document.getElementById('loading-tweek').style.display = "none";
    // Weekly events by network
    var netcolors = {1: '#0C7367', 2: '#0C1873', 3: '#670C73', 4: '#042d28',
                     5: '#12AB99', 6: '#AB1224', 7: '#E2182F', 8: '#340C73',
                     9: '#73340C', 0: '#73670C'};
    var netcolors_high = {1: '#13b8a5', 2: '#1326b8', 3: '#a513b8', 4: '#0a7366',
                          5: '#22e8d0', 6: '#c21429', 7: '#ed596a', 8: '#5313b8',
                          9: '#b85313', 0: '#b8a513'};
    var netcolors_rgb = {1: 'rgba(12,115,103,', 2: 'rgba(12,24,115,',
                         3: 'rgba(103,12,115, ', 4: 'rgba(4,45,40, ',
                         5: 'rgba(18,71,153, ', 6: 'rgba(171,18,36, ',
                         7: 'rgba(226,24,47, ', 8: 'rgba(52,12,115, ',
                         9: 'rgba(115,52,12, ', 0: 'rgba(115,103,12, '};
    var upTo = nids.length;
    if (nids.length > 10)
        upTo = 10;
    var data_nweek = [];
    for (var i = 0; i < upTo; i++) {
        data_nweek.push({value: nweek[nids[i]],
                         color: netcolors[nids[i] % 10],
                         highlight: netcolors_high[nids[i] % 10],
                         label: nets[nids[i]]});
    }
    var nweek_context = document.getElementById('can-nweek').getContext('2d');
    var nweek_chart = new Chart(nweek_context).Doughnut(data_nweek, options);
    document.getElementById('nweek-legend').innerHTML = nweek_chart.generateLegend();
    document.getElementById('loading-nweek').style.display = "none";
    // Daily events by type (Bar + Line chart)
    var optionsLine = {legendTemplate : "<ul class=\"<%=name.toLowerCase()%>-legend\"><% for (var i=0; i<datasets.length; i++){%><li><span style=\"background-color:<%=datasets[i].strokeColor%>\"></span><%if(datasets[i].label){%><%=datasets[i].label%><%}%></li><%}%></ul>"};
    var data_tday_bar = { labels: days, datasets: []};
    var data_tday_line = { labels: days, datasets: []};
    var temp_tday_bar = {};
    var temp_tday_line = {};
    for (var i = 0; i < event_types.length; i++) {
        temp_tday_bar[event_types[i]] = {label: labels[event_types[i]],
                                         fillColor: colors_rgb[event_types[i]] + "0.7)",
                                         strokeColor: colors[event_types[i]],
                                         pointColor: colors[event_types[i]],
                                         pointStrokeColor: "#fff",
                                         pointHighlightFill: "#fff",
                                         pointHighlightStroke: colors[event_types[i]],
                                         data: []};
        temp_tday_line[event_types[i]] = {label: labels[event_types[i]],
                                          fillColor: colors_rgb[event_types[i]] + "0.2)",
                                          strokeColor: colors[event_types[i]],
                                          pointColor: colors[event_types[i]],
                                          pointStrokeColor: "#fff",
                                          pointHighlightFill: "#fff",
                                          pointHighlightStroke: colors[event_types[i]],
                                          data: []};
    }
    for (var i = 0; i < days.length; i++) {
        for (var j = 0; j < event_types.length; j++) {
            temp_tday_bar[event_types[j]].data.push(tday[days[i]][event_types[j]]);
            temp_tday_line[event_types[j]].data.push(tday[days[i]][event_types[j]]);
        }
    }
    for (var i = 0; i < event_types.length; i++) {
        data_tday_bar.datasets.push(temp_tday_bar[event_types[i]]);
        data_tday_line.datasets.push(temp_tday_line[event_types[i]]);
    }
    // Bar
    var tdaybar_context = document.getElementById('can-tday-bar').getContext('2d');
    var tdaybar_chart = new Chart(tdaybar_context).Bar(data_tday_bar, optionsLine);
    document.getElementById('loading-tday-bar').style.display = "none";
    // Line
    var tdayline_context = document.getElementById('can-tday-line').getContext('2d');
    var tdayline_chart = new Chart(tdayline_context).Line(data_tday_line, optionsLine);
    document.getElementById('loading-tday-line').style.display = "none";
    // Daily events by network
    var data_nday = { labels: days, datasets: []};
    var temp_nday = {};
    for (var i = 0; i < upTo; i++) {
        temp_nday[nids[i]] = {label: nets[nids[i]],
                              fillColor: netcolors_rgb[nids[i] % 10] + "0.7)",
                              strokeColor: netcolors[nids[i] % 10],
                              pointColor: netcolors[nids[i] % 10],
                              pointStrokeColor: "#fff",
                              pointHighlightFill: "#fff",
                              pointHighlightStroke: netcolors[nids[i] % 10],
                              data: []};
    }
    for (var i = 0; i < days.length; i++) {
        for (var j = 0; j < upTo; j++) {
            temp_nday[nids[j]].data.push(nday[days[i]][nids[j]]);
        }
    }
    for (var i = 0; i < upTo; i++) {
        data_nday.datasets.push(temp_nday[nids[i]]);
    }
    var nday_context = document.getElementById('can-nday').getContext('2d');
    var nday_chart = new Chart(nday_context).Bar(data_nday, optionsLine);
    document.getElementById('loading-nday').style.display = "none";

}

function getStats() {
    var days = nets = nids = type_day = net_day = type_week = net_week = 0;
    $.get('/checkstats', function(res) {
        if (res.status === 200) {
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

/*********
 * Icons *
 *********/
/* Changes icons by class name. If clasOne present sets classTwo and vice-versa.*/
function changeIcon(element, classOne, classTwo) {
    if ($(element).hasClass(classOne)) {
        $(element).removeClass(classOne);
        $(element).addClass(classTwo);
    } else {
        $(element).removeClass(classTwo);
        $(element).addClass(classOne);
    }
}

/***********
 * General *
 ***********/
$(document).ready(function() {
    $('#current-year').text(new Date().getFullYear());
    
    if (window.location.href.indexOf('dashboard') > -1) {
        if (document.getElementById('updated-ago') != null) {
             timelineSSE();
        }
        if (window.location.href.indexOf('stats') > -1) {
            getStats();
        }
    }
    
    $('#button-add-entry').on('click', function() { changeClassButtonIcon(); });
    $('#button-add-net').on('click', function() { changeClassButtonIcon(); });
    $('#button-add-host').on('click', function() { changeClassButtonIcon(); });
    
    if (document.getElementById('neterrors') != null) {
        $("#button-add-net").click();
    }
    if (document.getElementById('entryerrors') != null) {
        $("#button-add-entry").click();
    }
    if (document.getElementById('inconsistent') != null) {
        $("#button-add-entry").click();
    }
    if (document.getElementById('hosterrors') != null) {
        $("#button-add-host").click();
    }
    if (document.getElementById('hostediterrors') != null) {
        var errorOn = $("#hostediterrors").attr('data-host-error');
        if (errorOn != null) {
            var text = "#button-edit-host-" + errorOn;
            window.console.log(text);
            $(text).click();
        }
    }
    
    $("[rel='tooltip']").tooltip();
    $('.selectpicker').selectpicker();
});
