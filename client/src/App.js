import React, { Component } from 'react';
import { SocketProvider } from './SocketContext';

import * as io from 'socket.io-client';

import ConnectionStatusMenu from './ConnectionStatusMenu';
import 'semantic-ui-css/semantic.min.css';


const connectURL = (
  (process.env.NODE_ENV === 'development') ?
  (window.location.protocol + '//' + window.location.hostname + ":5000") :
  (window.location.protocol + '//' + window.location.host)
);
const socket = io(connectURL, {
  reconnectionAttempts: 3
});



class App extends Component {
  render() {
    return (
      <SocketProvider value={socket}>
        <div>
          <ConnectionStatusMenu socket={socket} />
        </div>
      </SocketProvider>
    );
  }
}

export default App;
