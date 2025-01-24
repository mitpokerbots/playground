import React, { Component } from "react";
import { io } from "socket.io-client";
import "semantic-ui-css/semantic.min.css";
import { BrowserRouter as Router, Route } from "react-router-dom";

import { SocketProvider } from "./SocketContext";
import ConnectionStatusMenu from "./ConnectionStatusMenu";
import Home from "./Home";
import Game from "./Game";

const connectURL =
  process.env.NODE_ENV === "development"
    ? "http://localhost:5001"
    : window.location.protocol + "//" + window.location.host;
const socket = io(connectURL, {
  reconnectionAttempts: 5,
});

class App extends Component {
  render() {
    return (
      <SocketProvider value={socket}>
        <Router>
          <div
            style={{
              height: "100vh",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <div style={{ height: "50px" }}>
              <ConnectionStatusMenu socket={socket} />
            </div>
            <div style={{ flex: "1" }}>
              <Route path="/" exact component={Home} />
              <Route path="/game/:id" component={Game} />
            </div>
          </div>
        </Router>
      </SocketProvider>
    );
  }
}

export default App;
