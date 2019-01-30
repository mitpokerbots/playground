import React, { Component } from 'react';

import {
  Menu,
  Icon,
} from 'semantic-ui-react'

class ConnectionStatusMenu extends Component {
  constructor(props) {
    super(props);

    this.state = {
      status: (this.props.socket.connected) ? "connected" : "connecting"
    }
  }

  handleConnect = () => {
    this.setState({
      status: "connected"
    })
  }

  handleReconnecting = () => {
    this.setState({
      status: "reconnecting"
    })
  }

  handleConnectError = () => {
    if (this.state.status !== 'reconnecting') {
      this.setState({
        status: "disconnected"
      })
    }
  }

  handleDisconnect = () => {
    this.setState({
      status: "disconnected"
    })
  }

  handlePermaDisconnect = () => {
    this.setState({
      status: "permanently_disconnected"
    })
  }

  componentDidMount() {
    this.props.socket.on('connect', this.handleConnect);
    this.props.socket.on('connect_error', this.handleConnectError);
    this.props.socket.on('disconnect', this.handleDisconnect);
    this.props.socket.on('reconnecting', this.handleReconnecting);
    this.props.socket.on('reconnect_failed', this.handlePermaDisconnect);
  }

  componentWillUnmount() {
    this.props.socket.off('connect', this.handleConnect);
    this.props.socket.off('connect_error', this.handleConnectError);
    this.props.socket.off('disconnect', this.handleDisconnect);
    this.props.socket.off('reconnecting', this.handleReconnecting);
    this.props.socket.off('reconnect_failed', this.handlePermaDisconnect);
  }

  render() {
    return (
      <Menu fixed='top' inverted borderless>
        <Menu.Item href="/">
          <img src='/logo_clear.png' alt="" />
          &nbsp; Pokerbots Playground
        </Menu.Item>
        { this.state.status === "connecting" && (
          <Menu.Item position='right' color='grey' active={true}>
            <Icon name='arrows alternate horizontal' />
            Connecting...
          </Menu.Item>
        )}
        { this.state.status === "connected" && (
          <Menu.Item position='right' color='green' active={true}>
            <Icon name='linkify' />
            Connected.
          </Menu.Item>
        )}
        { this.state.status === "reconnecting" && (
          <Menu.Item position='right' color='yellow' active={true}>
            <Icon name='arrows alternate horizontal' />
            Attempting to reconnect...
          </Menu.Item>
        )}
        { this.state.status === "disconnected" && (
          <Menu.Item position='right' color='yellow' active={true}>
            <Icon name='broken chain' />
            Connection lost.
          </Menu.Item>
        )}
        { this.state.status === "permanently_disconnected" && (
          <Menu.Item position='right' color='red' active={true}>
            <Icon name='broken chain' />
            Could not connect. Please refresh.
          </Menu.Item>
        )}
      </Menu>
    )
  }
}

export default ConnectionStatusMenu;
