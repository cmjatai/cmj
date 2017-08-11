import React from 'react';

class App extends React.Component {
    render(){
        return (
            <h2>Hello Django - React...</h2>
        );
    }
}

class AppFetch extends React.Component{
  render(){
    return (
      <Fetch url="http://www.camarajatai.go.gov.br/portal/json/jsonclient/json?page=1&step=10">
        <TestComponent/>
      </Fetch>
    )
  }
}

class TestComponent extends React.Component{
  render(){
    return (
        <div>
            {this.props.results ? this.props.results[0].text : 'carregando...'}
        </div>
    )
  }
}

export default App;
