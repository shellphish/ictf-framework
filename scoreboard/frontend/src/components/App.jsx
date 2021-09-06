import { Redirect, NavLink, useLocation, Route } from 'react-router-dom';
import { useState, useEffect } from 'react';


import {useGameState} from '../sources/api_hooks'
/* import AcademicSwitch from './AcademicSwitch'; */
import Countdown from './shared/Countdown';

import Scores from './Scores';
import ServiceExploits from './ServiceExploits';
import Services from './Services';
import ServiceState from './ServiceStates';
import Teams from './Teams';


const views = [
  { title: 'Scoreboard',        path: '/scores',            component: Scores},
  { title: 'Service List',      path: '/services',          component: Services},
  { title: 'Service Status',    path: '/service-states',    component: ServiceState},
  { title: 'Service Exploits',  path: '/service-exploits',  component: ServiceExploits},
  { title: 'Teams',             path: '/teams',             component: Teams}
]

const App = (props) => {
  const [title, setTitle] = useState('');
  let location = useLocation();
  let {gamestate, loading, error} = useGameState();

  // const [curTeams, setCurTeams] = useState([]);
  useEffect(() => {
    setTitle(document.title)
  }, [location])

  return (
    <div className="wrap space--both-2">

      <header className="main-header">
        <NavLink className="logo" to="/">
          <span className="logo__name">{ title }</span>
        </NavLink>
        <Countdown/>
        <nav className="navigation">
          <Route key='route-redirect' exact strict path='/'>
            <Redirect to='/scores' />
          </Route>
          {
            views.map((view) => <NavLink 
                                  key={"link-" + view.path}
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
                                key={"route" + view.path}
                              > 
                                <view.component
                                  staticdata={gamestate.static}
                                  dynamicdata={gamestate.dynamic}
                                  teams={gamestate.static.teams}
                                  services={gamestate.static.services}
                                  key={"component" + view.path}
                                />
                              </Route>)
        }
      </div>
    </div>
  );
}

export default App;