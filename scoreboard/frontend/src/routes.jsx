import React from 'react';
import {
  Route,
  Redirect
} from 'react-router';
import {BrowserRouter} from 'react-router-dom';
import App from './components/App'

const Routes = () => (
  <BrowserRouter>
    <Route path="/" component={App} />
  </BrowserRouter>
);

export default Routes;