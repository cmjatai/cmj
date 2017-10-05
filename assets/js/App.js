import React from 'react';

class App  extends React.Component {
  constructor(props) {
    super(props);
    this.state = { elapsed: 0 };
    this.tick = this.tick.bind(this);
  }

  componentDidMount() {
    this.timer = setInterval(this.tick, 1000);
  }

  componentWillUnmount() {
    clearInterval(this.timer);
  }

  tick() {
    this.setState({ elapsed: this.state.elapsed + 1 });
  }

  render() {
    return <h1>{this.state.elapsed} seconds</h1>;
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
