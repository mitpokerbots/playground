import React, { Component } from 'react';
import { Header, Icon, Container, Segment, Button, Grid, Feed, Divider, Statistic } from 'semantic-ui-react';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';
import { withRouter } from 'react-router-dom';

import { SocketConsumer } from './SocketContext';

const PlaceholderCard = () => {
  return (
    <div style={{ border: '1px dashed grey', borderRadius: '5px', display: 'inline-block', margin: '0 0.5em' }}>
      <table>
        <tbody>
          <tr style={{ textAlign: 'left' }}>
            <td>&nbsp;</td>
          </tr>
          <tr>
            <td style={{ textAlign: 'center', fontSize: '2em', width: '50px', padding: '0.2em 0' }}>
              &nbsp;
            </td>
          </tr>
          <tr>
            <td style={{ textAlign: 'right' }}>&nbsp;</td>
          </tr>
        </tbody>
      </table>
    </div>
  )
}

const Card = (props) => {
  const card = props.card;
  if (card === '??') {
    return (
      <div style={{ border: '1px solid grey', borderRadius: '5px', display: 'inline-block', color: 'green', backgroundColor: 'green', margin: '0 0.5em' }}>
        <table>
          <tbody>
            <tr style={{ textAlign: 'left' }}>
              <td>&nbsp;</td>
            </tr>
            <tr>
              <td style={{ textAlign: 'center', fontSize: '2em', width: '50px', padding: '0.2em 0' }}>
                &nbsp;
              </td>
            </tr>
            <tr>
              <td style={{ textAlign: 'right' }}>&nbsp;</td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }
  return (
    <div style={{ border: '1px solid grey', borderRadius: '5px', display: 'inline-block', color: (card[1] === 's' || card[1] === 'c') ? 'black' : 'red', margin: '0 0.5em' }}>
      <table>
        <tbody>
          <tr style={{ textAlign: 'left' }}>
            <td>{ card[1].toUpperCase() }</td>
          </tr>
          <tr>
            <td style={{ textAlign: 'center', fontSize: '2em', width: '50px', padding: '0.2em 0' }}>
              { card[0] === 'T' && '10'}
              { card[0] !== 'T' && card[0] }
            </td>
          </tr>
          <tr>
            <td style={{ textAlign: 'right' }}>{ card[1].toUpperCase() }</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

class Game extends Component {
  constructor(props) {
    super(props);

    this.state = {
      status: 'loading',
      game: null,
      selected_amount: 0,
      min_amount: null,
      max_amount: null,
      pingInterval: null,
    }
  }

  componentDidMount() {
    this.props.socket.emit('join_game', this.props.match.params.id, (result) => {
      this.setState({
        status: 'loaded',
        pingInterval: setInterval(() => {
          this.props.socket.emit('game_ping', this.props.match.params.id);
        }, 2000)
      })
      this.handleGameUpdate(result);
    })

    this.props.socket.on('game_update', this.handleGameUpdate);
  }

  componentWillUnmount() {
    this.props.socket.off('game_update', this.handleGameUpdate);
    clearInterval(this.state.pingInterval);
  }

  handleGameUpdate = (newGame) => {
    var min_amount = null;
    var max_amount = null;
    if (newGame.last_message && newGame.last_message.legal_moves) {
      newGame.last_message.legal_moves.forEach((move) => {
        min_amount = move.min || min_amount;
        max_amount = move.max || min_amount;
      });      
    }
    console.log("Blah", min_amount, max_amount);

    this.setState({
      game: newGame,
      selected_amount: min_amount,
      min_amount,
      max_amount
    })
  }

  renderGameLog() {
    var log = this.state.game.last_message.move_history.slice().reverse();

    var actionToPastTense = {
      'BET': 'bet',
      'RAISE': 'raised',
      'POST': 'posted',
      'TIE': 'tied',
      'WIN': 'won',
      'CALL': 'called',
      'FOLD': 'folded',
      'CHECK': 'checked',
    }

    return (
      <Feed size='small'>
        <Header as='h4'>
          Game log
          <Header.Subheader>Reverse chronological order.</Header.Subheader>
        </Header>

        { log.map((log_item, i) => (
          <Feed.Event key={'' + i}>
            <Feed.Content>
              <Feed.Summary>
                { log_item.type === 'DEAL' && (
                  <div>
                  <span style={{ color: 'grey' }}>The { log_item.street } was dealt.</span>
                  <Divider />
                  </div>
                )}
                { ['BET', 'RAISE'].indexOf(log_item.type) !== -1 && (
                  <span style={{ color: (log_item.player === 'bot') ? 'black' : '#016699' }}>
                    { log_item.player === 'hero' && (<span>You </span>)}
                    { log_item.player === 'bot' && (<span>{ this.state.game.bot.team } </span>)}
                    <span>{ actionToPastTense[log_item.type] } to </span>
                    { log_item.amount } { (log_item.amount === 1) ? 'chip.' : 'chips.' }
                  </span>
                )}
                { log_item.type === 'POST' && (
                  <span style={{ color: (log_item.player === 'bot') ? 'black' : '#016699' }}>
                    { log_item.player === 'hero' && (<span>You </span>)}
                    { log_item.player === 'bot' && (<span>{ this.state.game.bot.team } </span>)}
                    <span>posted </span>
                    { log_item.amount } { (log_item.amount === 1) ? 'chip.' : 'chips.' }
                  </span>
                )}
                { log_item.type === 'EXCHANGE' && (
                  <span style={{ color: (log_item.player === 'bot') ? 'black' : '#016699' }}>
                  { log_item.player === 'hero' && (
                    <span>You exchanged { log_item.old.join(', ') } for { log_item.new.join(', ') }.</span>
                  )}
                  { log_item.player === 'bot' && (
                    <span>{ this.state.game.bot.team } exchanged.</span>
                  )}
                  </span>
                )}
                { ['CALL', 'CHECK', 'FOLD', 'WIN', 'TIE'].indexOf(log_item.type) !== -1 && (
                  <span style={{ color: (log_item.player == 'bot') ? 'black' : '#016699' }}>
                    { log_item.player === 'hero' && (<span>You </span>)}
                    { log_item.player === 'bot' && (<span>{ this.state.game.bot.team } </span>)}
                    <span>{ actionToPastTense[log_item.type] }.</span>
                  </span>
                )}
              </Feed.Summary>
            </Feed.Content>
          </Feed.Event>
        ))}
      </Feed>
    )
  }

  renderBoard() {
    return (
      <Grid stackable divided>
        <Grid.Row>
          <Grid.Column width='16'>
            <Header as='h4' style={{ textAlign: 'center' }}>
              Board Cards
            </Header>
            <div style={{ textAlign: 'center' }}>
            { this.state.game.last_message.board_cards.map((card, i) => (
              <Card card={card} key={i} />
            ))}
            { this.state.game.last_message.board_cards.length === 0 && (
              <div>
                <PlaceholderCard />
                <PlaceholderCard />
                <PlaceholderCard />
                <PlaceholderCard />
                <PlaceholderCard />
              </div>
            )}
            </div>
          </Grid.Column>
        </Grid.Row>
        <Grid.Row>
          <Grid.Column width='8'>
            <Header as='h4' style={{ textAlign: 'center' }}>
              Opponent Cards
            </Header>
            <div style={{ textAlign: 'center' }}>
            { this.state.game.last_message.opponent_cards.map((card, i) => (
              <Card card={card} key={i} />
            ))} 
            </div>
          </Grid.Column>
          <Grid.Column width='8'>
            <Header as='h4' style={{ textAlign: 'center' }}>
              Your Cards
            </Header>
            <div style={{ textAlign: 'center' }}>
            { this.state.game.last_message.cards.map((card, i) => (
              <Card card={card} key={i} />
            ))} 
            </div>
          </Grid.Column>
        </Grid.Row>
      </Grid>
    );
  }

  renderPot() {
    return (
      <div>
        <Statistic.Group size='mini' style={{ textAlign: 'center', display: 'block', marginTop: '1em' }}>
          <Statistic>
            <Statistic.Value>{ this.state.game.last_message.pot.grand_total }</Statistic.Value>
            <Statistic.Label>Pot size</Statistic.Label>
          </Statistic>
          <Statistic>
            <Statistic.Value>{ this.state.game.last_message.pot.num_exchanges }</Statistic.Value>
            <Statistic.Label>Your Exchanges</Statistic.Label>
          </Statistic>
          <Statistic>
            <Statistic.Value>{ this.state.game.last_message.pot.bets + this.state.game.last_message.pot.pip }</Statistic.Value>
            <Statistic.Label>Your bets</Statistic.Label>
          </Statistic>
        </Statistic.Group>
        <Divider />
      </div>
    )
  }

  handleAction = (move) => {
    this.props.socket.emit('game_action', this.props.match.params.id, {
      type: move,
      amount: this.state.selected_amount
    })
  }

  renderAction() {
    console.log(this.state)
    return (
      <div>
        <Header style={{ textAlign: 'center' }}>
          Choose an action
          <Header.Subheader>The cost is listed in parentheses</Header.Subheader>
        </Header>
        <div style={{ textAlign: 'center' }}>
          { this.state.game.last_message.legal_moves.map((move, i) => (
            <Button
              key={move.type}
              size='huge'
              basic
              positive={ move.base_cost == 0 && move.type !== 'FOLD' }
              negative={ move.type === 'FOLD' }
              onClick={() => this.handleAction(move.type)}>
              { move.type } ({ (['BET', 'RAISE'].indexOf(move.type) === -1) ? move.base_cost : this.state.selected_amount })
            </Button>
          ))}
        </div>
        { this.state.min_amount !== null && this.state.max_amount !== null && (
          <div style={{ textAlign: 'center', padding: '1em' }}>
            <p>
              (Optional) Select an amount for bet.
            </p>
            <Slider
              min={this.state.min_amount}
              max={this.state.max_amount}
              value={this.state.selected_amount}
              step={1}
              onChange={(value) => this.setState({ selected_amount: value })} />
          </div>
        )}
      </div>
    )
  }

  renderGetAction() {
    return (
      <Segment color='yellow'>
        <Header dividing style={{ textAlign: 'center' }}>
          Your move!
          <Header.Subheader>
            Select an action below
          </Header.Subheader>
        </Header>
        <Statistic.Group size='mini' style={{ textAlign: 'center', display: 'block', margin: '1em 0' }}>
          <Statistic style={{ margin: '0 10px' }}>
            <Statistic.Value>{ this.state.game.last_message.bankroll }</Statistic.Value>
            <Statistic.Label>Hero</Statistic.Label>
          </Statistic>
          <Statistic style={{ margin: '0 10px' }}>
            <Statistic.Value>{ this.state.game.last_message.opponent_bankroll }</Statistic.Value>
            <Statistic.Label>{ this.state.game.bot.team }</Statistic.Label>
          </Statistic>
        </Statistic.Group>
        <Divider />
        <Grid stackable divided>
          <Grid.Row>
            <Grid.Column width='10'>
              { this.renderBoard() }
              { this.renderPot() }
              { this.renderAction() }
            </Grid.Column>
            <Grid.Column width='6'>
              { this.renderGameLog() }
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </Segment>
    )
  }

  renderRoundOver() {
    return (
      <Segment color='black'>
        <Header dividing style={{ textAlign: 'center' }}>
          The round is over
        </Header>
        <Statistic.Group size='mini' style={{ textAlign: 'center', display: 'block', margin: '1em 0' }}>
          <Statistic style={{ margin: '0 10px' }}>
            <Statistic.Value>{ this.state.game.last_message.bankroll }</Statistic.Value>
            <Statistic.Label>Hero</Statistic.Label>
          </Statistic>
          <Statistic style={{ margin: '0 10px' }}>
            <Statistic.Value>{ this.state.game.last_message.opponent_bankroll }</Statistic.Value>
            <Statistic.Label>{ this.state.game.bot.team }</Statistic.Label>
          </Statistic>
        </Statistic.Group>
        <Divider />
        <Grid stackable divided>
          <Grid.Row>
            <Grid.Column width='10'>
              { this.renderBoard() }
              { this.renderPot() }
              { this.state.game.last_message.result === 'win' && (
                <Header style={{ color: 'green', textAlign: 'center' }}>
                  You won the pot! You win { this.state.game.last_message.new_bankroll - this.state.game.last_message.bankroll } chips.
                </Header>
              )}
              { this.state.game.last_message.result === 'loss' && (
                <Header style={{ color: 'red', textAlign: 'center' }}>
                  You lost the pot! You lost { -this.state.game.last_message.new_bankroll + this.state.game.last_message.bankroll } chips.
                </Header>
              )}
              { this.state.game.last_message.result === 'tie' && (
                <Header style={{ color: 'grey', textAlign: 'center' }}>
                  You tied for the pot.
                </Header>
              )}
            </Grid.Column>
            <Grid.Column width='6'>
              { this.renderGameLog() }
            </Grid.Column>
          </Grid.Row>
        </Grid>
      </Segment>
    );
  }

  renderGame() {
    if (this.state.game.last_message.status === 'download_and_compile') {
      return (
        <Segment placeholder>
          <div style={{ textAlign: "center" }}>
            <Header icon>
              <Icon name='spinner' loading />
              Downloading and compiling bot...
            </Header>
          </div>
        </Segment>
      )
    } else if (this.state.game.last_message.status === 'starting_game') {
      return (
        <Segment placeholder>
          <div style={{ textAlign: "center" }}>
            <Header icon>
              <Icon name='spinner' loading />
              Starting game...
            </Header>
          </div>
        </Segment>
      )
    } else if (this.state.game.last_message.status == 'get_action') {
      return this.renderGetAction();
    } else if (this.state.game.last_message.status == 'round_over') {
      return this.renderRoundOver();
    }
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
              { this.state.game.status === 'created' && (
                <Segment placeholder>
                  <Header icon>
                    <Icon name='spinner' loading />
                    Waiting for game to start...
                  </Header>
                </Segment>
              )}
              { this.state.game.status === 'in_progress' && this.renderGame() }
              { this.state.game.status === 'internal_error' && (

                <Segment placeholder>
                  <div style={{ textAlign: "center" }}>
                    <Header icon>
                      <Icon name='exclamation' color='red' />
                      Sorry! Something went wrong. Please create a new game.
                    </Header>
                    <Button primary onClick={() => this.props.history.push("/")}>Go back</Button>
                  </div>
                </Segment>
              )}
              { this.state.game.status === 'completed' && (

                <Segment placeholder>
                  <div style={{ textAlign: "center" }}>
                    <Header icon>
                      <Icon name='check' color='green' />
                      This game has completed.
                      { this.state.game.last_message && this.state.game.last_message.message && (
                        <Header.Subheader>
                          { this.state.game.last_message.message }
                        </Header.Subheader>
                      )}
                    </Header>
                    <Button primary onClick={() => this.props.history.push("/")}>New game</Button>
                  </div>
                </Segment>
              )}
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
