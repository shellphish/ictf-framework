import 'whatwg-fetch';

class AbstractApi {
  constructor(baseURL) {
    this.baseURL = baseURL;
  }

  get(url, params, options = {}) {
    options = Object.assign(
      {},
      options,
      { method: 'get' }
    );
    if (params) {
      url = url + '?' + this.objectToQueryString(params);
    }
    return this.request(url, options);
  }

  post(url, body, options = {}) {
    options = Object.assign(
      {},
      options,
      { method: 'post', body: JSON.stringify(body) }
    );
    return this.request(url, options);
  }

  patch(url, body, options = {}) {
    options = Object.assign(
      {},
      options,
      { method: 'PATCH', body: JSON.stringify(body) }
    );
    return this.request(url, options);
  }

  delete(url, options = {}) {
    options = Object.assign(
      {},
      options,
      { method: 'delete' }
    );
    return this.request(url, options);
  }

  apiUrl(path = '') {
    return this.baseURL + path;
  }

  defaultHeaders() {
    return {
      'Content-Type': 'application/json'
    };
  }

  request(url, options = {}) {
    url = this.apiUrl(url);

    options.headers = Object.assign({}, this.defaultHeaders(), options.headers);

    return fetch(url, options)
      .then((response) => {
        var keys = ['headers', 'ok', 'status', 'statusText', 'type', 'url'];
        var responseClone = {};
        for (var key of keys) {
          responseClone[key] = response[key];
        }

        if (response.status !== 204) {
          return response.json()
          .then(body => {
            responseClone.body = body;
            return responseClone;
          })
          .catch(x => { 
            console.log("json error: " + x)
            responseClone.body = false;
            return responseClone;
          });
        } else {
          responseClone.body = true;
          return responseClone;
        }
      })
      .then((response) => {
        if (response.status >= 200 && response.status < 300) {
          return Promise.resolve(response);
        } else {
          return Promise.reject(response);
        }
      });
  }

  objectToQueryString(obj) {
    return Object.keys(obj).map(k => {
      return encodeURIComponent(k) + '=' + encodeURIComponent(obj[k]);
    }).join('&');
  }
}

export default AbstractApi;
