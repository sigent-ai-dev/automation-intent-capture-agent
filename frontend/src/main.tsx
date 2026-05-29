import React from 'react';
import ReactDOM from 'react-dom/client';
import { configureAmplify } from './config/amplify';
import { App } from './App';
import './styles/globals.css';

configureAmplify();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
