import React, { Component } from 'react';
import { Header, Icon, Container, Segment, Button, Form } from 'semantic-ui-react';
import { withRouter } from 'react-router-dom';

import { SocketConsumer } from './SocketContext';

class Home extends Component {
  constructor(props) {
    super(props);

    this.state = {
      teams: null,
      selectedTeam: null,
      selectedBot: null,
      loadingChallenge: false,
    }
  }

  fetchBots = () => {
    this.setState({ teams: null });
    this.props.socket.emit('request_bots', (result) => {
      this.setState({ teams: result.teams });
    })
  }

  componentDidMount() {
    this.fetchBots()
  }

  componentWillUnmount() {

  }

  handleChange = (e, { name, value }) => {
    if (name === 'selectedTeam') {
      this.setState({ selectedBot: null })
    }
    this.setState({ [name]: value })
  }

  teamOptions = () => {
    return this.state.teams.map((team, i) => ({
      key: i,
      text: team.name,
      value: i,
    }))
  }

  botOptions = () => {
    if (this.state.selectedTeam == null) {
      return [];
    }
    return this.state.teams[this.state.selectedTeam].bots.map((bot, i) => ({
      key: bot.id,
      text: bot.name,
      value: bot.id,
    }))
  }

  challengeBot = () => {
    this.setState({
      loadingChallenge: true
    })
    this.props.socket.emit('create_game', this.state.selectedBot, (gameUuid) => {
      this.setState({
        loadingChallenge: false
      })
      this.props.history.push('/game/' + gameUuid);
    })
  }

  render() {
    return (
      <div style={{ height: "100%" }}>
        <Container text>
          <Header as='h2' style={{ paddingTop: "2em" }}>
            Welcome to the Pokerbots Playground!
            <Header.Subheader>Here, you play human-vs-bot heads up hold'em against the bots on the scrimmage server.</Header.Subheader>
          </Header>
          <p>
            Simply select a bot to play against below, and you'll be connected.
          </p>
          { this.state.teams == null && (
            <Segment placeholder>
              <Header icon>
                <Icon name='spinner' loading />
                Fetching available bots...
              </Header>
              <Button primary onClick={this.fetchBots}>Try again</Button>
            </Segment>
          )}
          { this.state.teams != null && (
            <Segment>
              <Header dividing>
                Select a bot
              </Header>
              <Form>
                <Form.Select
                  name='selectedTeam'
                  options={this.teamOptions()}
                  placeholder="Select a team"
                  label="Team"
                  onChange={this.handleChange}
                  value={this.state.selectedTeam} />
                <Form.Select
                  name='selectedBot'
                  options={this.botOptions()} placeholder={
                    (this.state.selectedTeam == null) ? "Select a team first" : "Select a bot"
                  }
                  label="Bot"
                  disabled={this.state.selectedTeam == null}
                  onChange={this.handleChange}
                  value={this.state.selectedBot} />
                <div style={{ textAlign: "center" }}>
                  <Button
                    color='green'
                    onClick={this.challengeBot}
                    fluid
                    loading={this.state.loadingChallenge}
                    disabled={this.state.selectedBot == null || this.state.loadingChallenge}>Challenge!</Button>
                </div>
              </Form>
            </Segment>
          )}
        </Container>
      </div>
    );
  }
}

const HomeWithSocket = (props) => (
  <SocketConsumer>
    { (value) => <Home {...props} socket={value} /> }
  </SocketConsumer>
);

export default withRouter(HomeWithSocket);
