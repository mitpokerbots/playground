import React, { Component } from 'react';
import { SocketConsumer } from './SocketContext';

class Game extends Component {

  componentDidMount() {

  }

  componentWillUnmount() {

  }

  render() {
    return (
      <div style={{ backgroundColor: "green", height: "100%" }}>
        Game... { this.props.match.params.id }
      </div>
    );
  }
}

const GameWithSocket = (props) => (
  <SocketConsumer>
    { (value) => <Game {...props} socket={value} /> }
  </SocketConsumer>
);

export default GameWithSocket;
