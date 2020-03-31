import React from 'react';
import { render } from 'react-dom';

import routes from './routes';

if (typeof document !== 'undefined') {
  render(routes, document.getElementById('app'));
}
