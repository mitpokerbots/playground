import React, { Component } from 'react';
import { Header, Icon, Container, Segment, Button } from 'semantic-ui-react';
import { withRouter } from 'react-router-dom';

import { SocketConsumer } from './SocketContext';

class Game extends Component {
  constructor(props) {
    super(props);

    this.state = {
      status: 'loading',
      game: null
    }
  }

  componentDidMount() {
    this.props.socket.emit('join_game', this.props.match.params.id, (result) => {
      this.setState({
        status: 'loaded',
        game: result
      })
    })

    this.props.socket.on('game_update', this.handleGameUpdate);
  }

  componentWillUnmount() {
    this.props.socket.off('game_update', this.handleGameUpdate);
  }

  handleGameUpdate = (newGame) => {
    this.setState({
      game: newGame
    })
  }

  renderGame() {

  }

  render() {
    return (
      <div style={{ height: "100%" }}>
        <Container>
          { this.state.status === 'loading' && (
            <Header as='h2' style={{ paddingTop: "2em", textAlign: 'center' }}>
              Loading game details...
            </Header>
          )}
          { this.state.status === 'loaded' && this.state.game == null && (
            <div style={{ paddingTop: "2em", textAlign: 'center' }}>
              <Header as='h2'>
                The game you're looking for doesn't exist.
              </Header>
              <Button primary onClick={() => this.props.history.push("/")}>Go back</Button>
            </div>
          )}
          { this.state.status === 'loaded' && this.state.game != null && (
            <div style={{ paddingTop: "2em" }}>
              <Header as='h3' style={{ textAlign: 'center' }}>
                Hero vs. { this.state.game.bot.team } ({ this.state.game.bot.name })
              </Header>
              <Segment placeholder>
                { this.state.game.status === 'created' && (
                  <Header icon>
                    <Icon name='spinner' loading />
                    Waiting for game to start...
                  </Header>
                )}
                { this.state.game.status === 'in_progress' && this.renderGame() }
                { this.state.game.status === 'internal_error' && (
                  <div style={{ textAlign: "center" }}>
                    <Header icon>
                      <Icon name='exclamation' color='red' />
                      Sorry! Something went wrong. Please create a new game.
                    </Header>
                    <Button primary onClick={() => this.props.history.push("/")}>Go back</Button>
                  </div>
                )}
                { this.state.game.status === 'completed' && (
                  <div style={{ textAlign: "center" }}>
                    <Header icon>
                      <Icon name='check' color='green' />
                      This game has completed.
                    </Header>
                    <Button primary onClick={() => this.props.history.push("/")}>New game</Button>
                  </div>
                )}
              </Segment>
            </div>
          )}
        </Container>
      </div>
    );
  }
}

const GameWithSocket = (props) => (
  <SocketConsumer>
    { (value) => <Game {...props} socket={value} /> }
  </SocketConsumer>
);

export default withRouter(GameWithSocket);
