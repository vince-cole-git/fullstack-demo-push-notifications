<!DOCTYPE html>
<html>
   <head>
      <script src="http://localhost:15670/web-stomp-examples/stomp.js"></script>
      <script>
        var ws = new WebSocket('ws://localhost:15674/ws');
        var client = Stomp.over(ws);
        
        var on_connect = function(x) {
            console.log('connected');
            id = client.subscribe("/exchange/logs", function(d) {
                console.log(d.body);
            });
        };

        var on_error =  function() {
            console.log('error');
        };

        client.connect('guest', 'guest', on_connect, on_error, '/');

      </script>
   </head>
   <body>
   </body>
</html>