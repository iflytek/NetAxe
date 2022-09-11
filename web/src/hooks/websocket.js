let webSocket = null;
let socketOpen = false;

// 发送消息
export const doSend = (message) => {
  if (socketOpen) {
    webSocket.send(message)
  }
}
export const doMessage = (message)=>{
  if (socketOpen) {
    console.log(message)
  }
}

// 初始化websocket
export const contactSocket = () => {
  if ("WebSocket" in window) {
    const ws_scheme = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws_url = ws_scheme + '://' + window.location.host + '/ws/syslogsearch/'
    webSocket = new WebSocket(ws_url);
    webSocket.onopen = function () {
      console.log("连接成功！");
      socketOpen = true
    };
    webSocket.onmessage = function (evt) {
      var received_msg = evt.data;
      console.log("接受消息：" + received_msg);
    };
    webSocket.onclose = function () {
      console.log("连接关闭！");
    };
    webSocket.onerror = function () {
      console.log("连接异常！");
    };
  }
}
