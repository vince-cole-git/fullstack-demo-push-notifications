import websocketStore from "svelte-websocket-store";

const initialValue = {0};
export const myStore = websocketStore("wss://mydomain.com/ws1", initialValue, ['option 1', 'option 2']);


// send JSON to websocket server
//$myStore = { content: "to be saved", other_values: "all" };
$myStore = {}

// receive JSON from server (push)
let response = $myStore;