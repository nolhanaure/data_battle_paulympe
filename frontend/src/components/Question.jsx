import React, { useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import "bootstrap-icons/font/bootstrap-icons.min.css";
import './futuristic.css';
import { Link } from 'react-router-dom';

function Question() {
  const [category, setCategory] = useState(''); // Catégorie de la question
  const [question, setQuestion] = useState(''); // Question générée
  const [userAnswer, setUserAnswer] = useState(''); // Réponse de l'utilisateur
  const [feedback, setFeedback] = useState(''); // Réponse générée
  const [loading, setLoading] = useState(false);
  const [answered, setAnswered] = useState(false); // Nouveau état pour savoir si la réponse a été générée ou pas
  const [previousQuestions, setPreviousQuestions] = useState([]); // Nouveau état pour stocker les anciennes questions
  const [answers, setAnswers] = useState({}); // Nouveau état pour stocker les réponses générées
  const [userResponses, setUserResponses] = useState({}); // Nouveau état pour stocker les réponses des utilisateurs
  const [questionReponses, setQuestionReponses] = useState({}); // État pour stocker les réponses générées avec les questions

  const API_BASE = "http://127.0.0.1:8000";

  // Fonction pour générer une question
  const generateQuestion = async () => {
    if (!category) return;
    setLoading(true);
    setFeedback('');
    setUserAnswer('');
    setAnswered(false); // Réinitialiser l'état de réponse lors de la génération d'une nouvelle question

    const response = await fetch(`${API_BASE}/generate-question?category=${encodeURIComponent(category)}`);
    const data = await response.json();
    setQuestion(data.question || 'Erreur lors de la génération');
    setLoading(false);

    // Ajouter la question générée dans l'historique des questions
    setPreviousQuestions((prevQuestions) => [...prevQuestions, data.question || 'Erreur']);
  };

  // Fonction pour analyser la réponse (après que l'utilisateur ait répondu)
  const analyzeAnswer = async () => {
    if (!userAnswer.trim()) {
      setFeedback("❌ Vous devez répondre à la question avant de l'analyser.");
      return;
    }

    setLoading(true);
    const response = await fetch(`${API_BASE}/analyze-answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, user_question: question, user_answer: userAnswer }),
    });
    const data = await response.json();
    setFeedback(data.feedback || "Erreur lors de l'analyse");
    setAnswered(true); // Mettre l'état `answered` à true une fois que la question a été répondue
    setLoading(false);

    // Stocker la réponse dans l'état answers en associant la question à sa réponse
    setAnswers((prevAnswers) => ({
      ...prevAnswers,
      [question]: data.feedback || "Aucune réponse générée",
    }));

    // Stocker la réponse de l'utilisateur dans l'état userResponses
    setUserResponses((prevResponses) => ({
      ...prevResponses,
      [question]: userAnswer, // Sauvegarder la réponse de l'utilisateur
    }));

    // Stocker la réponse générée avec la question
    setQuestionReponses((prevResponses) => ({
      ...prevResponses,
      [question]: data.feedback || "Aucune réponse générée",
    }));
  };

  // Fonction pour gérer le cas où l'utilisateur clique sur "Je n'ai pas la réponse"
  const handleNoAnswer = async () => {
    setLoading(true);
    const response = await fetch(`${API_BASE}/generate-model-answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category, user_question: question, user_answer: "Je n'ai pas la réponse" }), // Texte par défaut
    });
    const data = await response.json();
    setFeedback(data.feedback || "Aucune réponse générée");
    setAnswered(true); // Marquer la question comme répondue
    setLoading(false);

    // Stocker la réponse générée avec la question
    setQuestionReponses((prevResponses) => ({
      ...prevResponses,
      [question]: data.feedback || "Aucune réponse générée",
    }));
  };

  // Fonction pour afficher la question précédente et récupérer la réponse
  const handlePreviousQuestionClick = (prevQuestion) => {
    setQuestion(prevQuestion); // Mettre la question sélectionnée dans l'input
    setUserAnswer(''); // Réinitialiser la réponse de l'utilisateur
    setFeedback(''); // Réinitialiser le feedback
    setAnswered(false); // Réinitialiser l'état de réponse

    // Vérifier si une réponse est déjà stockée pour la question précédente
    if (answers[prevQuestion]) {
      setFeedback(answers[prevQuestion]); // Afficher la réponse déjà générée
    }
    if (userResponses[prevQuestion]) {
      setUserAnswer(userResponses[prevQuestion]); // Afficher la réponse de l'utilisateur précédemment donnée
    }

    // Récupérer la réponse stockée avec la question
    if (questionReponses[prevQuestion]) {
      setFeedback(questionReponses[prevQuestion]); // Afficher la réponse générée pour la question sélectionnée
    }
  };

  // Formatage de la réponse de l'IA (pour l'affichage)
  const formatFeedback = (text) => {
    return text
      .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')  // Remplacer **texte** par <b>texte</b> pour gras
      .replace(/\*(.+?)\*/g, '<i>$1</i>')    // Remplacer *texte* par <i>texte</i> pour italique
      .replace(/(\d+\.\s)/g, '<br/>$1')       // Remplacer les chiffres suivis d'un point par un saut de ligne
      .replace(/(\-\s|\*\s)/g, '<br/>• ')     // Remplacer les puces par des sauts de ligne
      .replace(/Important Note:/g, '<span class="important-note">Important Note:</span>'); // Styliser la note importante
  };

  return (
    <div className="d-flex">
      
      {/* Conteneur principal à droite */}
      <div className="p-4" style={{ flex: 1 }}>
        {/* Barre de titre avec image */}
        <div className="navbar navbar-expand-lg w-100">
          <div className="beige container">
            <h2 className="text-center mb-0">
              <Link to="/">
                <img 
                  src="https://i.imgur.com/3Zmd1bk.png" 
                  alt="logo" 
                  style={{ width: '100px', height: '100px', marginRight: '10px' }} 
                />
              </Link>
              Assistant Droit des Brevets
            </h2>
          </div>
        </div>

       
        <div className="mb-3">
          <input
            className="form-control"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Entrez une question"
            onKeyDown={(e) => e.key === "Enter" && handleNoAnswer()}
          />
        </div>

        <textarea
              rows="4"
              className="form-control"
              value={userAnswer}
              onChange={(e) => setUserAnswer(e.target.value)}
              placeholder="Répondre à la question"
            />
            <div className="row d-flex">
              <button className="rep btn btn-success mt-2" onClick={analyzeAnswer}>
                Répondre
              </button>
              <button className="rep btn btn-warning mt-2 ml-2" onClick={handleNoAnswer}>
                Je n'ai pas la réponse
              </button>
            </div>

        {loading && <div className="loading">Chargement...</div>}

        {/* Si la question a déjà été répondue et stockée, afficher la réponse directement */}
        {feedback && answered && (
          <div className="ai-feedback mt-3" dangerouslySetInnerHTML={{ __html: formatFeedback(feedback) }} />
        )}

        {feedback && !answered && (
          <div className="ai-feedback mt-3" dangerouslySetInnerHTML={{ __html: formatFeedback(feedback) }} />
        )}

        {feedback && (
          <button className="btn btn-secondary w-100 mt-2" onClick={generateQuestion}>
            Nouvelle Question
          </button>
        )}
      </div>
    </div>
  );
}

export default Question;
