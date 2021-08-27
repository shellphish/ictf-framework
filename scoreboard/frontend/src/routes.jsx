import React from 'react';
import {
  Route,
  Redirect
} from 'react-router';
import {BrowserRouter} from 'react-router-dom';

import App from './components/App';
import Scores from './components/Scores';
import ServiceExploits from './components/ServiceExploits';
import Services from './components/Services';
import ServiceState from './components/ServiceStates';
import Teams from './components/Teams';

const Routes = () => (
  <BrowserRouter>
    <Route exact path="/" component={App}></Route>
    <Route path="scores" component={Scores} />
      <Route path="services" component={Services}/>
      <Route path="service-states" component={ServiceState} />
      <Route path="service-exploits" component={ServiceExploits} />
      <Route path="teams" component={Teams} />
  </BrowserRouter>
);

export default Routes;