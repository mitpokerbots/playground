import React from 'react';

const SocketContext = React.createContext();

export const SocketProvider = SocketContext.Provider;
export const SocketConsumer = SocketContext.Consumer;
