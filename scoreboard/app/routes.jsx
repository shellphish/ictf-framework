import React from 'react';
import {
  Router,
  Route,
  IndexRoute,
  IndexRedirect
} from 'react-router';

import App from './components/App';
import Scores from './components/Scores';
import ServiceExploits from './components/ServiceExploits';
import Services from './components/Services';
import ServiceState from './components/ServiceStates';
import Teams from './components/Teams';

export default (
  <Router>
    <Route path="/" component={App}>
      {/* <IndexRedirect to="scores" query={{ academiconly: false }}/> */}
      <IndexRedirect to="scores" />
      <Route path="scores" component={Scores} />
      <Route path="services" component={Services}/>
      <Route path="service-states" component={ServiceState} />
      <Route path="service-exploits" component={ServiceExploits} />
      <Route path="teams" component={Teams} />
    </Route>
  </Router>
);
