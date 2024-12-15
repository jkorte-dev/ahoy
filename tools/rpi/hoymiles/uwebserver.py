import asyncio
import network
from datetime import datetime, timezone

_start_page = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Title</title>
    <style>
    #resp-table, .resp-table{
        width: 100%;
        display: table;
    }
    #resp-table-body, .resp-table-body{
        display: table-row-group;
    }
    .resp-table-row{
        display: table-row;
    }
    .table-body-cell{
        display: table-cell;
        border: 1px solid #dddddd;
        padding: 8px;
        line-height: 1.42857143;
        vertical-align: top;
    }
   .header-green{
        background: green;
        color: white;
        text-align: center;
    }
    .cell-lightgreen{
        background: chartreuse;
        text-align: center;
    }
    .header-blue{
        background: blue;
        color: white;
        text-align: center;
    }
    .cell-lightblue{
        background: deepskyblue;
        text-align: center;
    }
    .resp-table-half{
        width: 50%;
        display: table;
    }
    .half{
        width: 50%;
        margin: -1;
        margin-top: 10px;
        display: inline-block;
    }
    </style>

</head>

<body>
<script>
    const spec = {
        'temperature': ['Temp. ', ' °C'],
        'power': ['Power ', ' W'],
        'voltage': ['U ', ' V'],
        'current': ['I ', ' A'],
        'frequency': ['F_AC ', ' Hz'],
        'energy_daily' : ['Yield Day', 'Wh'],
        'yield_today' : ['Yield Day', 'Wh'],
        'yield_total' : ['Yield Total', 'kWh', '0.001'],
        'energy_daily' : ['Yield Day', 'Wh'],
        'energy_total' : ['Yield Total', 'kWh', '0.001'],
        'efficiency' : ['Eff.', '%']
    }

    const specMap = new Map(Object.entries(spec));

    document.addEventListener('DOMContentLoaded', function() {
        window.setInterval(updateContent, 5000);
    });
    function updateContent() {
        fetch(window.location + 'data')
            .then(response => response.json())
            .then(data => {
            //data = JSON.parse(text)
            let now = new Date();
            showData(data)
            //document.getElementById('content').innerText = data.yield_total + ' ' + now ;
        });
    }


   function showData(json) {
        let values = [json]
        json.power = json.phases[0].power;

        const divContent = document.getElementById('content');
        divContent.innerText = ''; // clear node first
        renderTable(divContent, values, json.inverter_name + ' ' + json.time + ' ' + new Date(), 'header-green', 'cell-lightgreen');
        json.strings.forEach(item => {
            parentNode = div('half');
            divContent.appendChild(parentNode);
            renderTable(parentNode, [item], item.name, 'header-blue', 'cell-lightblue');
        })
    };

    function div(cssClass) {
       let div =  document.createElement('div');
       div.className = cssClass;
       return div;
    }

    function renderHeader(value, cssClass) {
        let divTable = div('resp-table ' + cssClass);
        let divBody = div('resp-table-body');
        let divRow = div('resp-table-row');
        let divCell = div('table-body-cell');
        divBody.appendChild(divRow);
        divRow.append(divCell);
        divCell.innerText = value;
        divTable.appendChild(divBody);
        return divTable;
    }

    function renderTable(parentNode, values, headerValue, headerCss, cellCss) {

        parentNode.appendChild(renderHeader(headerValue, headerCss))
        const divTable = div('resp-table');
        const divBody = div('resp-table-body');
        divTable.appendChild(divBody);
        parentNode.appendChild(divTable);

        var divRow = div('resp-table-row');
        var counter = 0;

        values.forEach(item => {
            for (key in item) {
                if (specMap.get(key)) {
                    divCell = div('table-body-cell ' + cellCss);
                    if (spec[key].length > 2) {
                        factor = spec[key][2];
                    } else {
                        factor = 1;
                    }
                    divCell.innerHTML = `<span>${spec[key][0]}</span><br/><span>${(item[key]*factor).toFixed(1)} ${spec[key][1]}</span>`;
                    divRow.appendChild(divCell);
                    if (counter == 4) {
                        divBody.appendChild(divRow);
                        divRow = div('resp-table-row');
                        counter = 0;
                    } else {
                        counter++;
                    }
                }
            }
            divBody.appendChild(divRow);
        });
    }
</script>
<div id="content">
  DTU startet waiting for data ....
</div>

</body>
</html>
"""


class WebServer:

    dtu_data = {'last': {'dtu_ser': 99978563001, 'event_count': 10, 'time': datetime.now(timezone.utc), 'inverter_ser': 114182941658, 'inverter_name': 'garage', 'yield_total': 1305799.0, 'temperature': 18.6, 'powerfactor': 1.0, 'yield_today': 207.0, 'phases': [{'frequency': 50.01, 'current': 0.9599999, 'reactive_power': 0.2, 'power': 226.3, 'voltage': 236.3}], 'efficiency': 95.49, 'strings': [{'energy_daily': 67, 'name': 'String 1 left', 'power': 110.3, 'current': 3.06, 'energy_total': 580076, 'irradiation': 29.026, 'voltage': 36.1}, {'energy_daily': 140, 'name': 'String 2 right', 'power': 126.7, 'current': 3.7, 'energy_total': 725723, 'irradiation': 33.342, 'voltage': 34.3}]}}

    def __init__(self, data_provider=None, start_page="web/index.html", wifi_mode=network.STA_IF):
        if data_provider is None:
            self.data_provider = self
        else:
            self.data_provider = data_provider
        self.start_page = start_page
        self.wifi_mode = wifi_mode

    def get_data(self):
        _last = self.dtu_data['last']
        _timestamp = _last['time']
        if isinstance(_timestamp, datetime):
            _new_ts = _timestamp.isoformat().split('.')[0]
            _last['time'] = _new_ts
        return f"{_last}".replace('\'', '\"')

    async def serve_client(self, reader, writer):
        request_line = await reader.readline()
        print("Request:", request_line)
        # We are not interested in HTTP request headers, skip them
        while await reader.readline() != b"\r\n":
            pass

        request = str(request_line)
        if request.find('/data') == 6:
            print('=> data requested')
            header = 'HTTP/1.1 200 OK\r\nContent-type: application/json\r\n\r\n'
            #_json = {'dtu_ser': 99978563001, 'event_count': 10, 'time': '2024-12-12 20:34:45', 'inverter_ser': 114182941658, 'inverter_name': 'garage', 'yield_total': 1305799.0, 'temperature': 18.6, 'powerfactor': 1.0, 'yield_today': 207.0, 'phases': [{'frequency': 50.01, 'current': 0.9599999, 'reactive_power': 0.2, 'power': 226.3, 'voltage': 236.3}], 'efficiency': 95.49, 'strings': [{'energy_daily': 67, 'name': 'String 1 left', 'power': 110.3, 'current': 3.06, 'energy_total': 580076, 'irradiation': 29.026, 'voltage': 36.1}, {'energy_daily': 140, 'name': 'String 2 right', 'power': 126.7, 'current': 3.7, 'energy_total': 725723, 'irradiation': 33.342, 'voltage': 34.3}]}
            json = self.data_provider.get_data()
            response = f"{json}"
        else:
            try:  # serve file
                header = 'HTTP/1.1 200 OK\r\nContent-type: text/html\r\n\r\n'
                print('serving', self.start_page)
                #file = open(self.start_page, "r")
                #response = file.read()
                #file.close()
                response = _start_page
            except Exception as e:
                header = "HTTP/1.1 404 Not Found\n"
                response = "<html><body><h1>File not found</h1></body></html>"
                print(e)

        writer.write(header)
        writer.write(response)

        await writer.drain()
        await writer.wait_closed()

    async def webserver(self):
        import wlan
        #import ntptime

        if self.wifi_mode == network.AP_IF:
            wlan.start_ap(ssid='MPY-DTU')
        elif self.wifi_mode == network.STA_IF:
            wlan.do_connect()
            #ntptime.settime() # todo make resilient
        else:
            print("no valid wifi config. skipping webserver")
            return     # no valid wifi!

        ip = network.WLAN(self.wifi_mode).ifconfig()[0]
        port = 80
        url = f'http://{ip}:{port}'

        asyncio.create_task(asyncio.start_server(self.serve_client, ip, port))
        print(f'WebServer startet: {url}')
        while True:
            await asyncio.sleep(1)  # keep up server

    def start(self):
        try:
            asyncio.run(self.webserver())
        finally:
            asyncio.new_event_loop()


if __name__ == '__main__':
    WebServer().start()
else:
    print('skipped __main__')
