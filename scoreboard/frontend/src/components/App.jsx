import React from 'react';
import { NavLink, useLocation, Route } from 'react-router-dom';
import _ from 'underscore';
import { useEffect, useState } from 'react';
import { SWRConfig } from 'swr';

import SetIntervalMixin from '../mixins/SetIntervalMixin';
import {useGameState} from '../sources/api_hooks'
/* import AcademicSwitch from './AcademicSwitch'; */
import Countdown from './shared/Countdown';
import useInterval from '../hooks/useInterval';

import Scores from './Scores';
import ServiceExploits from './ServiceExploits';
import Services from './Services';
import ServiceState from './ServiceStates';
import Teams from './Teams';


const POLLING_INTERVAL = 10 * 1000;



const views = [
  // { title: 'Scoreboard',        path: '/scores',            component: (props) => <Scores {...props}/>},
  { title: 'Service List',      path: '/services',          component: Services},
  { title: 'Service Status',    path: '/service-states',    component: ServiceState},
  { title: 'Service Exploits',  path: '/service-exploits',  component: ServiceExploits},
  { title: 'Teams',             path: '/teams',             component: Teams}
]


const filterAcademicTeams = (teams, academiconly) => {
  if (!academiconly)
  {
    return teams;
  }
  return _.values(teams).filter(t => !t.academiconly || t.academic_team === 1);
}

const App = SetIntervalMixin((props) => {
  const [title, setTitle] = useState('');
  
  // const [curTeams, setCurTeams] = useState([]);

  let location = useLocation();
  // let { academic_only=false } = location.state || {};
  
  let {gamestate, loading, error} = useGameState();
  console.log(gamestate, loading, error);

  return (
    <div className="wrap space--both-2">

      <header className="main-header">
        <NavLink className="logo" to="/">
          <span className="logo__name">{ title }</span>
        </NavLink>
        <Countdown/>
        <nav className="navigation">
          {
            views.map((view) => <NavLink 
                                  key={view.title}
                                  to={{pathname: view.path, state: location.state}}
                                  activeClassName="is-active"
                                >
                                    {view.title}
                                </NavLink>)
          }
        </nav>
      </header>
      <div className="main-content">
        {
          gamestate && views.map((view) => <Route 
                                exact 
                                strict 
                                path={view.path} 
                              > 
                                <view.component
                                  staticdata={gamestate.static}
                                  dynamicdata={gamestate.dynamic}
                                  teams={gamestate.static.teams}
                                  services={gamestate.static.services}
                                  key={view.path}
                                />
                              </Route>)
        }
      </div>
    </div>
  );
})

export default App;