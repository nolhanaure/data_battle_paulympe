import React from 'react';
import { Link } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import './futuristic.css';

function MenuPage() {
  return (
    <div className="barre d-flex flex-column align-items-center">
      {/* Barre de titre avec image */}
      <div className="navbar navbar-expand-lg w-100">
        <div className="beige container">
          <h2 className="text-center mb-0">
            <img 
              src="https://i.imgur.com/3Zmd1bk.png" 
              alt="logo" 
              style={{ width: '100px', height: '100px', marginRight: '10px' }} 
            />
            Assistant Droit des Brevets
          </h2>
        </div>
      </div>

      {/* Zone des boutons */}
      <div className="mt-5 w-75">
        <div className="d-flex justify-content-between">
          {/* Bouton 1 - Lien vers une autre page */}
          <Link to="/random">
            <button className="btn btn-primary w-100 mx-2">
              Question à theme aléatoire
            </button>
          </Link>

          {/* Bouton 2 - Lien vers la page principale */}
          <Link to="/theme">
            <button className="btn btn-success w-100 mx-2">
              Questions par thème
            </button>
          </Link>

          {/* Bouton 3 - Lien vers une autre page */}
          <Link to="/question">
            <button className="btn btn-danger w-100 mx-2">
              Je me pose une question
            </button>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default MenuPage;
