import React from 'react';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import MenuPage from './components/MenuPage'; // Assurez-vous que ce chemin est correct
import Theme from './components/Theme'; // Page sur laquelle vous travaillez
import Random from './components/Random'; // Page sur laquelle vous travaillez
import Question from './components/Question'; // Page sur laquelle vous travaillez

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MenuPage />} />
        <Route path="/random" element={<Random />} />
        <Route path="/theme" element={<Theme />} />
        <Route path="/question" element={<Question />} />
      </Routes>
    </Router>
  );
}

export default App;
