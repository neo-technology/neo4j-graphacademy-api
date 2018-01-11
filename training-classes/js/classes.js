var options = {
  closable: false,
  theme: {
    logo: 'https://s3.amazonaws.com/dev.assets.neo4j.com/wp-content/uploads/neo4j_logo_globe.png',
    primaryColor: '#58b535'
  },
  initialScreen: (localStorage.getItem('previousLogin') == null)?'signUp':'login',
  languageDictionary: {
    title: 'Neo4j',
    signin: {
      title: 'Sign in'
    },
    signup: {
      title: 'Sign up'
    }
  },
  auth: {
    redirectUrl: 'https://neo4j.com/graphacademy/login/?return=' + window.location.href,
    params: {
      scope: 'openid name email',
      responseType: 'token'
    }
  }
}

var lock = new Auth0Lock(
  'xSEhNfb0vyfF5SnlzGKx5F6LhAB9pabu',
  'neo4j-sync.auth0.com',
  options
);

var webAuth = new auth0.WebAuth({
  domain: 'neo4j-sync.auth0.com',
  clientID: 'xSEhNfb0vyfF5SnlzGKx5F6LhAB9pabu'
});

function logTrainingView() {
  id_token = Cookies.get("graphacademy_id_token");
  return $.ajax
  ({
    type: "POST",
    url: "https://nmae7t4ami.execute-api.us-east-1.amazonaws.com/prod/logTrainingView",
    contentType: "application/json",
    dataType: 'json',
    async: true,
    data: JSON.stringify(
      { "className": "online-training-1",
        "partName": $(".quiz").first().attr("id").replace("quiz","part")
      }),
    headers: {
      "Authorization": id_token
    }
  });
}

function renewAuth() {
  webAuth.renewAuth({
        redirectUri: 'https://neo4j.com/graphacademy/auth-iframe/',
        usePostMessage: true,
        postMessageDataType: 'graphacademy-auth',
        scope: 'openid name email',
        nonce: btoa(Math.floor((Math.random() * 100000000)) + ":" + Math.round(Date.now() / 10))
      }, function (error, renewAuthResult) {
        if (renewAuthResult) {
          Cookies.set('graphacademy_id_token', renewAuthResult['idToken'], { path: '/graphacademy/' });
          console.log('renewAuth successful', error, renewAuthResult);
          logTrainingView();
          getQuizStatus();
        } else {
          lock.show();
        }
  });
}

jQuery(document).ready(function () {
  if (Cookies.get('graphacademy_id_token')) {
    // we're authenticated
    // could check expiration of token, but not critical for this app
    // still need to check quiz status
    logTrainingView().then(
      function() {
        return getQuizStatus().then(
          function() {}, 
          function() { return renewAuth() });
      },
      function() { return renewAuth() } 
    );
  } else {
    renewAuth();
  }
});
